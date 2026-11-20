#!/usr/bin/env bash
# Install pos-agent-kit into an Odoo project.
#
# Only writes <project>/AGENTS.md (never overwrites an existing one). Skills are
# read in place from community/skills/ and pos-agent-kit/skills/: nothing is
# copied or linked into .agents/, .claude/ or .codex/.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT=""
HANDLE=""
WORKTREE_ROOT=""
LINK_SKILLS=0
SKILLS_DIR="$HOME/.claude/skills"

usage() {
    cat <<EOF
Usage: $0 [options]

  --project DIR        project root (default: parent of the kit, $(dirname "$KIT_DIR"))
  --handle HANDLE      Odoo handle used in branch names (default: from your
                       @odoo.com git email, else asked)
  --worktree-root DIR  where new worktrees go (default: <project>/../odoo-git-worktrees)
  --skills             also link kit and community skills into SKILLS_DIR so
                       they work as /skill-name commands (nothing is copied)
  --skills-dir DIR     user-level skills folder (default: ~/.claude/skills)
  -h, --help
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --project) PROJECT="$2"; shift 2 ;;
        --handle) HANDLE="$2"; shift 2 ;;
        --worktree-root) WORKTREE_ROOT="$2"; shift 2 ;;
        --skills) LINK_SKILLS=1; shift ;;
        --skills-dir) SKILLS_DIR="$2"; LINK_SKILLS=1; shift 2 ;;
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

# Optional: expose skills as /commands through user-level symlinks. The
# project itself gets no .agents/ or .claude/ directory.
if [ "$LINK_SKILLS" = 1 ]; then
    mkdir -p "$SKILLS_DIR"
    for d in "$PROJECT"/community/skills/*/ "$KIT_DIR"/skills/*/; do
        [ -f "$d/SKILL.md" ] || continue
        name="$(basename "$d")"
        lnk="$SKILLS_DIR/$name"
        if [ -e "$lnk" ] && [ ! -L "$lnk" ]; then
            echo "!! $lnk is a real directory, skipped; move it away to link $name." >&2
            continue
        fi
        ln -sfn "${d%/}" "$lnk"
        echo "Linked /$name -> ${d%/}"
    done
    for lnk in "$SKILLS_DIR"/*; do   # drop links left dangling by removed skills
        if [ -L "$lnk" ] && [ ! -e "$lnk" ]; then
            rm "$lnk"; echo "Removed dangling $lnk"
        fi
    done
fi

if [ -e "$PROJECT/AGENTS.md" ]; then
    echo "$PROJECT/AGENTS.md exists, left untouched. Merge $KIT_DIR/AGENTS.template.md into it by hand."
    exit 0
fi
# Odoo handle: the local part of an @odoo.com git email, else ask.
if [ -z "$HANDLE" ]; then
    email="$(git -C "$PROJECT/community" config user.email 2>/dev/null || true)"
    case "$email" in *@odoo.com) HANDLE="${email%@odoo.com}" ;; esac
fi
if [ -z "$HANDLE" ] && [ -t 0 ]; then
    read -r -p "Your Odoo handle (used in branch names, e.g. abcd): " HANDLE
fi
if [ -z "$HANDLE" ]; then
    HANDLE="<odoo_handle>"
    echo "!! No Odoo handle found; set odoo_handle in AGENTS.md by hand." >&2
fi
sed -e "s#<project_root_value>#$PROJECT#" \
    -e "s#<worktree_root_value>#$WORKTREE_ROOT#" \
    -e "s#<odoo_handle_value>#$HANDLE#" \
    "$KIT_DIR/AGENTS.template.md" > "$PROJECT/AGENTS.md"
echo "Wrote $PROJECT/AGENTS.md (handle: $HANDLE, worktrees: $WORKTREE_ROOT)."
echo "Restart your agent session to use it."
