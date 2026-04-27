#!/usr/bin/env bash
# =============================================================================
# install-extra-tools.sh -- Shell, dev & utility tool additions
# =============================================================================
# Tools: caddy, glow (charm), eza, zoxide, starship, lazydocker,
#        bottom, dust, just, jless, watchexec, procs, tldr, duf, miller
# =============================================================================

set -euo pipefail

export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
step()  { echo -e "\n${CYAN}==> $1${NC}"; }
ok()    { echo -e "  ${GREEN}ok${NC}  $1"; }
skip()  { echo -e "  ${YELLOW}skip${NC} $1"; }

# --------------------------------------------------------------------------- #
# APT repos
# --------------------------------------------------------------------------- #
step "Registering external APT repos"

# Caddy
if ! dpkg -l caddy &>/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
  ok "Caddy repo registered"
else
  skip "Caddy repo"
fi

# Charm (glow markdown renderer, vhs, etc.)
if ! dpkg -l glow &>/dev/null; then
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://repo.charm.sh/apt/gpg.key \
    | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg
  echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" \
    | sudo tee /etc/apt/sources.list.d/charm.list > /dev/null
  ok "Charm repo registered"
else
  skip "Charm repo"
fi

# eza
if ! dpkg -l eza &>/dev/null; then
  sudo mkdir -p /etc/apt/keyrings
  wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc \
    | sudo gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
  echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" \
    | sudo tee /etc/apt/sources.list.d/gierens.list > /dev/null
  sudo chmod 644 /etc/apt/keyrings/gierens.gpg /etc/apt/sources.list.d/gierens.list
  ok "eza repo registered"
else
  skip "eza repo"
fi

step "apt-get update"
sudo apt-get update -qq

step "Installing APT tools: caddy glow eza zoxide"
sudo apt-get install -y caddy glow eza zoxide 2>&1 | grep "Setting up" || true
ok "APT tools installed"

# --------------------------------------------------------------------------- #
# Starship prompt (official install script)
# --------------------------------------------------------------------------- #
step "Installing starship"
if command -v starship &>/dev/null; then
  skip "starship ($(starship --version | head -1))"
else
  curl -sS https://starship.rs/install.sh | sh -s -- --yes
  ok "starship installed"
fi

# --------------------------------------------------------------------------- #
# GitHub binary installer
# --------------------------------------------------------------------------- #
install_gh_binary() {
  local name="$1" repo="$2" asset_pattern="$3" bin_name="$4"

  if command -v "$bin_name" &>/dev/null; then
    skip "$name ($(command -v "$bin_name"))"
    return 0
  fi

  echo -e "  installing $name..."
  local asset_url
  asset_url=$(curl -s "https://api.github.com/repos/${repo}/releases/latest" \
    | jq -r --arg p "$asset_pattern" \
        '.assets[].browser_download_url | select(test($p))' \
    | head -1)

  if [ -z "$asset_url" ]; then
    echo "  WARN: no release asset matched pattern '$asset_pattern' for $repo"
    return 1
  fi

  local tmpdir
  tmpdir=$(mktemp -d)
  local archive="${tmpdir}/archive"
  curl -fsSL -o "$archive" "$asset_url"

  case "$asset_url" in
    *.tar.gz|*.tgz) tar xf "$archive" -C "$tmpdir" ;;
    *.tar.xz)       tar xJf "$archive" -C "$tmpdir" ;;
    *.zip)          unzip -q "$archive" -d "$tmpdir" ;;
  esac

  local found
  found=$(find "$tmpdir" -name "$bin_name" -type f | head -1)
  if [ -n "$found" ]; then
    sudo install "$found" /usr/local/bin/
    ok "$name"
  else
    echo "  WARN: binary '$bin_name' not found in archive for $name"
  fi
  rm -rf "$tmpdir"
}

step "Installing binary tools from GitHub"
install_gh_binary "lazydocker" "jesseduffield/lazydocker" "lazydocker_.*_Linux_x86_64\\.tar\\.gz$"     "lazydocker"
install_gh_binary "bottom"     "ClementTsang/bottom"      "bottom_x86_64-unknown-linux-gnu\\.tar\\.gz$" "btm"
install_gh_binary "dust"       "bootandy/dust"            "dust-.*-x86_64-unknown-linux-gnu\\.tar\\.gz$" "dust"
install_gh_binary "just"       "casey/just"               "just-.*-x86_64-unknown-linux-musl\\.tar\\.gz$" "just"
install_gh_binary "jless"      "PaulJuliusMartinez/jless" "jless-.*-x86_64-unknown-linux-gnu\\.zip$"   "jless"
install_gh_binary "watchexec"  "watchexec/watchexec"      "watchexec-.*-x86_64-unknown-linux-gnu\\.tar\\.xz$" "watchexec"
install_gh_binary "procs"      "dalance/procs"            "procs-.*-x86_64-unknown-linux\\.zip$"       "procs"

# --------------------------------------------------------------------------- #
# tldr via npm
# --------------------------------------------------------------------------- #
step "Installing tldr"
if command -v tldr &>/dev/null; then
  skip "tldr"
else
  npm install -g tldr --silent
  ok "tldr"
fi

# --------------------------------------------------------------------------- #
# Starship config (minimal, sensible defaults)
# --------------------------------------------------------------------------- #
step "Creating starship.toml"
mkdir -p "$HOME/.config"
if [ ! -f "$HOME/.config/starship.toml" ]; then
  cat > "$HOME/.config/starship.toml" << 'TOML'
"$schema" = 'https://starship.rs/config-schema.json'

add_newline = true

[character]
success_symbol = "[❯](bold green)"
error_symbol   = "[❯](bold red)"

[git_branch]
symbol = "⎇ "

[git_status]
ahead  = "⇡${count}"
behind = "⇣${count}"
staged = "[+${count}](green)"
modified = "[!${count}](yellow)"
untracked = "[?${count}](blue)"

[python]
symbol = "🐍 "
detect_extensions = ["py"]

[nodejs]
symbol = "⬢ "

[docker_context]
symbol = "🐳 "

[directory]
truncation_length   = 4
truncate_to_repo    = true
TOML
  ok "~/.config/starship.toml written"
else
  skip "~/.config/starship.toml already exists"
fi

# --------------------------------------------------------------------------- #
# .bashrc wiring for zoxide + starship
# --------------------------------------------------------------------------- #
step "Wiring zoxide + starship into ~/.bashrc"

if ! grep -q "zoxide init" ~/.bashrc; then
  echo 'eval "$(zoxide init bash)"' >> ~/.bashrc
  ok "zoxide init added"
else
  skip "zoxide init already in ~/.bashrc"
fi

if ! grep -q "starship init" ~/.bashrc; then
  # Must be last so it can read $? from every command
  echo 'eval "$(starship init bash)"' >> ~/.bashrc
  ok "starship init added"
else
  skip "starship init already in ~/.bashrc"
fi

# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #
echo -e "\n${CYAN}=== Verification ===${NC}"
for cmd in caddy glow eza zoxide starship lazydocker btm dust just jless watchexec procs tldr duf mlr; do
  if command -v "$cmd" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC}  $cmd"
  else
    echo -e "  \033[0;31m✗\033[0m  $cmd  NOT FOUND"
  fi
done
echo ""
