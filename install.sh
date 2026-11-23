#!/usr/bin/env bash
# Install pos-agent-kit into an Odoo project.
#
# 1. Optionally links skills into ~/.claude/skills (--skills) for /commands.
# 2. Writes <project>/AGENTS.md (never overwrites an existing one).
# 3. Asks whether to set up niche-review (GitHub token, fetch review comments).
# Skills are read in place from community/skills/ and pos-agent-kit/skills/;
# the project gets no .agents/, .claude/ or .codex/ directory.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT=""
HANDLE=""
WORKTREE_ROOT=""
LINK_SKILLS=0
NICHE=""   # "" = ask, 1 = yes, 0 = no
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
  --niche / --no-niche set up niche-review (asks for a GitHub token and fetches
                       your PR review comments) without / instead of asking
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
        --niche) NICHE=1; shift ;;
        --no-niche) NICHE=0; shift ;;
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

write_agents_md() {
    if [ -e "$PROJECT/AGENTS.md" ]; then
        echo "$PROJECT/AGENTS.md exists, left untouched. Merge $KIT_DIR/AGENTS.template.md into it by hand."
        return
    fi
    # Odoo handle: the local part of an @odoo.com git email, else ask.
    if [ -z "$HANDLE" ]; then
        local email
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
}

# niche-review: fetch the user's PR review comments from GitHub. Interactive
# only; the token is read hidden and never passed on a command line.
setup_niche_review() {
    [ "$NICHE" = 0 ] && return
    if [ ! -t 0 ]; then
        [ "$NICHE" = 1 ] && echo "!! --niche needs an interactive terminal; skipped." >&2
        return
    fi
    local answer token="" env_file="$PROJECT/.env"
    if [ "$NICHE" != 1 ]; then
        echo
        read -r -p "Set up niche-review and fetch your PR review comments from GitHub? [y/N] " answer
        case "$answer" in [yY]|[yY][eE][sS]) ;; *) echo "Skipped niche-review setup."; return ;; esac
    fi

    if [ -f "$env_file" ] && grep -Eq '^\s*(export\s+)?GITHUB_TOKEN\s*=\s*\S' "$env_file"; then
        read -r -p "Use the GITHUB_TOKEN already in $env_file? [Y/n] " answer
        case "$answer" in [nN]|[nN][oO]) ;; *) token="__from_env_file__" ;; esac
    fi
    if [ -z "$token" ]; then
        echo "A GitHub token with read access to pull requests is needed"
        echo "(fine-grained: 'Pull requests: Read' on odoo/odoo, odoo/enterprise, odoo/upgrade; classic: 'repo')."
        read -r -s -p "GitHub token (input hidden): " token; echo
        if [ -z "$token" ]; then echo "No token given; skipped niche-review setup."; return; fi
        read -r -p "Save it to $env_file for later syncs? [Y/n] " answer
        case "$answer" in
            [nN]|[nN][oO]) ;;
            *)
                touch "$env_file"; chmod 600 "$env_file"
                local tmp; tmp="$(mktemp)"
                grep -Ev '^\s*(export\s+)?GITHUB_TOKEN\s*=' "$env_file" > "$tmp" || true
                printf 'GITHUB_TOKEN=%s\n' "$token" >> "$tmp"
                cat "$tmp" > "$env_file"; rm -f "$tmp"
                echo "Saved to $env_file (mode 600)." ;;
        esac
    fi

    echo "Fetching your review comments (the first run can take a few minutes)..."
    local fetch="$KIT_DIR/scripts/pr_review_comments/fetch_pr_comments.py"
    if [ "$token" = "__from_env_file__" ]; then
        python3 "$fetch" || { echo "!! Fetch failed; re-run: python3 $fetch" >&2; return; }
    else
        GITHUB_TOKEN="$token" python3 "$fetch" || { echo "!! Fetch failed; re-run: python3 $fetch" >&2; return; }
    fi
    echo "niche-review is ready. Later, refresh with: python3 $fetch"
}

write_agents_md
setup_niche_review
echo "Restart your agent session to use the kit."
