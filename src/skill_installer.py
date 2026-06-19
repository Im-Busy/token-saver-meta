"""Skill tools installer (caveman, LG-token-saver, kevin-copilot)."""

from pathlib import Path
import shutil


SKILL_SOURCES = [
    {
        "name": "caveman",
        "sources": [Path("useful-repos/caveman/skills/caveman/SKILL.md")],
        "dest_dir": "caveman",
    },
    {
        "name": "lg-token-saver",
        "sources": [Path("useful-repos/LG-token-saver/SKILL.md")],
        "dest_dir": "lg-token-saver",
    },
    {
        "name": "kevin-copilot",
        "sources": [
            Path("useful-repos/kevin-copilot/.github/copilot-instructions.md"),
            Path("useful-repos/kevin-copilot/.github/skills/unslop/SKILL.md"),
        ],
        "dest_dir": "kevin-copilot",
    },
]


def install_skill_tools(project_path: Path, platforms: list[str]) -> dict:
    """Copy SKILL.md files to platform-specific skills directories.

    Args:
        project_path: Root path of the user's project.
        platforms: List of platform IDs (e.g. ['kilo', 'claude-code']).

    Returns:
        Dict mapping skill name to install result per platform.
    """
    from src.config_gen import detect_platform_skills_dir

    result = {}
    project_root = project_path.resolve()

    for skill_cfg in SKILL_SOURCES:
        name = skill_cfg["name"]
        result[name] = {"status": "ok", "platforms": {}}

        for platform_id in platforms:
            skills_dir = detect_platform_skills_dir(platform_id)
            if not skills_dir:
                result[name]["platforms"][platform_id] = {
                    "status": "skip",
                    "reason": "no skills dir",
                }
                continue

            # Build destination: {skills_dir}/token-saver/{name}/
            dest = project_root / skills_dir / "token-saver" / skill_cfg["dest_dir"]
            dest.mkdir(parents=True, exist_ok=True)

            installed_files = []
            had_warn = False
            for src_rel in skill_cfg["sources"]:
                src = project_root / src_rel
                if src.exists():
                    dest_file = dest / src.name
                    shutil.copy2(str(src), str(dest_file))
                    installed_files.append(str(dest_file))
                else:
                    had_warn = True
                    result[name]["platforms"][platform_id] = {
                        "status": "warn",
                        "message": f"Source not found: {src}",
                    }

            if not had_warn:
                result[name]["platforms"][platform_id] = {
                    "status": "ok",
                    "files": installed_files,
                }

    return result