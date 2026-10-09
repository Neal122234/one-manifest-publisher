# Video publishing playbook

## Process (in order; don't skip steps)

1. **Agree the checklist before rendering**: language, which versions (landscape / portrait / multi-part), on-screen text rules (explanatory text only, no story/meme text), title, credit line. Render nothing until this is agreed.
2. **Review from a draft**: `./render.sh --draft <target>` renders at half resolution, or check in Remotion Studio preview. The final version is rendered once only, and only the versions you'll actually use.
3. **Research before publishing**: `python3 research/bili_research.py hot <keywords>` to see which categories, tags and title styles the hot videos of the same theme use in the last 7 days.
4. **Write the manifest**: copy `examples/example.json` and edit it. `python3 publish.py <manifest>` does a dry-run check (title length, file existence, category, tag count).
5. **Publish**: `python3 publish.py <manifest> --go`. Bilibili is read back and checked automatically after publishing; for other platforms, check the platform's creator dashboard.
6. **Review a few hours later**: `python3 research/bili_research.py rank <BV> <keywords>` to see where it ranks for its keywords.

## Platforms

| Platform | Tool | Title limit | AI declaration | Notes |
|---|---|---|---|---|
| Bilibili | biliup (direct) | 80 | `creation_statement:{id:1}` **auto, verified working** | Multi-part, event (mission_id), cover, schedule (≥4 h out) |
| Douyin | sau | 30 | `--declaration 内容由AI生成` auto | Portrait 9:16; cover 3:4 `cover_portrait` |
| Kuaishou | sau | — | not supported, add manually if needed | Portrait |
| Xiaohongshu | sau | 20 | not supported | Portrait; hashtags are important |
| WeChat Channels (tencent) | sau | — | not supported | Short title 6–16 chars via `short_title` |
| YouTube | sau | 100 | not supported | Needs a proxy: set `YT_PROXY` in `$SAU_HOME/conf.py` |
| Weibo / Baijiahao / Alipay / Hupu | sau | — | not supported | Hupu audience is sports/gaming; pick content that fits |

Log in: prefer `$SAU_HOME/.venv/bin/python login_window.py <platform>` (opens a window and waits up to 15 minutes for the user to scan the QR code or use an SMS code; sau's own login only waits 2 minutes, so the QR code often expires). Alternatively have the user run `sau <platform> login --account main` in their own terminal and scan the QR code (the QR expires in about 2 minutes; if it's hard to scan in the terminal, `open` the qrcode.png it saves). Credentials are saved in `$SAU_HOME/cookies/` and **never go into the repo**.

## Bilibili lessons (verified 2026-09-24)

- **Category decides first-round distribution**: AI topics go in Tech → Computer Technology `tid 231` (where the hot Opus 5.5 videos sit). The first submission landed in Daily Life `tid 21`: 8 plays, and it didn't show in the top 100 for any keyword.
- **Don't publish in the small hours.** Evening peak (18–22) or schedule it.
- **Title**: put the model name at the very front, plus a hook word (全程自动 / 震惊瘫坐 / 核弹) plus a concrete result. Put `Opus 5.5` with a space.
- **Events can only be joined on the first submission**: `mission_id` (e.g. AI无限竞技场 4070254). After submitting, an edit can only add the topic, not join the event. Once you pick one event topic, tags exclusive to other events (AI IN ALL!, AI整活全宇宙) are rejected.
- **The creation declaration can never be changed once submitted** (the edit page greys it out permanently), so it must be set on the first submission.
- The content type `human_type2` (1011 人工智能) has no effect through biliup's app endpoint; it can only be chosen in the web upload page.
- When uploading via the web page: dragging two files in at once creates **two separate submissions**. For multi-part, use "添加分P" (add part).
- Search indexing is fast (minutes), but ranking depends on plays/engagement. Being indexed ≠ being findable.
- Duplicate submissions of the same content risk being flagged; when republishing, have the user delete the old one first (Claude doesn't delete it on their behalf).

## Douyin lessons (verified 2026-09-27)

- **The first publish from a new device triggers SMS verification**: use `--headed` and have the user type the code into the window themselves (Claude doesn't handle verification codes); after that it publishes automatically.
- sau's `DEBUG_MODE=True` takes a full-page screenshot before clicking publish, and it hangs waiting for fonts (it once blocked for 30 minutes). `setup.sh` turns it off.
- The Playwright browser must not live in `~/Library/Caches` (macOS cleanup deletes it); `setup.sh` installs it under `~/claude-projects/tools/ms-playwright`.
- Check whether it published: the "作品" (works) list in the creator dashboard (`creator.douyin.com/creator-micro/content/manage`). New works show "审核中" (under review) first.
- Titles: hooks like suspense or contrast ("我让AI自己做视频，它交出了这个…"); a project name nobody knows doesn't draw clicks.
