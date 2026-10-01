import sqlite3

from src.db import run_query


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO t (id, name) VALUES (1, 'a'), (2, 'b')")
    conn.commit()
    conn.close()


def test_run_query_select_with_named_param(tmp_path):
    db = str(tmp_path / "d.db")
    _make_db(db)

    headers, rows = run_query(db, "SELECT id, name FROM t WHERE id = :id", {"id": 2})

    assert headers == ["id", "name"]
    assert rows == [(2, "b")]


def test_run_query_select_no_rows_still_has_headers(tmp_path):
    db = str(tmp_path / "d.db")
    _make_db(db)

    headers, rows = run_query(db, "SELECT id FROM t WHERE id = :id", {"id": 999})

    assert headers == ["id"]
    assert rows == []


def test_run_query_write_has_no_headers_and_persists(tmp_path):
    db = str(tmp_path / "d.db")
    _make_db(db)

    headers, rows = run_query(db, "UPDATE t SET name = :name WHERE id = :id", {"name": "z", "id": 1})

    assert headers == [] and rows == []
    headers2, rows2 = run_query(db, "SELECT name FROM t WHERE id = :id", {"id": 1})
    assert rows2 == [("z",)]


def test_run_query_bad_sql_raises(tmp_path):
    db = str(tmp_path / "d.db")
    _make_db(db)
    try:
        run_query(db, "SELECT * FROM nope", {})
        assert False, "должно было упасть"
    except sqlite3.Error:
        pass
