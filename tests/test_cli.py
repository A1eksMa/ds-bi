import json
import sqlite3

from src.cli import main


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO t (id, name) VALUES (1, 'alice'), (2, 'bob')")
    conn.commit()
    conn.close()


def _write_query(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_one_shot_cli_with_nested_path_and_params(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(
        tmp_path / "queries" / "crm" / "by_id.sql",
        "-- НАЗВАНИЕ: По id\nSELECT name FROM t WHERE id = :id",
    )

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"), "crm/by_id", "id=2"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "По id" in out and "bob" in out


def test_dynamic_identifier_and_value_together(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(
        tmp_path / "queries" / "generic.sql",
        "SELECT name FROM {table} WHERE id = :id",
    )

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"),
               "generic", "table=t", "id=1"])

    assert rc == 0
    assert "alice" in capsys.readouterr().out


def test_rejects_unsafe_identifier_value(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(tmp_path / "queries" / "generic.sql", "SELECT * FROM {table}")

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"),
               "generic", "table=t; DROP TABLE t"])

    assert rc == 1
    assert "недопустимое имя" in capsys.readouterr().err


def test_missing_query_reports_error(tmp_path, capsys):
    (tmp_path / "queries").mkdir()
    rc = main(["--queries-dir", str(tmp_path / "queries"), "nope"])
    assert rc == 1
    assert "не найден" in capsys.readouterr().err


def test_write_statement_reports_no_data(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(tmp_path / "queries" / "touch.sql", "UPDATE t SET name = :name WHERE id = :id")

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"),
               "touch", "name=z", "id=1"])

    assert rc == 0
    assert "данные не возвращены" in capsys.readouterr().out


def test_sql_error_reports_nonzero(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(tmp_path / "queries" / "bad.sql", "SELECT * FROM nope")

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"), "bad"])

    assert rc == 1
    assert "Ошибка SQL" in capsys.readouterr().err


# --- --format / --out --------------------------------------------------


def test_format_json_to_stdout(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(tmp_path / "queries" / "all.sql", "SELECT id, name FROM t ORDER BY id")

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"),
               "all", "--format", "json"])

    assert rc == 0
    out = capsys.readouterr().out
    body = out.split("':\n", 1)[1]
    assert json.loads(body) == [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]


def test_format_csv_to_file_has_bom_for_excel(tmp_path, capsys):
    db = tmp_path / "d.db"
    _make_db(str(db))
    _write_query(tmp_path / "queries" / "all.sql", "SELECT id, name FROM t ORDER BY id")
    out_path = tmp_path / "out.csv"

    rc = main(["--db", str(db), "--queries-dir", str(tmp_path / "queries"),
               "all", "--format", "csv", "--out", str(out_path)])

    assert rc == 0
    assert ("-> " + str(out_path)) in capsys.readouterr().out
    raw = out_path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    text = raw.decode("utf-8-sig")
    assert text.splitlines()[0] == "id,name"
    assert "alice" in text and "bob" in text


def test_queries_dir_autocreated_if_missing(tmp_path):
    missing = tmp_path / "queries"
    assert not missing.exists()
    rc = main(["--queries-dir", str(missing)])  # без query -> интерактив, но input() не вызовется
    # пустая папка -> навигация сразу вернёт None (ничего не выбрано) -> main() вернёт 1,
    # но сама папка должна быть создана как побочный эффект
    assert rc == 1
    assert missing.is_dir()
