#!/usr/bin/env bash
# Universal macOS/Linux installer for the ashiba-keisan AI Agent Skill.
# Usage:
#   ./install.sh [--target agents|antigravity|claude|codex|cursor|gemini|copilot|windsurf|project|all]
#   curl -fsSL https://raw.githubusercontent.com/RingLord3812/ashiba-keisan/main/install.sh | bash -s -- --target all

set -euo pipefail

SKILL_NAME="ashiba-keisan"
TARGET="agents"
REPO="RingLord3812/ashiba-keisan"
BRANCH="main"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target|-t) TARGET="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--target agents|antigravity|claude|codex|cursor|gemini|copilot|windsurf|project|all]"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
LOCAL_SRC="$SCRIPT_DIR/skills/$SKILL_NAME"
TMP_DIR=""

cleanup() {
  if [[ -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

if [[ -f "$LOCAL_SRC/SKILL.md" ]]; then
  SRC_DIR="$LOCAL_SRC"
  echo "[ashiba-keisan] Using local skill source: $SRC_DIR"
else
  TMP_DIR="$(mktemp -d)"
  TAR_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"
  echo "[ashiba-keisan] Downloading $TAR_URL ..."
  curl -fsSL "$TAR_URL" | tar -xz -C "$TMP_DIR"
  EXTRACTED="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  SRC_DIR="$EXTRACTED/skills/$SKILL_NAME"
  if [[ ! -f "$SRC_DIR/SKILL.md" ]]; then
    echo "Error: SKILL.md not found in archive." >&2
    exit 1
  fi
fi

target_path() {
  case "$1" in
    agents)      echo "$HOME/.agents/skills/$SKILL_NAME" ;;
    antigravity) echo "$HOME/.gemini/config/skills/$SKILL_NAME" ;;
    claude)      echo "$HOME/.claude/skills/$SKILL_NAME" ;;
    codex)       echo "$HOME/.codex/skills/$SKILL_NAME" ;;
    cursor)      echo "$HOME/.cursor/skills/$SKILL_NAME" ;;
    gemini)      echo "$HOME/.gemini/skills/$SKILL_NAME" ;;
    copilot)     echo "$HOME/.copilot/skills/$SKILL_NAME" ;;
    windsurf)    echo "$HOME/.codeium/windsurf/skills/$SKILL_NAME" ;;
    project)     echo "$(pwd)/.agents/skills/$SKILL_NAME" ;;
    *) echo "Unsupported target: $1" >&2; exit 1 ;;
  esac
}

if [[ "$TARGET" == "all" ]]; then
  TARGETS=(agents antigravity claude codex cursor gemini copilot windsurf)
else
  TARGETS=("$TARGET")
fi

for t in "${TARGETS[@]}"; do
  DEST="$(target_path "$t")"
  mkdir -p "$(dirname "$DEST")"
  rm -rf "$DEST"
  cp -R "$SRC_DIR" "$DEST"
  find "$DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  echo "[OK] Installed ($t) -> $DEST"
done

FIRST_DEST="$(target_path "${TARGETS[0]}")"
echo ""
echo "Done! Verify with:"
echo "  python3 -m unittest discover -s \"$FIRST_DEST/tests\" -v"
