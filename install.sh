#!/bin/sh
# Token Saver Meta — curl | sh install script
# Usage: curl -fsSL https://raw.githubusercontent.com/Im-Busy/token-saver-meta/main/install.sh | sh
set -eu

VERSION="${VERSION:-}"
INSTALL_DIR="${INSTALL_DIR:-}"

# ── helpers ──────────────────────────────────────────────
abort() { printf "ERROR: %s\n" "$*" >&2; exit 1; }
info()  { printf "  → %s\n" "$*"; }
ok()    { printf "  ✓ %s\n" "$*"; }

need_cmd() { command -v "$1" >/dev/null 2>&1 || abort "Missing $1. Install it first."; }

# ── detection ────────────────────────────────────────────
detect_installer() {
    if need_cmd node >/dev/null 2>&1 && need_cmd npx >/dev/null 2>&1; then
        INSTALLER="npm"
        if [ -n "$VERSION" ]; then
            RUN_CMD="npx token-saver-meta@${VERSION}"
        else
            RUN_CMD="npx token-saver-meta@latest"
        fi
        return 0
    fi

    if need_cmd uv >/dev/null 2>&1 || need_cmd python3 >/dev/null 2>&1; then
        INSTALLER="uv"
        if [ -n "$VERSION" ]; then
            RUN_CMD="uvx token-saver-meta==${VERSION}"
        else
            RUN_CMD="uvx token-saver-meta"
        fi
        return 0
    fi

    abort "Neither npm/npx nor uv/python found. Install Node.js (https://nodejs.org) or uv (https://docs.astral.sh/uv)."
}

# ── main ─────────────────────────────────────────────────
main() {
    case "${1:-}" in
        --help|-h)
            cat <<EOF
Token Saver Meta — zero-config token-saving toolkit installer.

Usage: curl -fsSL https://raw.githubusercontent.com/Im-Busy/token-saver-meta/main/install.sh | sh

Environment:
  VERSION      Pin to a specific version (e.g. VERSION=0.1.0)
  INSTALL_DIR  Target directory (default: current directory)

Examples:
  curl -fsSL https://raw.githubusercontent.com/Im-Busy/token-saver-meta/main/install.sh | sh
  VERSION=0.1.0 sh install.sh
EOF
            exit 0
            ;;
    esac

    printf "\nToken Saver Meta — installer\n"
    printf "─────────────────────────────\n"

    detect_installer
    info "Detected $INSTALLER runtime"

    if [ -n "$INSTALL_DIR" ]; then
        info "Installing to: $INSTALL_DIR"
        mkdir -p "$INSTALL_DIR"
        cd "$INSTALL_DIR" || abort "Cannot enter $INSTALL_DIR"
    fi

    info "Running: $RUN_CMD"
    printf "\n"
    eval "$RUN_CMD"
    printf "\n"
    ok "Token Saver Meta installed successfully"

    printf "\nNext steps:\n"
    printf "  Your AGENTS.md now has the token-saving protocol injected.\n"
    printf "  Restart your AI coding agent to apply.\n\n"
}

main "$@"
