#!/usr/bin/env python3
"""Multi-platform video publishing: one manifest -> up to 10 platforms.

  python3 publish.py examples/example.json                   # dry run: validate + print commands
  python3 publish.py examples/example.json --go              # actually publish
  python3 publish.py m.json --only bilibili,douyin --go           # only selected platforms
  python3 publish.py m.json --only douyin --headed --go           # visible window: handle SMS verification yourself
  python3 publish.py --verify-bilibili BV1xxxx                    # read back an already-submitted Bilibili video

Bilibili uses biliup directly (multi-part, AI declaration, event mission_id); other platforms use social-auto-upload's `sau`.
Login credentials live in $SAU_HOME/cookies/ and are never written into this repo.
"""
import argparse, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

SAU_HOME = Path(os.environ.get("SAU_HOME", Path.home() / "claude-projects/tools/social-auto-upload"))
PLATFORMS = ["bilibili", "douyin", "kuaishou", "xiaohongshu", "tencent", "youtube", "weibo", "baijiahao", "alipay", "hupu"]
# Title length limits (characters; measured from the platform upload pages / sau source); None = not known
TITLE_MAX = {"bilibili": 80, "douyin": 30, "xiaohongshu": 20, "youtube": 100}
BILI_AI_DECLARATION = {"creation_statement": {"id": 1}}  # "含AI生成内容"; verified 2026-09-24 that the app endpoint accepts it
DOUYIN_AI_DECLARATION = "内容由AI生成"


def cookie_file(platform, account):
    return SAU_HOME / "cookies" / f"{platform}_{account}.json"


def merged(manifest, platform):
    """Platform config overrides the shared fields."""
    base = {k: manifest.get(k) for k in ("title", "desc", "tags", "schedule", "ai_generated", "account")}
    base.update(manifest["platforms"][platform] or {})
    base.setdefault("account", "main")
    base["tags"] = base.get("tags") or []
    return base


def check(platform, cfg):
    """Return a list of problems; empty means OK to publish."""
    errs = []
    files = cfg.get("files") or ([cfg["file"]] if cfg.get("file") else [])
    if not files:
        errs.append("no video file (file / files)")
    for f in files:
        if not Path(f).expanduser().is_file():
            errs.append(f"video not found: {f}")
    if len(files) > 1 and platform != "bilibili":
        errs.append("only Bilibili supports multiple parts; other platforms take a single file")
    for k in ("cover", "cover_portrait", "cover_landscape"):
        if cfg.get(k) and not Path(cfg[k]).expanduser().is_file():
            errs.append(f"{k} not found: {cfg[k]}")
    title = cfg.get("title") or ""
    if not title:
        errs.append("title is empty")
    lim = TITLE_MAX.get(platform)
    if lim and len(title) > lim:
        errs.append(f"title is {len(title)} chars, over {platform}'s limit of {lim} (shorten it in platforms.{platform}.title)")
    if platform == "bilibili" and not cfg.get("tid"):
        errs.append("Bilibili needs tid (AI videos: 231 Computer Technology / 230 Software Applications)")
    if platform == "bilibili" and len(cfg["tags"]) > 10:
        errs.append(f"Bilibili allows at most 10 tags, got {len(cfg['tags'])}")
    return errs


def build_cmd(platform, cfg):
    x = lambda p: str(Path(p).expanduser())
    acct, title, desc, tags = cfg["account"], cfg["title"], cfg.get("desc") or "", cfg["tags"]
    if platform == "bilibili":
        extra = dict(cfg.get("extra_fields") or {})
        if cfg.get("ai_generated"):
            extra.update(BILI_AI_DECLARATION)
        cmd = ["biliup", "-u", x(cookie_file("bilibili", acct)), "upload", *[x(f) for f in cfg.get("files") or [cfg["file"]]],
               "--title", title, "--desc", desc, "--tid", str(cfg["tid"]), "--copyright", str(cfg.get("copyright", 1)),
               "--tag", ",".join(tags)]
        if cfg.get("cover"): cmd += ["--cover", x(cfg["cover"])]
        if cfg.get("mission_id"): cmd += ["--mission-id", str(cfg["mission_id"])]
        if cfg.get("schedule"):  # biliup takes a 10-digit timestamp, at least 4 hours out
            import datetime
            ts = int(datetime.datetime.strptime(cfg["schedule"], "%Y-%m-%d %H:%M").timestamp())
            cmd += ["--dtime", str(ts)]
        if extra: cmd += ["--extra-fields", json.dumps(extra, ensure_ascii=False)]
        return cmd + list(cfg.get("args") or [])
    cmd = ["sau", platform, "upload-video", "--account", acct, "--file", x(cfg["file"]), "--title", title]
    if desc: cmd += ["--desc", desc]
    if tags: cmd += ["--tags", ",".join(tags)]
    if cfg.get("schedule") and platform in ("douyin", "kuaishou", "xiaohongshu", "tencent"):
        cmd += ["--schedule", cfg["schedule"]]
    if cfg.get("cover"): cmd += ["--thumbnail", x(cfg["cover"])]
    if platform in ("douyin", "tencent"):
        if cfg.get("cover_portrait"): cmd += ["--thumbnail-portrait", x(cfg["cover_portrait"])]
        if cfg.get("cover_landscape"): cmd += ["--thumbnail-landscape", x(cfg["cover_landscape"])]
    if platform == "douyin" and cfg.get("ai_generated"):
        cmd += ["--declaration", cfg.get("declaration") or DOUYIN_AI_DECLARATION]
    if platform == "tencent" and cfg.get("short_title"): cmd += ["--short-title", cfg["short_title"]]
    if platform == "youtube": cmd += ["--visibility", cfg.get("visibility", "public")]
    if cfg.get("collection") and platform not in ("xiaohongshu", "hupu", "youtube"):
        cmd += ["--collection", cfg["collection"]]
    return cmd + list(cfg.get("args") or [])


def logged_in(platform, account):
    r = subprocess.run(["sau", platform, "check", "--account", account], capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1:] == ["valid"]


def bili_session(account="main"):
    d = json.loads(cookie_file("bilibili", account).read_text())
    return "; ".join(f"{c['name']}={c['value']}" for c in d["cookie_info"]["cookies"])


def verify_bilibili(bvid, account="main"):
    """Read the submission back from the creator-center API (which exposes the AI declaration / event / content type)."""
    req = urllib.request.Request(f"https://member.bilibili.com/x/vupre/web/archive/view?bvid={bvid}",
                                 headers={"Cookie": bili_session(account), "User-Agent": "Mozilla/5.0"})
    d = json.load(urllib.request.urlopen(req, timeout=20))
    a = (d.get("data") or {}).get("archive") or {}
    vids = (d.get("data") or {}).get("videos") or []
    return {"code": d.get("code"), "state": a.get("state_desc"), "title": a.get("title"), "tid": a.get("tid"),
            "declaration": (a.get("creation_statement") or {}).get("content") or "(none)",
            "mission_id": a.get("mission_id"), "tags": a.get("tag"), "parts": [v.get("title") for v in vids]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--only", help="comma-separated platforms")
    ap.add_argument("--go", action="store_true", help="actually publish (default is a dry run)")
    ap.add_argument("--headed", action="store_true", help="sau platforms use a visible browser window (use this the first time, when SMS verification is likely)")
    ap.add_argument("--verify-bilibili", metavar="BVID")
    a = ap.parse_args()

    if a.verify_bilibili:
        print(json.dumps(verify_bilibili(a.verify_bilibili), ensure_ascii=False, indent=2)); return
    if not a.manifest:
        ap.error("manifest required")

    m = json.loads(Path(a.manifest).read_text())
    targets = [p for p in PLATFORMS if p in m["platforms"]]
    if a.only:
        want = a.only.split(",")
        bad = [p for p in want if p not in m["platforms"]]
        if bad: sys.exit(f"not in manifest: {bad}")
        targets = [p for p in targets if p in want]

    plan, failed = [], False
    for p in targets:
        cfg = merged(m, p)
        errs = check(p, cfg)
        print(f"\n[{p}] {'OK' if not errs else 'ERROR'}")
        for e in errs: print("   x", e)
        if errs: failed = True; continue
        cmd = build_cmd(p, cfg) + (["--headed"] if a.headed and p != "bilibili" else [])
        print("   $", " ".join(repr(c) if " " in c or "\n" in c else c for c in cmd)[:600])
        plan.append((p, cfg, cmd))
    if failed: sys.exit("\nFix the errors above before publishing.")
    if not a.go:
        print("\n(dry run: nothing published; add --go to publish)"); return

    results = {}
    for p, cfg, cmd in plan:
        if p != "bilibili" and not logged_in(p, cfg["account"]):
            results[p] = f"skipped: not logged in -> sau {p} login --account {cfg['account']}"; continue
        if p == "bilibili" and not cookie_file("bilibili", cfg["account"]).exists():
            results[p] = f"skipped: not logged in -> sau bilibili login --account {cfg['account']}"; continue
        print(f"\n>>> publishing {p} ...", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        out = re.sub(r"\x1b\[[0-9;]*m", "", r.stdout + r.stderr)
        if p == "bilibili":
            bv = re.search(r'"bvid": String\("(BV\w+)"\)', out)
            if bv:
                v = verify_bilibili(bv.group(1), cfg["account"])
                ok = (not cfg.get("ai_generated") or v["declaration"] == "含AI生成内容") and \
                     (not cfg.get("mission_id") or v["mission_id"] == cfg["mission_id"])
                results[p] = f"{bv.group(1)} {v['state']} | declaration: {v['declaration']} | mission: {v['mission_id']} | " \
                             f"parts: {v['parts']} {'✓' if ok else '✗ read-back does not match the manifest'}"
            else:
                results[p] = "failed: " + out.strip().splitlines()[-1][:300] if out.strip() else "failed"
        else:
            tail = [l for l in out.strip().splitlines() if l.strip()][-3:]
            results[p] = ("ok" if r.returncode == 0 else f"failed (exit {r.returncode})") + " | " + " / ".join(tail)[:300]
    print("\n==== results")
    for p, s in results.items(): print(f"{p:12} {s}")


if __name__ == "__main__":
    main()
