#!/usr/bin/env python3
"""Open a real browser window so the user logs in themselves (QR scan / SMS, as they like); save the session once logged in.

sau's built-in login only waits 2 minutes and the QR code often expires; this waits up to --minutes.
Run it with sau's venv (it has patchright), e.g.:
  $SAU_HOME/.venv/bin/python login_window.py douyin --account main
The session is saved to $SAU_HOME/cookies/<platform>_<account>.json (same format sau uses).
"""
import argparse, asyncio, os, time
from pathlib import Path
from patchright.async_api import async_playwright

SAU_HOME = Path(os.environ.get("SAU_HOME", Path.home() / "claude-projects/tools/social-auto-upload"))
# Platform: (login page, cookie name that means "logged in")
SITES = {
    "douyin": ("https://creator.douyin.com/", "sessionid"),
    "kuaishou": ("https://cp.kuaishou.com/", "kuaishou.web.cp.api_st"),
    "xiaohongshu": ("https://creator.xiaohongshu.com/", ("web_session", "galaxy_creator_session_id", "access-token-creator.xiaohongshu.com")),  # creator-centre login sets the latter two
    "tencent": ("https://channels.weixin.qq.com/", "sessionid"),
}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", choices=SITES)
    ap.add_argument("--account", default="main")
    ap.add_argument("--minutes", type=int, default=15)
    a = ap.parse_args()
    url, key = SITES[a.platform]
    out = SAU_HOME / "cookies" / f"{a.platform}_{a.account}.json"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chromium")
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await ctx.new_page()
        await page.goto(url)
        await page.bring_to_front()
        print(f"Window is open: log in to {a.platform} in it (waiting up to {a.minutes} minutes)", flush=True)
        deadline = time.time() + a.minutes * 60
        while time.time() < deadline:
            if browser.is_connected() is False:
                print("Window was closed"); return
            cookies = await ctx.cookies()
            keys = key if isinstance(key, tuple) else (key,)
            if any(c["name"] in keys and c["value"] for c in cookies):
                await asyncio.sleep(3)  # let the page finish writing the rest of the cookies
                out.parent.mkdir(exist_ok=True)
                await ctx.storage_state(path=str(out))
                print(f"LOGIN_OK saved to {out}", flush=True)
                await browser.close(); return
            await asyncio.sleep(2)
        print("LOGIN_TIMEOUT")
        await browser.close()


asyncio.run(main())
