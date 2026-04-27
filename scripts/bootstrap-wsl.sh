#!/usr/bin/env bash
# =============================================================================
# bootstrap-wsl.sh -- GLOW WSL Ubuntu 24.04 Development Environment Bootstrap
# =============================================================================
# Idempotent: safe to re-run on an existing instance.
#
# Usage (from Windows PowerShell):
#   wsl -d Ubuntu -- bash /mnt/d/code/glow/scripts/bootstrap-wsl.sh
#
# Usage (from inside WSL):
#   bash /mnt/d/code/glow/scripts/bootstrap-wsl.sh
#
# What it installs:
#   - System packages (apt): build tools, languages, DB clients, Playwright deps
#   - External APT repos: PowerShell, Node.js 22, GitHub CLI, deadsnakes Python 3.13
#   - Global npm tools:  Codex, Gemini CLI, Claude Code
#   - pipx tools:        aider-chat, black, ruff, uv, httpie, pre-commit
#   - Binary tools:      lazygit (latest release)
#   - Git config:        delta, rerere, prune, VS Code as editor
#   - Shell config:      ~/.bashrc aliases and PATH entries
# =============================================================================

set -euo pipefail

REPO_ROOT="/mnt/d/code/glow"
GIT_NAME="Jeff Bishop"
GIT_EMAIL="jeffbis@arizona.edu"

# Colour helpers
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
step()  { echo -e "\n${CYAN}==> $1${NC}"; }
ok()    { echo -e "  ${GREEN}ok${NC}  $1"; }
skip()  { echo -e "  ${YELLOW}skip${NC} $1 (already present)"; }

# --------------------------------------------------------------------------- #
# 1. APT repos
# --------------------------------------------------------------------------- #
step "Registering external APT repositories"

# PowerShell
if ! dpkg -l powershell &>/dev/null; then
  curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor \
    | sudo tee /usr/share/keyrings/microsoft-prod.gpg > /dev/null
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
https://packages.microsoft.com/ubuntu/24.04/prod noble main" \
    | sudo tee /etc/apt/sources.list.d/microsoft-prod.list > /dev/null
  ok "PowerShell repo registered"
else
  skip "PowerShell repo"
fi

# Node.js 22
if ! dpkg -l nodejs &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - 2>&1 | tail -3
  ok "NodeSource 22 repo registered"
else
  skip "NodeSource repo"
fi

# GitHub CLI
if ! dpkg -l gh &>/dev/null; then
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null
  sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
  ok "GitHub CLI repo registered"
else
  skip "GitHub CLI repo"
fi

# Python 3.13 (deadsnakes)
if ! dpkg -l python3.13 &>/dev/null; then
  sudo add-apt-repository -y ppa:deadsnakes/ppa 2>&1 | tail -3
  ok "deadsnakes PPA registered"
else
  skip "deadsnakes PPA"
fi

# --------------------------------------------------------------------------- #
# 2. APT packages
# --------------------------------------------------------------------------- #
step "Updating package lists"
sudo apt-get update -qq

step "Installing APT packages"

# Core utilities
APT_CORE=(
  curl wget git git-lfs gnupg ca-certificates lsb-release
  unzip zip p7zip-full rsync
  software-properties-common apt-transport-https
)

# Build tools
APT_BUILD=(
  build-essential gcc g++ gdb cmake ninja-build
  clang clang-format clang-tidy lldb valgrind
  autoconf automake libtool pkg-config
)

# Shell & editors
APT_SHELL=(
  bash zsh vim nano tmux tree
  jq yq fd-find ripgrep bat fzf
  shellcheck shfmt
)

# Python
APT_PYTHON=(
  python3 python3-dev python3-pip python3-venv pipx
  python3.13 python3.13-dev python3.13-venv
)

# Node / PowerShell / gh
APT_TOOLS=(
  nodejs powershell gh
)

# Database clients
APT_DB=(
  sqlite3 libsqlite3-dev
  default-mysql-client postgresql-client redis-tools
)

# PHP (for tooling compat)
APT_PHP=(
  php php-cli php-common php-curl php-gd php-intl
  php-mbstring php-mysql php-sqlite3 php-xml php-zip
  composer
)

# Playwright system dependencies
APT_PLAYWRIGHT=(
  xvfb fonts-liberation fonts-noto-color-emoji
  fonts-freefont-ttf fonts-ipafont-gothic fonts-tlwg-loma-otf
  fonts-unifont fonts-wqy-zenhei xfonts-cyrillic xfonts-scalable
  libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64
  libcairo2 libcups2t64 libdbus-1-3 libdrm2 libfontconfig1 libfreetype6
  libgbm1 libglib2.0-0t64 libnspr4 libnss3 libpango-1.0-0 libsqlite3-dev
  libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3
  libxkbcommon0 libxrandr2
)

# Combine and install (apt is idempotent)
ALL_APT=(
  "${APT_CORE[@]}"
  "${APT_BUILD[@]}"
  "${APT_SHELL[@]}"
  "${APT_PYTHON[@]}"
  "${APT_TOOLS[@]}"
  "${APT_DB[@]}"
  "${APT_PHP[@]}"
  "${APT_PLAYWRIGHT[@]}"
  # Extras
  htop ncdu git-delta openssh-client init
)

sudo apt-get install -y "${ALL_APT[@]}" 2>&1 | grep -E "^(Setting up|Preparing|Get:)" | head -40 || true
ok "APT packages installed"

# --------------------------------------------------------------------------- #
# 3. npm global user prefix + AI CLIs
# --------------------------------------------------------------------------- #
step "Configuring npm user prefix"
mkdir -p "$HOME/.npm-global"
npm config set prefix "$HOME/.npm-global"
ok "npm prefix -> ~/.npm-global"

step "Installing npm AI CLIs"
export PATH="$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

install_npm() {
  local pkg="$1" bin="$2"
  if command -v "$bin" &>/dev/null; then
    skip "$pkg"
  else
    npm install -g "$pkg" --silent
    ok "$pkg"
  fi
}

install_npm "@openai/codex"            "codex"
install_npm "@google/gemini-cli"       "gemini"
install_npm "@anthropic-ai/claude-code" "claude"

# --------------------------------------------------------------------------- #
# 4. pipx tools
# --------------------------------------------------------------------------- #
step "Installing pipx tools"

install_pipx() {
  local pkg="$1" bin="$2"
  if pipx list 2>/dev/null | grep -q "package ${pkg%@*}"; then
    skip "$pkg"
  else
    pipx install "$pkg"
    ok "$pkg"
  fi
}

install_pipx "aider-chat"  "aider"
install_pipx "black"       "black"
install_pipx "ruff"        "ruff"
install_pipx "uv"          "uv"
install_pipx "httpie"      "http"
install_pipx "pre-commit"  "pre-commit"

# --------------------------------------------------------------------------- #
# 5. lazygit (binary from GitHub releases)
# --------------------------------------------------------------------------- #
step "Installing lazygit"
if command -v lazygit &>/dev/null; then
  skip "lazygit ($(lazygit --version 2>/dev/null | grep -oP 'version=\K[^,]+'))"
else
  LAZYGIT_VERSION=$(curl -s https://api.github.com/repos/jesseduffield/lazygit/releases/latest \
    | jq -r '.tag_name' | sed 's/v//')
  curl -Lo /tmp/lazygit.tar.gz \
    "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
  tar xf /tmp/lazygit.tar.gz -C /tmp lazygit
  sudo install /tmp/lazygit /usr/local/bin
  rm -f /tmp/lazygit /tmp/lazygit.tar.gz
  ok "lazygit $LAZYGIT_VERSION"
fi

# --------------------------------------------------------------------------- #
# 6. Git global config
# --------------------------------------------------------------------------- #
step "Configuring git"

git config --global user.name       "$GIT_NAME"
git config --global user.email      "$GIT_EMAIL"
git config --global init.defaultBranch main
git config --global pull.rebase     false
git config --global push.autoSetupRemote true
git config --global fetch.prune     true
git config --global rerere.enabled  true
git config --global core.editor     "code --wait"
git config --global core.pager      "delta"
git config --global interactive.diffFilter "delta --color-only"
git config --global delta.navigate  true
git config --global delta.light     false
git config --global delta.line-numbers true
git config --global merge.conflictStyle diff3
git config --global diff.colorMoved default

# safe.directory for the repo on Windows drive
git config --global --add safe.directory "$REPO_ROOT" 2>/dev/null || true

ok "git configured"

# --------------------------------------------------------------------------- #
# 7. .bashrc additions
# --------------------------------------------------------------------------- #
step "Updating ~/.bashrc"

BASHRC_BLOCK='
# ---- GLOW dev environment ------------------------------------------------- #

# npm user global
export PATH="$HOME/.npm-global/bin:$PATH"

# pipx / pip --user
export PATH="$HOME/.local/bin:$PATH"

# GLOW project aliases
alias glow="cd /mnt/d/code/glow"

# Docker Compose shortcuts
alias dc="docker compose"
alias dcu="docker compose up -d"
alias dcd="docker compose down"
alias dcl="docker compose logs -f"

# bat on Ubuntu is installed as batcat
alias bat="batcat"

# fd on Ubuntu is installed as fdfind
alias fd="fdfind"

# lazygit shortcut
alias lg="lazygit"

# ---- end GLOW dev environment --------------------------------------------- #'

if grep -q "GLOW dev environment" ~/.bashrc; then
  skip "~/.bashrc block already present"
else
  echo "$BASHRC_BLOCK" >> ~/.bashrc
  ok "~/.bashrc updated"
fi

# --------------------------------------------------------------------------- #
# 8. Verify
# --------------------------------------------------------------------------- #
step "Verification"
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

check() {
  local name="$1" cmd="$2"
  if ver=$(eval "$cmd" 2>/dev/null | head -1); then
    echo -e "  ${GREEN}✓${NC}  $name: $ver"
  else
    echo -e "  \033[0;31m✗\033[0m  $name: NOT FOUND"
  fi
}

check "pwsh"       "pwsh --version"
check "node"       "node --version"
check "npm"        "npm --version"
check "python3.13" "python3.13 --version"
check "gh"         "gh --version | head -1"
check "tmux"       "tmux -V"
check "git"        "git --version"
check "lazygit"    "lazygit --version | grep -oP 'version=\K[^,]+' | sed 's/^/v/'"
check "codex"      "codex --version"
check "gemini"     "gemini --version"
check "claude"     "claude --version"
check "aider"      "aider --version"
check "rg"         "rg --version | head -1"
check "batcat"     "batcat --version | head -1"
check "fzf"        "fzf --version"
check "delta"      "delta --version"
check "ruff"       "ruff --version"
check "black"      "black --version"
check "uv"         "uv --version"
check "pre-commit" "pre-commit --version"
check "http"       "http --version"

echo ""
echo -e "${GREEN}Bootstrap complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Enable Docker Desktop WSL integration:"
echo "     Docker Desktop → Settings → Resources → WSL Integration → Ubuntu → ON → Apply & Restart"
echo "  2. Set your API keys in ~/.bashrc:"
echo "     export OPENAI_API_KEY=..."
echo "     export ANTHROPIC_API_KEY=..."
echo "     export GEMINI_API_KEY=..."
echo "  3. Authenticate GitHub CLI:"
echo "     gh auth login"
echo "  4. Run: source ~/.bashrc"
