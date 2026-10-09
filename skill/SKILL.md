---
name: video-publish
description: 把做好的视频发布到 B站/抖音/快手/小红书/视频号/YouTube/微博/百家号/支付宝/虎扑。用户说"发到B站""投稿""多平台发布""发抖音""重新发一遍""查视频搜索排名/热门标签"时使用。一份清单→一条命令，B站自动回读核验。
---

# video-publish

Repo: `~/claude-projects/video-publish-kit` (if missing, clone the user's private repo `video-publish-kit` and run `./setup.sh`).
Read `docs/PLAYBOOK.md` first: the process, the platform table, and the lessons already learned.

## Steps

1. **Research** (Bilibili topics): `python3 research/bili_research.py hot "<keyword>"...`; use the category, tags and title style of hot videos from the last 7 days.
2. **Write the manifest**: copy `examples/example.json`; shared fields at the top, per-platform overrides under `platforms.<p>`. Portrait platforms (douyin/kuaishou/xiaohongshu/tencent) get the 9:16 version and a 3:4 cover.
3. **Dry run**: `python3 publish.py <manifest>`. Fix every ERROR first (title over the limit, missing file, missing tid).
4. **Confirm with the user**: publishing is public and irreversible. List the title / category / tags / platforms / time, and only proceed on an explicit yes.
5. **Log in**: platforms not logged in are skipped automatically and the login command is printed. Have the user run `sau <p> login --account main` in their own terminal and scan the code (**never enter passwords yourself**).
6. **Publish**: `python3 publish.py <manifest> --only <p1,p2> --go`
7. **Verify**: Bilibili is read back automatically (declaration / event / parts); if needed, run `python3 publish.py --verify-bilibili <BV>` again. For other platforms, check the dashboards and report honestly.

## Hard rules
- Bilibili events and the AI declaration can only be set on the first submission; get them right before publishing.
- Before republishing, have the user delete the old submission (Claude doesn't delete it for them) to avoid duplicate-submission flags.
- Content with AI-generated material always carries `ai_generated: true`.
