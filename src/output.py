from __future__ import annotations

import csv
import io
import json
from typing import Sequence

_NO_ROWS = "\n[ Запрос не вернул строк ]"


def render_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Тот же ASCII-рендер таблицы, что был в исходном прототипе."""
    if not rows:
        return _NO_ROWS

    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    lines = [
        sep,
        "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths)) + " |",
        sep,
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(c).ljust(w) for c, w in zip(row, col_widths)) + " |")
    lines.append(sep)
    return "\n".join(lines)


def render_json(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """Список объектов {колонка: значение}. default=str -- на случай BLOB (bytes),
    которых в схеме ds нет, но на всякий случай не должны ронять экспорт."""
    docs = [dict(zip(headers, row)) for row in rows]
    return json.dumps(docs, ensure_ascii=False, indent=2, default=str)


def render_csv(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    """NULL -> пустая ячейка (не строка 'None', как сделал бы csv.writer по умолчанию)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow("" if cell is None else cell for cell in row)
    return buf.getvalue()


_RENDERERS = {"table": render_table, "json": render_json, "csv": render_csv}

FORMATS = tuple(_RENDERERS)


def render(fmt: str, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return _RENDERERS[fmt](headers, rows)
