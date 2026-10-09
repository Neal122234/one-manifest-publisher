# one-manifest-publisher · 一份清单，发十个平台

写一份 JSON 清单，一条命令把视频发到 B 站、抖音、快手、小红书、视频号、YouTube、微博、百家号、支付宝、虎扑。先空跑检查（标题长度、文件、分区），确认后再真发；B 站发完自动回读核对（AI 创作声明、活动、分 P）。

配套 Claude Code skill：对 Claude 说"把这个视频发到 B 站和抖音"，它会按这里的流程写清单、检查、发布、核对。

## 用法

```bash
./setup.sh                                                    # 首次：装 sau / biliup / 浏览器 / Claude skill
$SAU_HOME/.venv/bin/python login_window.py douyin             # 每个平台登录一次（扫码或短信，窗口等 15 分钟）
python3 publish.py examples/example.json                      # 空跑：检查标题长度、文件、分区，打印要执行的命令
python3 publish.py examples/example.json --only bilibili,douyin --go   # 真发
python3 publish.py --verify-bilibili BV1xxxx                  # 回读一条 B 站投稿
python3 research/bili_research.py hot "关键词"                 # 某个话题的热门视频分区 / 标签统计
python3 research/bili_research.py rank BV1xxxx "关键词"        # 查自己的视频在关键词搜索里排第几
```

清单格式见 [examples/example.json](examples/example.json)：顶层字段所有平台共用，`platforms.<平台>` 里的字段覆盖顶层，删掉某个平台就跳过它。

## 组成

| 路径 | 内容 |
|---|---|
| `publish.py` | 读清单 → 校验 → 逐平台调用上传工具 → B 站回读 |
| `login_window.py` | 打开各平台登录窗口，保存登录态 |
| `research/` | B 站热门统计与搜索排名查询 |
| `docs/PLAYBOOK.md` | 完整流程、各平台差异（竖横封面、标题字数、分区）、踩过的坑 |
| `skill/SKILL.md` | Claude Code skill，`setup.sh` 会链接到 `~/.claude/skills/video-publish` |

B 站直接用 [biliup](https://github.com/biliup/biliup-rs)（支持分 P、AI 声明、活动）；其他平台用 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 的 `sau` 命令。

## 说明

- 登录态存在 `$SAU_HOME/cookies/`，在仓库外；`.gitignore` 也挡掉了 cookie、视频和图片。
- 在 macOS（Apple Silicon）上测试过。
- 小红书等平台对重复提交很敏感：一次没成功，先去 App 里看，不要连续重试。
- 代码 MIT 许可。

---

**English** — Write one JSON manifest, run one command, publish a video to up to 10 Chinese and global platforms (Bilibili, Douyin, Kuaishou, Xiaohongshu, WeChat Channels, YouTube, Weibo, Baijiahao, Alipay, Hupu). Dry run first, then `--go`; Bilibili submissions are read back and verified. Ships with a Claude Code skill. MIT.
