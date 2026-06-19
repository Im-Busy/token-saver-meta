"""AGENTS.md injection for token-saver protocol."""

from pathlib import Path
from datetime import datetime
import shutil

START_MARKER = "<!-- TOKEN_SAVER_START -->"
END_MARKER = "<!-- TOKEN_SAVER_END -->"


def _get_template() -> str:
    """Read the injection template from templates/."""
    template_path = Path(__file__).resolve().parent.parent / "templates" / "agents_md_section.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return ""


def _backup_file(filepath: Path) -> str | None:
    """Create .bak-YYYYMMDD-HHMMSS backup before modifying."""
    if not filepath.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = filepath.with_name(f"{filepath.name}.bak-{timestamp}")
    shutil.copy2(str(filepath), str(bak))
    return str(bak)


def is_injected(filepath: Path) -> bool:
    """Check if TOKEN_SAVER markers already exist in file."""
    if not filepath.exists():
        return False
    content = filepath.read_text(encoding="utf-8")
    return START_MARKER in content and END_MARKER in content


def remove_injected_section(filepath: Path) -> dict:
    """Remove TOKEN_SAVER section from file, restoring pre-injection state."""
    if not filepath.exists():
        return {"status": "skip", "reason": "file not found"}
    if not is_injected(filepath):
        return {"status": "skip", "reason": "no token-saver section found"}

    backup = _backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    start_idx = content.index(START_MARKER)
    end_idx = content.index(END_MARKER) + len(END_MARKER)

    # Remove the section plus any trailing whitespace/newlines
    new_content = content[:start_idx] + content[end_idx:]
    # Clean up: remove blank lines left behind
    while new_content.endswith("\n\n"):
        new_content = new_content[:-1]

    filepath.write_text(new_content, encoding="utf-8")
    return {"status": "removed", "backup": backup}


def inject_agents_md_section(project_path: Path, platforms: list[str]) -> dict:
    """Inject token-saver protocol into AGENTS.md for detected platforms."""
    from src.config_gen import detect_platform_instructions_file

    result = {}
    template = _get_template()

    for platform_id in platforms:
        instr_file = detect_platform_instructions_file(platform_id)
        if instr_file is None:
            result[platform_id] = {"status": "skip", "reason": "no instructions file"}
            continue

        target = project_path / instr_file if not instr_file.is_absolute() else instr_file

        if not target.exists():
            # File doesn't exist — create it with template
            backup = _backup_file(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(template, encoding="utf-8")
            result[platform_id] = {"status": "created", "backup": backup}
        else:
            content = target.read_text(encoding="utf-8")
            if START_MARKER in content and END_MARKER in content:
                # Markers exist — replace between them (idempotent)
                backup = _backup_file(target)
                start_idx = content.index(START_MARKER)
                end_idx = content.index(END_MARKER) + len(END_MARKER)
                existing_block = content[start_idx:end_idx]
                if existing_block.rstrip() == template.rstrip():
                    result[platform_id] = {"status": "unchanged"}
                else:
                    new_content = content[:start_idx] + template + content[end_idx:]
                    target.write_text(new_content, encoding="utf-8")
                    result[platform_id] = {"status": "updated", "backup": backup}
            elif START_MARKER not in content:
                # File exists without markers — append at end
                backup = _backup_file(target)
                with open(str(target), "a", encoding="utf-8") as f:
                    f.write("\n\n" + template)
                result[platform_id] = {"status": "appended", "backup": backup}
            else:
                result[platform_id] = {"status": "warn", "message": "Found start marker but no end marker"}

    return result