"""CBM (codebase-memory-mcp) binary download and validation installer."""
import subprocess
import platform
import tempfile
import hashlib
import shutil
from pathlib import Path

CBM_RELEASE_URL = "https://github.com/DeusData/codebase-memory-mcp/releases/latest/download"
CBM_VERSION = "0.8.1"  # Confirmed by pre-flight (Task 0)

def detect_platform() -> str:
    """Detect current platform. Returns 'windows-amd64', 'linux-amd64', etc."""
    system = platform.system().lower()
    if system == "windows":
        return "windows-amd64"
    elif system == "linux":
        return "linux-amd64"  # arm64 detection possible but not for v1
    elif system == "darwin":
        return "darwin-arm64" if platform.machine() == "arm64" else "darwin-amd64"
    return "unknown"

def get_install_path() -> Path:
    """Get the installation path for CBM binary."""
    home = Path.home()
    return home / ".token-saver-meta" / "bin"

def get_cbm_db_path() -> Path:
    """Get the expected CBM database path."""
    home = Path.home()
    return home / ".cache" / "codebase-memory-mcp"

def install_cbm() -> dict:
    """Download and validate CBM binary. Returns structured result."""
    result = {"status": "ok", "binary_path": None, "version": None, "message": ""}
    
    try:
        import requests as _unused  # Check if requests is available
    except ImportError:
        result["status"] = "warn"
        result["message"] = "Python 'requests' not available for binary download"
        return result
    
    import requests
    
    plat = detect_platform()
    if plat == "unknown":
        return {"status": "error", "message": f"Unsupported platform: {platform.system()}"}
    
    install_path = get_install_path()
    install_path.mkdir(parents=True, exist_ok=True)
    
    binary_name = "cbm.exe" if plat.startswith("windows") else "cbm"
    binary_path = install_path / binary_name
    
    # Download URL - CBM releases are named like: codebase-memory-mcp-windows-amd64.zip
    archive_name = f"codebase-memory-mcp-{plat}"
    ext = ".zip" if plat.startswith("windows") else ".tar.gz"
    url = f"{CBM_RELEASE_URL}/{archive_name}{ext}"
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            archive_path = tmp / f"cbm{ext}"
            
            # Download
            import requests as _r
            response = _r.get(url, timeout=60, allow_redirects=True)
            if response.status_code != 200:
                result["status"] = "error"
                result["message"] = f"Download failed: HTTP {response.status_code}"
                return result
            
            archive_path.write_bytes(response.content)
            
            # Extract
            if ext == ".zip":
                import zipfile
                with zipfile.ZipFile(archive_path) as zf:
                    # Extract just the binary
                    for member in zf.namelist():
                        if member.endswith((".exe", ".tar.gz")) or "cbm" in member.lower():
                            continue
                    zf.extractall(tmp)
            else:
                import tarfile
                with tarfile.open(archive_path) as tf:
                    tf.extractall(tmp)
            
            # Find and copy binary
            extracted_binary = None
            for f in tmp.rglob(binary_name):
                extracted_binary = f
                break
            if not extracted_binary:
                for f in tmp.rglob("codebase-memory-mcp*"):
                    if not f.name.endswith((".tar.gz", ".zip")):
                        extracted_binary = f
                        break
            
            if not extracted_binary:
                result["status"] = "error"
                result["message"] = "Binary not found in archive"
                return result
            
            shutil.copy2(extracted_binary, binary_path)
            binary_path.chmod(0o755)
        
        # Verify binary runs
        try:
            ver = subprocess.run(
                [str(binary_path), "--version"],
                capture_output=True, text=True, timeout=10
            )
            result["version"] = ver.stdout.strip() or ver.stderr.strip()
        except Exception:
            result["version"] = "unknown"
        
        result["binary_path"] = str(binary_path)
        result["message"] = f"CBM {result.get('version', 'unknown')} installed"
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_cbm_config(agent_type: str) -> dict:
    """Generate MCP server config for CBM. Returns {status, config, message}."""
    result: dict = {"status": "ok", "config": None, "message": ""}

    binary_name = "cbm.exe" if platform.system() == "Windows" else "cbm"
    binary_path = get_install_path() / binary_name

    if not binary_path.exists():
        result["status"] = "warn"
        result["message"] = f"CBM binary not found at {binary_path}. Run install_cbm() first."
        return result

    binary_str = str(binary_path)

    supported = {"opencode", "claude"}
    if agent_type not in supported:
        result["status"] = "error"
        result["message"] = f"Unsupported agent: {agent_type}"
        return result

    result["config"] = {
        "mcpServers": {
            "codebase-memory-mcp": {
                "command": binary_str,
                "args": [],
            }
        }
    }

    return result
