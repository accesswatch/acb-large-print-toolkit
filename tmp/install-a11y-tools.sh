#!/usr/bin/env bash
# install-a11y-tools.sh  -- one-time install of web accessibility dev tools
set -euo pipefail
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
step()  { echo -e "\n${CYAN}==> $1${NC}"; }
ok()    { echo -e "  ${GREEN}ok${NC}  $1"; }
skip()  { echo -e "  ${YELLOW}skip${NC} $1 (already installed)"; }

install_npm() {
  local pkg="$1" bin="$2"
  if command -v "$bin" &>/dev/null; then
    skip "$pkg"
  else
    npm install -g "$pkg" --silent 2>&1 | tail -2
    ok "$pkg"
  fi
}

# --------------------------------------------------------------------------- #
# npm global a11y tools
# --------------------------------------------------------------------------- #
step "Installing npm accessibility tools"

install_npm "@axe-core/cli"                          "axe"
install_npm "@lhci/cli"                              "lhci"
install_npm "pa11y"                                  "pa11y"
install_npm "html-validate"                          "html-validate"
install_npm "markdownlint-cli2"                      "markdownlint-cli2"
install_npm "stylelint"                              "stylelint"
install_npm "stylelint-config-standard"              "stylelint-config-standard" 2>/dev/null || true
install_npm "@ibm/equal-access-accessibility-checker" "achecker"

# --------------------------------------------------------------------------- #
# act -- run GitHub Actions locally
# --------------------------------------------------------------------------- #
step "Installing act (GitHub Actions local runner)"

if command -v act &>/dev/null; then
  skip "act"
else
  echo "  downloading act..."
  tmpdir=$(mktemp -d)
  asset_url=$(curl -s https://api.github.com/repos/nektos/act/releases/latest \
    | jq -r '.assets[].browser_download_url | select(test("act_Linux_x86_64\\.tar\\.gz$"))')
  curl -fsSL -o "$tmpdir/act.tar.gz" "$asset_url"
  tar xf "$tmpdir/act.tar.gz" -C "$tmpdir"
  sudo install "$tmpdir/act" /usr/local/bin/
  rm -rf "$tmpdir"
  ok "act $(act --version)"
fi

# --------------------------------------------------------------------------- #
# stylelint-a11y plugin (needs to be alongside stylelint)
# --------------------------------------------------------------------------- #
step "Installing stylelint-a11y plugin"
if npm list -g stylelint-a11y &>/dev/null 2>&1; then
  skip "stylelint-a11y"
else
  npm install -g stylelint-a11y --silent 2>&1 | tail -2
  ok "stylelint-a11y"
fi

# --------------------------------------------------------------------------- #
# Verify
# --------------------------------------------------------------------------- #
step "Verification"
echo ""
for item in "axe:axe" "lhci:lhci" "pa11y:pa11y" "html-validate:html-validate" "markdownlint-cli2:markdownlint-cli2" "stylelint:stylelint" "achecker:achecker" "act:act"; do
  name="${item%%:*}"
  cmd="${item##*:}"
  if command -v "$cmd" &>/dev/null; then
    ver=$("$cmd" --version 2>/dev/null | head -1 || echo "installed")
    echo -e "  ${GREEN}✓${NC}  $name  $ver"
  else
    echo -e "  \033[0;31m✗\033[0m  $name  NOT FOUND"
  fi
done
echo ""
echo "Done! 🎉"
