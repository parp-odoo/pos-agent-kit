#!/usr/bin/env bash
# Install pos-agent-kit into an Odoo project.
#
# Only writes <project>/AGENTS.md (never overwrites an existing one). Skills are
# read in place from community/skills/ and pos-agent-kit/skills/: nothing is
# copied or linked into .agents/, .claude/ or .codex/.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT=""
HANDLE="<odoo_handle>"
WORKTREE_ROOT=""

usage() {
    cat <<EOF
Usage: $0 [options]

  --project DIR        project root (default: parent of the kit, $(dirname "$KIT_DIR"))
  --handle HANDLE      Odoo handle used in branch names (e.g. abcd)
  --worktree-root DIR  where new worktrees go (default: <project>/../odoo-git-worktrees)
  -h, --help
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --project) PROJECT="$2"; shift 2 ;;
        --handle) HANDLE="$2"; shift 2 ;;
        --worktree-root) WORKTREE_ROOT="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

PROJECT="$(cd "${PROJECT:-$(dirname "$KIT_DIR")}" && pwd)"
WORKTREE_ROOT="${WORKTREE_ROOT:-$(dirname "$PROJECT")/odoo-git-worktrees}"

if [ "$(dirname "$KIT_DIR")" != "$PROJECT" ] || [ "$(basename "$KIT_DIR")" != "pos-agent-kit" ]; then
    echo "!! The kit must be at $PROJECT/pos-agent-kit (links depend on it)." >&2
    exit 1
fi
if [ ! -f "$PROJECT/community/skills/odoo-guidelines/SKILL.md" ]; then
    echo "!! $PROJECT/community/skills/ not found or incomplete." >&2
    echo "   Check out a community branch that ships skills/ (master or a recent version)." >&2
    exit 1
fi

if [ -e "$PROJECT/AGENTS.md" ]; then
    echo "$PROJECT/AGENTS.md exists, left untouched. Merge $KIT_DIR/AGENTS.template.md into it by hand."
    exit 0
fi
sed -e "s#<project_root_value>#$PROJECT#" \
    -e "s#<worktree_root_value>#$WORKTREE_ROOT#" \
    -e "s#<odoo_handle_value>#$HANDLE#" \
    "$KIT_DIR/AGENTS.template.md" > "$PROJECT/AGENTS.md"
echo "Wrote $PROJECT/AGENTS.md; review its Settings section, then restart your agent session."
