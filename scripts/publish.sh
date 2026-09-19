#!/bin/zsh
# Push Jinken Repo to GitHub Pages.
# Credit: Jinken Nguyen - 1989
set -euo pipefail
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Library/Developer/CommandLineTools}"
export PATH="$HOME/.local/bin:/Library/Developer/CommandLineTools/usr/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! gh auth status >/dev/null 2>&1; then
  echo "Chưa đăng nhập GitHub. Chạy:"
  echo "  gh auth login --hostname github.com --git-protocol https --web"
  exit 1
fi

USER="$(gh api user --jq .login)"
echo "GitHub user: $USER"

if [[ "$USER" == "tientrieu19892025" ]]; then
  REPO="tientrieu19892025.github.io"
  BASE="https://tientrieu19892025.github.io"
else
  REPO="${USER}.github.io"
  BASE="https://${USER}.github.io"
  echo "GitHub user $USER → repo $USER/$REPO"
  echo "URL source Sileo: $BASE"
  python3 scripts/update-repo.py --base-url "$BASE"
  git add -A
  git diff --cached --quiet || git commit -m "Set BASE_URL for $USER/$REPO"
fi

if gh repo view "$USER/$REPO" >/dev/null 2>&1; then
  echo "Repo đã tồn tại: https://github.com/$USER/$REPO"
else
  gh repo create "$REPO" --public --source=. --remote=origin --description "Jinken Repo — jailbreak tweaks by Jinken Nguyen - 1989. Donate: MB Bank 0345140889 Nguyen Tien Trieu"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://github.com/$USER/$REPO.git"
else
  git remote set-url origin "https://github.com/$USER/$REPO.git"
fi

git push -u origin main

# Enable GitHub Pages from main / root (user or project site)
gh api -X POST "repos/$USER/$REPO/pages" -f build_type=workflow >/dev/null 2>&1 || \
gh api -X POST "repos/$USER/$REPO/pages" -f source='{"branch":"main","path":"/"}' >/dev/null 2>&1 || \
gh api -X PUT "repos/$USER/$REPO/pages" -f source='{"branch":"main","path":"/"}' >/dev/null 2>&1 || true

echo
echo "Xong."
echo "GitHub : https://github.com/$USER/$REPO"
echo "Pages  : $BASE"
echo "Sileo  : $BASE"
echo "Donate : MB Bank 0345140889 Nguyen Tien Trieu"
echo "Credit : Jinken Nguyen - 1989"
