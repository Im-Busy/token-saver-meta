"""DB output compression — truncate wide columns, limit rows, format tables."""

from __future__ import annotations


def truncate_columns(rows: list[list[str]], max_width: int = 30) -> list[list[str]]:
    """Truncate cell values longer than *max_width*, appending "...".

    Args:
        rows: Table data as a list of rows (each row is a list of column strings).
        max_width: Maximum character width per cell.

    Returns:
        New list of rows with truncated cell values.
    """
    result: list[list[str]] = []
    for row in rows:
        truncated: list[str] = []
        for cell in row:
            s = str(cell)
            if len(s) > max_width:
                truncated.append(s[: max_width - 3] + "...")
            else:
                truncated.append(s)
        result.append(truncated)
    return result


def limit_rows(rows: list[list[str]], max_rows: int = 10) -> list[list[str]]:
    """Keep at most *max_rows* rows, adding a summary row for the remainder.

    Args:
        rows: Table data (header NOT included — only data rows).
        max_rows: Maximum number of data rows to return.

    Returns:
        Shortened row list. If rows were dropped the last entry is a
        single-element row like ``["... and 42 more rows"]``.
    """
    if len(rows) <= max_rows:
        return [list(row) for row in rows]

    remaining = len(rows) - max_rows
    result = [list(row) for row in rows[:max_rows]]
    result.append([f"... and {remaining} more rows"])
    return result


def format_table(
    headers: list[str],
    rows: list[list[str]],
    max_rows: int = 10,
    max_cols: int = 20,
) -> str:
    """Format a table as an aligned plain-text string.

    Columns are padded to the width of the widest cell in that column.
    Excess columns beyond *max_cols* are dropped with a ``...`` marker.

    Args:
        headers: Column header strings.
        rows: Data rows (each row is a list of column strings).
        max_rows: Maximum data rows to include (see :func:`limit_rows`).
        max_cols: Maximum columns to include.

    Returns:
        Formatted table string with aligned columns.
    """
    # Truncate columns.
    original_cols = len(headers)
    col_count = min(original_cols, max_cols)
    headers = list(headers[:col_count])
    rows = [list(row[:col_count]) for row in rows]
    if original_cols > max_cols:
        headers.append("...")
        for row in rows:
            row.append("...")

    # Limit rows.
    rows = limit_rows(rows, max_rows)

    # Compute column widths.
    all_rows = [headers, *rows]
    col_widths: list[int] = []
    for ci in range(len(headers)):
        width = max((len(str(r[ci])) if ci < len(r) else 0) for r in all_rows)
        col_widths.append(width)

    def _format_row(row: list[str]) -> str:
        parts: list[str] = []
        for ci, cell in enumerate(row[: len(col_widths)]):
            parts.append(str(cell).ljust(col_widths[ci]))
        return "  ".join(parts)

    lines = [_format_row(headers)]
    lines.extend(_format_row(r) for r in rows)
    return "\n".join(lines)
