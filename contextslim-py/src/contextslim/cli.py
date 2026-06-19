"""ContextSlim CLI — token-optimized command wrappers.

Usage:
    contextslim code cat src/auth.py
    contextslim search grep "TODO" .
    contextslim setup init
"""

from __future__ import annotations

import click

from contextslim import __version__


@click.group()
@click.version_option(version=__version__, prog_name="contextslim")
@click.option("--dir", "project_dir", default=".", help="Project root directory")
@click.pass_context
def cli(ctx: click.Context, project_dir: str) -> None:
    """Token-optimized CLI wrappers. 35 commands that replace verbose tool output."""
    ctx.ensure_object(dict)
    ctx.obj["project_dir"] = project_dir


# ── code group ──────────────────────────────────────────────

@cli.group("code")
def code_group() -> None:
    """Code file reading and analysis commands."""


@code_group.command("cat")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def cat_cmd(ctx: click.Context, file: str) -> None:
    """Read file with blank stripping and truncation."""
    from contextslim.commands.code.cat import cat_command
    from contextslim.config import load_config
    cfg = load_config()
    cat_command(file, cfg)


@code_group.command("head")
@click.argument("file", type=click.Path(exists=True))
@click.option("--lines", "-n", default=30, help="Number of lines to show")
@click.pass_context
def head_cmd(ctx: click.Context, file: str, lines: int) -> None:
    """Show first N lines with blank stripping."""
    from contextslim.commands.code.head import head_command
    from contextslim.config import load_config
    cfg = load_config()
    head_command(file, lines, cfg)


@code_group.command("map")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def map_cmd(ctx: click.Context, file: str) -> None:
    """Extract structural signatures only (functions, classes, exports)."""
    from contextslim.commands.code.map_cmd import map_command
    map_command(file)


@code_group.command("ls")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def ls_cmd(ctx: click.Context, directory: str) -> None:
    """List directory contents, hide heavy dirs."""
    from contextslim.commands.code.ls_cmd import ls_command
    from contextslim.config import load_config
    cfg = load_config()
    ls_command(directory, cfg)


@code_group.command("tree")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.option("--depth", "-d", default=3, help="Maximum tree depth")
@click.pass_context
def tree_cmd(ctx: click.Context, directory: str, depth: int) -> None:
    """Directory tree with depth cap, skip ignored dirs."""
    from contextslim.commands.code.tree_cmd import tree_command
    from contextslim.config import load_config
    cfg = load_config()
    tree_command(directory, depth, cfg)


@code_group.command("brief")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def brief_cmd(ctx: click.Context, directory: str) -> None:
    """~300-token project summary (stack, entry points, tree)."""
    from contextslim.commands.code.brief import brief_command
    brief_command(directory)


@code_group.command("outline")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def outline_cmd(ctx: click.Context, directory: str) -> None:
    """Recursive signature extraction from all source files."""
    from contextslim.commands.code.outline import outline_command
    from contextslim.config import load_config
    cfg = load_config()
    outline_command(directory, cfg)


@code_group.command("imports")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def imports_cmd(ctx: click.Context, file: str) -> None:
    """Extract only import/require statements."""
    from contextslim.commands.code.imports_cmd import imports_command
    imports_command(file)


@code_group.command("types")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def types_cmd(ctx: click.Context, file: str) -> None:
    """Extract only TypeScript interface/type/enum declarations."""
    from contextslim.commands.code.types_cmd import types_command
    types_command(file)


@code_group.command("deps")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def deps_cmd(ctx: click.Context, directory: str) -> None:
    """Compact dependency listing (no version numbers)."""
    from contextslim.commands.code.deps import deps_command
    deps_command(directory)


@code_group.command("config")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def config_cmd(ctx: click.Context, file: str) -> None:
    """Read config file, strip comments, redact secrets."""
    from contextslim.commands.code.config_cmd import config_command
    config_command(file)


@code_group.command("summary")
@click.argument("file", type=click.Path(exists=True))
@click.pass_context
def summary_cmd(ctx: click.Context, file: str) -> None:
    """Structured file stats (lines, imports, exports, functions)."""
    from contextslim.commands.code.summary_cmd import summary_command
    summary_command(file)


# ── search group ────────────────────────────────────────────

@cli.group("search")
def search_group() -> None:
    """File search and log analysis commands."""


@search_group.command("grep")
@click.argument("query")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def grep_cmd(ctx: click.Context, query: str, directory: str) -> None:
    """Search files, skip heavy dirs, cap results."""
    from contextslim.commands.search.grep import grep_command
    from contextslim.config import load_config
    cfg = load_config()
    grep_command(query, directory, cfg)


@search_group.command("findfiles")
@click.argument("pattern")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def findfiles_cmd(ctx: click.Context, pattern: str, directory: str) -> None:
    """Find files by glob pattern, cap results."""
    from contextslim.commands.search.findfiles import findfiles_command
    from contextslim.config import load_config
    cfg = load_config()
    findfiles_command(pattern, directory, cfg)


@search_group.command("todo")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def todo_cmd(ctx: click.Context, directory: str) -> None:
    """Find TODO/FIXME/HACK/BUG comments across project."""
    from contextslim.commands.search.todo import todo_command
    from contextslim.config import load_config
    cfg = load_config()
    todo_command(directory, cfg)


@search_group.command("errors")
@click.argument("file", type=click.Path(exists=True))
@click.option("--max-lines", "-n", default=50, help="Maximum lines to show")
@click.pass_context
def errors_cmd(ctx: click.Context, file: str, max_lines: int) -> None:
    """Extract only error/warning lines from log files."""
    from contextslim.commands.search.errors import errors_command
    errors_command(file, max_lines)


@search_group.command("logs")
@click.argument("file", type=click.Path(exists=True))
@click.option("--lines", "-n", default=100, help="Number of lines to tail")
@click.pass_context
def logs_cmd(ctx: click.Context, file: str, lines: int) -> None:
    """Last N lines of log, timestamps stripped."""
    from contextslim.commands.search.logs import logs_command
    logs_command(file, lines)


# ── git group ───────────────────────────────────────────────

@cli.group("git")
def git_group() -> None:
    """Git integration commands with token-optimized output."""


@git_group.command("diff")
@click.argument("target", default=None, required=False)
@click.argument("target2", default=None, required=False)
@click.pass_context
def diff_cmd(ctx: click.Context, target: str | None, target2: str | None) -> None:
    """Compact git diff or file diff (filtered of heavy dirs)."""
    from contextslim.commands.git.diff import diff_command
    diff_command(target, target2)


@git_group.command("changes")
@click.option("--count", "-n", default=10, help="Number of commits")
@click.pass_context
def changes_cmd(ctx: click.Context, count: int) -> None:
    """Compact git log — last N commits with changed files."""
    from contextslim.commands.git.changes import changes_command
    changes_command(count)


# ── system group ────────────────────────────────────────────

@cli.group("system")
def system_group() -> None:
    """System information commands."""


@system_group.command("sysinfo")
@click.pass_context
def sysinfo_cmd(ctx: click.Context) -> None:
    """Compact OS/hardware info."""
    from contextslim.commands.system.sysinfo import sysinfo_command
    sysinfo_command()


@system_group.command("procs")
@click.option("--filter", "name_filter", default=None, help="Filter by process name")
@click.option("--limit", "-n", default=30, help="Maximum processes to show")
@click.pass_context
def procs_cmd(ctx: click.Context, name_filter: str | None, limit: int) -> None:
    """Sorted process list by memory usage."""
    from contextslim.commands.system.procs import procs_command
    procs_command(name_filter, limit)


@system_group.command("services")
@click.option("--filter", "name_filter", default=None, help="Filter by service name")
@click.option("--limit", "-n", default=30, help="Maximum services to show")
@click.pass_context
def services_cmd(ctx: click.Context, name_filter: str | None, limit: int) -> None:
    """Service list grouped by status."""
    from contextslim.commands.system.services import services_command
    services_command(name_filter, limit)


@system_group.command("netinfo")
@click.pass_context
def netinfo_cmd(ctx: click.Context) -> None:
    """Network interfaces and listening ports."""
    from contextslim.commands.system.netinfo import netinfo_command
    netinfo_command()


@system_group.command("envinfo")
@click.option("--filter", "name_filter", default=None, help="Filter by variable name")
@click.pass_context
def envinfo_cmd(ctx: click.Context, name_filter: str | None) -> None:
    """Environment variables grouped by category, sensitive vars hidden."""
    from contextslim.commands.system.envinfo import envinfo_command
    envinfo_command(name_filter)


@system_group.command("ports")
@click.option("--filter", "name_filter", default=None, help="Filter by port or process")
@click.pass_context
def ports_cmd(ctx: click.Context, name_filter: str | None) -> None:
    """Open ports list from netstat/ss."""
    from contextslim.commands.system.ports import ports_command
    ports_command(name_filter)


@system_group.command("disk")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def disk_cmd(ctx: click.Context, directory: str) -> None:
    """Filesystem overview + top directory sizes."""
    from contextslim.commands.system.disk import disk_command
    disk_command(directory)


@system_group.command("docker")
@click.option("--filter", "name_filter", default=None, help="Filter by name")
@click.pass_context
def docker_cmd(ctx: click.Context, name_filter: str | None) -> None:
    """Containers + images + volumes overview."""
    from contextslim.commands.system.docker import docker_command
    docker_command(name_filter)


@system_group.command("packages")
@click.option("--filter", "name_filter", default=None, help="Filter by package name")
@click.pass_context
def packages_cmd(ctx: click.Context, name_filter: str | None) -> None:
    """Installed packages (platform-aware)."""
    from contextslim.commands.system.packages import packages_command
    packages_command(name_filter)


# ── db group ────────────────────────────────────────────────

@cli.group("db")
def db_group() -> None:
    """SQLite database inspection commands."""


@db_group.command("dbschema")
@click.argument("db_path", type=click.Path(exists=True))
@click.option("--filter", "name_filter", default=None, help="Filter by table name")
@click.pass_context
def dbschema_cmd(ctx: click.Context, db_path: str, name_filter: str | None) -> None:
    """Compact schema tree (tables, columns, indexes)."""
    from contextslim.commands.db.dbschema import dbschema_command
    dbschema_command(db_path, name_filter)


@db_group.command("dbquery")
@click.argument("sql_or_file")
@click.option("--db", "db_path", default=None, help="SQLite database path")
@click.pass_context
def dbquery_cmd(ctx: click.Context, sql_or_file: str, db_path: str | None) -> None:
    """Execute SQL query with truncated output."""
    from contextslim.commands.db.dbquery import dbquery_command
    dbquery_command(sql_or_file, db_path)


@db_group.command("dbsample")
@click.argument("table")
@click.option("--db", "db_path", default=None, help="SQLite database path")
@click.pass_context
def dbsample_cmd(ctx: click.Context, table: str, db_path: str | None) -> None:
    """Auto-generate SELECT * LIMIT N."""
    from contextslim.commands.db.dbsample import dbsample_command
    dbsample_command(table, db_path)


@db_group.command("dbstats")
@click.argument("db_path", type=click.Path(exists=True))
@click.option("--filter", "name_filter", default=None, help="Filter by table name")
@click.pass_context
def dbstats_cmd(ctx: click.Context, db_path: str, name_filter: str | None) -> None:
    """Table sizes, row counts, index stats."""
    from contextslim.commands.db.dbstats import dbstats_command
    dbstats_command(db_path, name_filter)


@db_group.command("dbdiff")
@click.argument("schema1", type=click.Path(exists=True))
@click.argument("schema2", type=click.Path(exists=True))
@click.pass_context
def dbdiff_cmd(ctx: click.Context, schema1: str, schema2: str) -> None:
    """Compare two schema dumps."""
    from contextslim.commands.db.dbdiff import dbdiff_command
    dbdiff_command(schema1, schema2)


# ── setup group ─────────────────────────────────────────────

@cli.group("setup")
def setup_group() -> None:
    """Project setup and health check commands."""


@setup_group.command("init")
@click.option("--ides", default="cursor,claude", help="Comma-separated IDE list")
@click.option("--force", is_flag=True, help="Overwrite existing config")
@click.pass_context
def init_cmd(ctx: click.Context, ides: str, force: bool) -> None:
    """Initialize project with ignore files + AI rules."""
    from contextslim.commands.setup.init_cmd import init_command
    init_command(ctx.obj["project_dir"], ides.split(","), force)


@setup_group.command("audit")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def audit_cmd(ctx: click.Context, directory: str) -> None:
    """Audit token waste and projected savings."""
    from contextslim.commands.setup.audit import audit_command
    from contextslim.config import load_config
    cfg = load_config()
    audit_command(directory, cfg)


@setup_group.command("doctor")
@click.argument("directory", type=click.Path(exists=True), default=".")
@click.pass_context
def doctor_cmd(ctx: click.Context, directory: str) -> None:
    """Check configuration health."""
    from contextslim.commands.setup.doctor import doctor_command
    doctor_command(directory)


if __name__ == "__main__":
    cli()
