#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ---- procs ---------------------------------------------------------------- #
echo -e "${CYAN}==> Installing procs${NC}"
if command -v procs &>/dev/null; then
  echo -e "  ${YELLOW}skip${NC} procs"
else
  tmpdir=$(mktemp -d)
  asset_url=$(curl -s https://api.github.com/repos/dalance/procs/releases/latest \
    | jq -r '.assets[].browser_download_url | select(test("procs-v.*-x86_64-linux\\.zip$"))')
  curl -fsSL -o "$tmpdir/archive.zip" "$asset_url"
  unzip -q "$tmpdir/archive.zip" -d "$tmpdir"
  sudo install "$tmpdir/procs" /usr/local/bin/
  rm -rf "$tmpdir"
  echo -e "  ${GREEN}ok${NC}  procs"
fi

# ---- tldr ----------------------------------------------------------------- #
echo -e "${CYAN}==> Installing tldr${NC}"
if command -v tldr &>/dev/null; then
  echo -e "  ${YELLOW}skip${NC} tldr"
else
  npm install -g tldr --silent
  echo -e "  ${GREEN}ok${NC}  tldr"
fi

# ---- zoxide + starship wiring --------------------------------------------- #
echo -e "${CYAN}==> Wiring zoxide + starship into ~/.bashrc${NC}"
if ! grep -q "zoxide init" ~/.bashrc; then
  printf '\neval "$(zoxide init bash)"\n' >> ~/.bashrc
  echo -e "  ${GREEN}ok${NC}  zoxide init added"
else
  echo -e "  ${YELLOW}skip${NC} zoxide init"
fi

if ! grep -q "starship init" ~/.bashrc; then
  printf '\neval "$(starship init bash)"\n' >> ~/.bashrc
  echo -e "  ${GREEN}ok${NC}  starship init added"
else
  echo -e "  ${YELLOW}skip${NC} starship init"
fi

# ---- starship.toml -------------------------------------------------------- #
echo -e "${CYAN}==> starship.toml${NC}"
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

[nodejs]
symbol = "⬢ "

[docker_context]
symbol = "🐳 "

[directory]
truncation_length = 4
truncate_to_repo  = true
TOML
  echo -e "  ${GREEN}ok${NC}  ~/.config/starship.toml written"
else
  echo -e "  ${YELLOW}skip${NC} starship.toml already exists"
fi

# ---- verify --------------------------------------------------------------- #
echo -e "\n${CYAN}=== Verification ===${NC}"
for cmd in caddy glow eza zoxide starship lazydocker btm dust just jless watchexec procs tldr duf mlr; do
  if command -v "$cmd" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC}  $cmd"
  else
    echo -e "  \033[0;31m✗\033[0m  $cmd  NOT FOUND"
  fi
done
echo ""
