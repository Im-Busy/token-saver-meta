"""MCP server installer for GitNexus and CGC."""

from pathlib import Path
import subprocess
import shutil


def install_mcp_servers(project_path: Path, platforms: list[str], cgc_path: str | None = None) -> dict:
    """Install MCP servers (GitNexus + CGC) for all detected platforms."""
    from src.config_gen import load_matrix, generate_server_entry, write_mcp_config

    result = {"gitnexus": {"status": "ok", "platforms": {}}, "cgc": {"status": "ok", "platforms": {}}}
    matrix = load_matrix()
    mcp_servers = matrix.get("mcp_servers", {})

    # GitNexus: just generate config (npx auto-fetches on use)
    if "gitnexus_server" in mcp_servers:
        gn_def = mcp_servers["gitnexus_server"]
        for platform_id in platforms:
            try:
                pdef = matrix["platforms"].get(platform_id)
                if not pdef:
                    continue
                family = pdef["mcp_family"]
                generate_server_entry("gitnexus", gn_def, family)
                status, msg = write_mcp_config(platform_id, project_path)
                result["gitnexus"]["platforms"][platform_id] = {"status": status, "message": msg}
            except Exception as e:
                result["gitnexus"]["platforms"][platform_id] = {"status": "warn", "message": str(e)}
    else:
        result["gitnexus"]["status"] = "warn"
        result["gitnexus"]["message"] = "gitnexus_server not in matrix"

    # CGC: attempt install via uv
    if "codegraphcontext_server" in mcp_servers:
        cgc_def = mcp_servers["codegraphcontext_server"]
        
        # Check if cgc is available
        try:
            if shutil.which("cgc"):
                subprocess.run(["cgc", "--version"], capture_output=True, text=True, timeout=10)
            elif shutil.which("uv"):
                subprocess.run(["uv", "run", "cgc", "--version"], capture_output=True, text=True, timeout=10)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # CGC not installed - try installing
            if shutil.which("uv"):
                try:
                    subprocess.run(
                        ["uv", "pip", "install", "codegraphcontext"],
                        capture_output=True, text=True, timeout=120,
                    )
                except subprocess.TimeoutExpired:
                    result["cgc"]["status"] = "warn"
                    result["cgc"]["message"] = "CGC install timed out"
            else:
                result["cgc"]["status"] = "warn"
                result["cgc"]["message"] = "uv not available, cannot install CGC"

        # Generate CGC configs for each platform
        for platform_id in platforms:
            try:
                pdef = matrix["platforms"].get(platform_id)
                if not pdef:
                    continue
                family = pdef["mcp_family"]
                generate_server_entry("codegraphcontext", cgc_def, family)
                status, msg = write_mcp_config(platform_id, project_path, cgc_path)
                result["cgc"]["platforms"][platform_id] = {"status": status, "message": msg}
            except Exception as e:
                result["cgc"]["platforms"][platform_id] = {"status": "warn", "message": str(e)}
    else:
        result["cgc"]["status"] = "warn"
        result["cgc"]["message"] = "codegraphcontext_server not in matrix"

    return result
