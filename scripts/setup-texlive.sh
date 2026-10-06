#!/usr/bin/env bash
# Small, frozen TeX Live installation; cached by the reusable build workflow.
set -euo pipefail

: "${TEXLIVE_ROOT:?Set TEXLIVE_ROOT to the installation directory}"
repository=https://ftp.math.utah.edu/pub/tex/historic/systems/texlive/2025/tlnet-final
installer_sha512=a307d7d11bcbd1f054ad0b0d476f7f12bc1a40d07445020edef8713b44453831d18a2f1722c3d2b0ea2e4fe6c06183a79d1c4049495113f412a9f5a570a8614d
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$TEXLIVE_ROOT/.ready" ]; then
  echo "Using cached TeX Live 2025"
  exit 0
fi

scratch="$(mktemp -d)"
trap 'rm -rf -- "$scratch"' EXIT
curl -fsSL --retry 3 "$repository/install-tl-unx.tar.gz" -o "$scratch/install-tl-unx.tar.gz"
printf '%s  %s\n' "$installer_sha512" "$scratch/install-tl-unx.tar.gz" | sha512sum -c -
mkdir "$scratch/installer"
tar -xzf "$scratch/install-tl-unx.tar.gz" --strip-components=1 -C "$scratch/installer"
cat > "$scratch/texlive.profile" <<PROFILE
selected_scheme scheme-minimal
TEXDIR $TEXLIVE_ROOT
TEXMFLOCAL $TEXLIVE_ROOT/texmf-local
TEXMFSYSCONFIG $TEXLIVE_ROOT/texmf-config
TEXMFSYSVAR $TEXLIVE_ROOT/texmf-var
TEXMFHOME $TEXLIVE_ROOT/texmf-home
TEXMFCONFIG $TEXLIVE_ROOT/texmf-user-config
TEXMFVAR $TEXLIVE_ROOT/texmf-user-var
binary_x86_64-linux 1
instopt_adjustpath 0
instopt_letter 0
instopt_portable 1
instopt_write18_restricted 1
tlpdbopt_install_docfiles 0
tlpdbopt_install_srcfiles 0
PROFILE
perl "$scratch/installer/install-tl" --profile "$scratch/texlive.profile" --repository "$repository"
export PATH="$TEXLIVE_ROOT/bin/x86_64-linux:$PATH"
mapfile -t packages < <(sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$script_dir/../.github/texlive/packages.txt")
tlmgr install "${packages[@]}"
# Explicitly select the same Japanese font family checked by CI.
kanji-config-updmap-sys haranoaji
printf '%s\n' "$repository" > "$TEXLIVE_ROOT/repository.txt"
touch "$TEXLIVE_ROOT/.ready"
