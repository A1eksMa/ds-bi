import json

from src.output import render, render_csv, render_json, render_table


_HEADERS = ["id", "name"]
_ROWS = [(1, "alice"), (2, None)]


def test_render_table_basic_shape():
    text = render_table(_HEADERS, _ROWS)
    lines = text.splitlines()
    assert lines[0] == lines[2] == lines[-1]  # верхняя/разделительная/нижняя рамки совпадают
    assert "id" in lines[1] and "name" in lines[1]
    assert "alice" in text


def test_render_table_empty_rows_message():
    assert render_table(_HEADERS, []) == "\n[ Запрос не вернул строк ]"


def test_render_json_roundtrip():
    text = render_json(_HEADERS, _ROWS)
    docs = json.loads(text)
    assert docs == [{"id": 1, "name": "alice"}, {"id": 2, "name": None}]


def test_render_json_non_ascii_not_escaped():
    text = render_json(["name"], [("Алиса",)])
    assert "Алиса" in text  # ensure_ascii=False


def test_render_csv_header_and_null_as_empty_cell():
    text = render_csv(_HEADERS, _ROWS)
    lines = text.splitlines()
    assert lines[0] == "id,name"
    assert lines[1] == "1,alice"
    assert lines[2] == "2,"  # None -> пустая ячейка, не строка "None"


def test_render_dispatches_by_format():
    assert render("csv", _HEADERS, _ROWS) == render_csv(_HEADERS, _ROWS)
    assert render("json", _HEADERS, _ROWS) == render_json(_HEADERS, _ROWS)
    assert render("table", _HEADERS, _ROWS) == render_table(_HEADERS, _ROWS)
