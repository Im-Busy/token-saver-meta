"""RTK installer — binary download strategy with fallbacks, version check, and hook init."""

from pathlib import Path
import platform
import subprocess
import shutil


def _run_rtk_version() -> str | None:
    """Run `rtk --version` and return cleaned version string, or None on failure."""
    try:
        ver = subprocess.run(
            ["rtk", "--version"], capture_output=True, text=True, timeout=10
        )
        raw = (ver.stdout.strip() or ver.stderr.strip())
        # Strip "rtk " prefix if present (e.g. "rtk 1.2.3" → "1.2.3")
        if raw.lower().startswith("rtk "):
            raw = raw[4:]
        return raw if raw else None
    except Exception:
        return None


def init_rtk_hook() -> dict:
    """Run `rtk init -g` to inject the PreToolUse hook into agent configs.

    Returns:
        dict with keys: status ("ok"|"skip"|"warn"), message
    """
    try:
        result = subprocess.run(
            ["rtk", "init", "-g"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return {"status": "ok", "message": "PreToolUse hook injected via rtk init -g"}
        else:
            return {
                "status": "warn",
                "message": f"rtk init -g returned non-zero: {result.stderr.strip()[:200]}",
            }
    except FileNotFoundError:
        return {"status": "skip", "message": "rtk binary not found — cannot init hook"}
    except Exception as exc:
        return {"status": "warn", "message": f"rtk init -g failed: {exc}"}


def install_rtk(project_path: Path, platforms: list[str] | None = None) -> dict:
    """Install RTK CLI output compressor. Falls back through brew, curl, cargo.

    Args:
        project_path: Path to the target project directory (for context, not used directly).
        platforms: Optional list of platform identifiers to configure RTK for.

    Returns:
        dict with keys: status, version, install_method, hook_status, message.
            status: "ok" | "warn" | "skip" | "error"
            version: version string or None
            install_method: "brew" | "cargo" | "curl" | "pre-installed" | None
            hook_status: "ok" | "skip" | "warn"
            message: human-readable explanation when status != "ok"
    """
    os_name = platform.system()

    # ---- Already installed? ----
    existing = shutil.which("rtk")
    if existing:
        ver_str = _run_rtk_version()
        if ver_str:
            # Working install — init hook
            hook = init_rtk_hook()
            return {
                "status": "ok",
                "version": ver_str,
                "install_method": "pre-installed",
                "hook_status": hook["status"],
                "message": "",
            }
        # rtk binary found but --version failed — warn and stop
        return {
            "status": "warn",
            "version": None,
            "install_method": None,
            "hook_status": "skip",
            "message": (
                "rtk found on PATH but 'rtk --version' failed. "
                "The installation may be corrupted. Reinstall with: "
                "cargo install --git https://github.com/rtk-ai/rtk"
            ),
        }

    # ---- macOS: brew → curl ----
    if os_name == "Darwin":
        if shutil.which("brew"):
            try:
                subprocess.run(
                    ["brew", "install", "rtk"],
                    check=True, capture_output=True, text=True, timeout=120,
                )
                ver_str = _run_rtk_version()
                hook = init_rtk_hook()
                return {
                    "status": "ok",
                    "version": ver_str,
                    "install_method": "brew",
                    "hook_status": hook["status"],
                    "message": "",
                }
            except Exception:
                pass

        try:
            subprocess.run(
                "curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh",
                shell=True, check=True, capture_output=True, text=True, timeout=120,
            )
            ver_str = _run_rtk_version()
            hook = init_rtk_hook()
            return {
                "status": "ok",
                "version": ver_str,
                "install_method": "curl",
                "hook_status": hook["status"],
                "message": "",
            }
        except Exception:
            pass

    # ---- Linux: curl ----
    elif os_name == "Linux":
        try:
            subprocess.run(
                "curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh",
                shell=True, check=True, capture_output=True, text=True, timeout=120,
            )
            ver_str = _run_rtk_version()
            hook = init_rtk_hook()
            return {
                "status": "ok",
                "version": ver_str,
                "install_method": "curl",
                "hook_status": hook["status"],
                "message": "",
            }
        except Exception:
            pass

    # ---- Windows or fallback: cargo ----
    if shutil.which("cargo"):
        try:
            subprocess.run(
                ["cargo", "install", "--git", "https://github.com/rtk-ai/rtk"],
                check=True, capture_output=True, text=True, timeout=300,
            )
            ver_str = _run_rtk_version()
            hook = init_rtk_hook()
            return {
                "status": "ok",
                "version": ver_str,
                "install_method": "cargo",
                "hook_status": hook["status"],
                "message": "",
            }
        except Exception:
            return {
                "status": "skip",
                "version": None,
                "install_method": None,
                "hook_status": "skip",
                "message": (
                    "RTK not installable via cargo. "
                    "Install Rust (https://rustup.rs) then run: "
                    "cargo install --git https://github.com/rtk-ai/rtk "
                    "or download a prebuilt binary from: "
                    "https://github.com/rtk-ai/rtk/releases"
                ),
            }

    # ---- All paths exhausted ----
    return {
        "status": "skip",
        "version": None,
        "install_method": None,
        "hook_status": "skip",
        "message": (
            "RTK not installable. No package manager (brew, curl, cargo) found. "
            "Install Rust with: https://rustup.rs "
            "Then: cargo install --git https://github.com/rtk-ai/rtk "
            "Or download a prebuilt binary from: "
            "https://github.com/rtk-ai/rtk/releases"
        ),
    }
