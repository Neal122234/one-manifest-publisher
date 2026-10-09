#!/bin/zsh
# One-shot install for the publishing toolchain (macOS, tested on Apple Silicon). Safe to re-run.
set -e
KIT=$(cd "$(dirname "$0")" && pwd)
SAU_HOME=${SAU_HOME:-$HOME/claude-projects/tools/social-auto-upload}
PY=${PY:-$(command -v python3.12 || command -v python3.11 || command -v python3.10 || echo /opt/homebrew/bin/python3.10)}
MIRROR=${PIP_MIRROR:-https://pypi.tuna.tsinghua.edu.cn/simple}

# 1. social-auto-upload (sau): multi-platform uploader, needs Python 3.10-3.12
[[ -d $SAU_HOME ]] || git clone --depth 1 https://github.com/dreammis/social-auto-upload "$SAU_HOME"
cd "$SAU_HOME"
[[ -x .venv/bin/sau ]] || "$PY" -m venv .venv
.venv/bin/pip install -q -i "$MIRROR" -e .
.venv/bin/pip install -q -i "$MIRROR" playwright   # upstream pyproject omits it; several platform modules import it directly
[[ -f conf.py ]] || cp conf.example.py conf.py
sed -i '' 's/^DEBUG_MODE = True/DEBUG_MODE = False/' conf.py   # debug screenshots hang waiting for fonts, blocking the publish step
# Browser: install outside ~/Library/Caches (macOS cleanup deletes it there); npmmirror often lacks this version, so use the official CDN
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-$HOME/claude-projects/tools/ms-playwright}
.venv/bin/patchright install chromium

# 2. Put on PATH
mkdir -p ~/.local/bin
rm -f ~/.local/bin/sau
printf '#!/bin/zsh\nexport PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-%s}\nexec %s "$@"\n' "$PLAYWRIGHT_BROWSERS_PATH" "$SAU_HOME/.venv/bin/sau" > ~/.local/bin/sau
chmod +x ~/.local/bin/sau
.venv/bin/python -c "from uploader.bilibili_uploader.runtime import ensure_biliup_binary as e; print(e())" \
  | xargs -I{} ln -sf {} ~/.local/bin/biliup

# 3. Claude skills: this repo's workflow skill + sau's per-platform skills
mkdir -p ~/.claude/skills
ln -sfn "$KIT/skill" ~/.claude/skills/video-publish
for s in "$SAU_HOME"/skills/*/; do ln -sfn "$s" ~/.claude/skills/sau-$(basename "$s"); done

sau --help >/dev/null && biliup --version && echo "OK. Next: log in to each platform once with: $SAU_HOME/.venv/bin/python $KIT/login_window.py <platform> (waits 15 min) or sau <platform> login --account main"
