#!/usr/bin/env python3
"""Bilibili topic-selection / traffic research (public search API, no login needed).

  python3 research/bili_research.py hot "Opus 5.5" "AI编程" --days 7     # recent hot videos: category/tag/title stats
  python3 research/bili_research.py rank BV1xxxx "Opus 5.5" "Claude"     # where your video ranks for each keyword (top 100)
  python3 research/bili_research.py video BV1xxxx                        # public info for one video (category/plays/parts)
"""
import argparse, collections, http.cookiejar, json, re, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
_jar = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))
_op.addheaders = [("User-Agent", UA), ("Referer", "https://search.bilibili.com")]


def _get(url):
    if not _jar:  # get buvid3 first, otherwise search returns 412
        _op.open("https://www.bilibili.com/", timeout=15).read()
    return json.load(_op.open(url, timeout=15))


def search(kw, order="totalrank", page=1):
    u = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&order={order}&page={page}&keyword={urllib.parse.quote(kw)}"
    return (_get(u).get("data") or {}).get("result") or []


clean = lambda t: re.sub("<.*?>", "", t)


def cmd_hot(kws, days, top):
    now, seen = time.time(), {}
    for kw in kws:
        for order in ("click", "totalrank"):
            for r in search(kw, order):
                if now - r["pubdate"] < days * 86400: seen[r["bvid"]] = r
            time.sleep(0.4)
    rows = sorted(seen.values(), key=lambda r: -r["play"])
    print(f"{len(rows)} videos in the last {days} days")
    print("category:", collections.Counter(r["typename"] for r in rows).most_common(12))
    print("tags:", collections.Counter(x for r in rows for x in r["tag"].split(",") if x).most_common(30))
    for r in rows[:top]:
        print(f"{r['play']:>8} {r['duration']:>6} {r['typename']:<6} {clean(r['title'])[:70]}")


def cmd_rank(bvid, kws, pages=5):
    for kw in kws:
        found, tot = None, 0
        for pg in range(1, pages + 1):
            res = search(kw, page=pg)
            for i, r in enumerate(res):
                if r["bvid"] == bvid: found = tot + i + 1
            tot += len(res)
            if found or not res: break
            time.sleep(0.3)
        print(f"{kw}: {'#%d' % found if found else 'not in top %d' % tot}")


def cmd_video(bvid):
    _get("https://api.bilibili.com/x/web-interface/nav")
    d = _get(f"https://api.bilibili.com/x/web-interface/wbi/view?bvid={bvid}")
    if d.get("code"): print(d.get("message")); return
    v = d["data"]
    print(json.dumps({"title": v["title"], "owner": v["owner"]["name"], "tid": v["tid"], "tid_v2": v.get("tid_v2"),
                      "view": v["stat"]["view"], "like": v["stat"]["like"], "parts": len(v["pages"]),
                      "pubdate": time.strftime("%Y-%m-%d %H:%M", time.localtime(v["pubdate"]))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    h = sp.add_parser("hot"); h.add_argument("keywords", nargs="+"); h.add_argument("--days", type=int, default=7); h.add_argument("--top", type=int, default=25)
    r = sp.add_parser("rank"); r.add_argument("bvid"); r.add_argument("keywords", nargs="+")
    v = sp.add_parser("video"); v.add_argument("bvid")
    a = ap.parse_args()
    {"hot": lambda: cmd_hot(a.keywords, a.days, a.top), "rank": lambda: cmd_rank(a.bvid, a.keywords),
     "video": lambda: cmd_video(a.bvid)}[a.cmd]()
