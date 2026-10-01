import pytest

from src.discovery import count_sql_files, find_query, load_dir


def _write(path, content="SELECT 1;"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- метаданные из заголовка -------------------------------------------------


def test_parses_title_and_description(tmp_path):
    _write(tmp_path / "a.sql", "-- НАЗВАНИЕ: Моё имя\n-- ОПИСАНИЕ: Моё описание\nSELECT 1;")
    q = find_query(str(tmp_path), "a")
    assert q.title == "Моё имя"
    assert q.description == "Моё описание"


def test_missing_title_falls_back_to_filename(tmp_path):
    _write(tmp_path / "plain.sql", "SELECT 1;")
    q = find_query(str(tmp_path), "plain")
    assert q.title == "plain"
    assert q.description == "Описание отсутствует"


def test_nested_fallback_title_is_just_filename_not_full_path(tmp_path):
    _write(tmp_path / "a" / "b" / "plain.sql", "SELECT 1;")
    q = find_query(str(tmp_path), "a/b/plain")
    assert q.title == "plain"


# --- load_dir (один уровень) -------------------------------------------------


def test_load_dir_lists_subdirs_and_files_separately(tmp_path):
    _write(tmp_path / "root.sql")
    _write(tmp_path / "sub" / "nested.sql")
    d = load_dir(str(tmp_path))
    assert d.dirs == ("sub",)
    assert [f.rel_path for f in d.files] == ["root"]


def test_load_dir_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dir(str(tmp_path), "nope")


def test_load_dir_ignores_non_sql_files(tmp_path):
    _write(tmp_path / "query.sql")
    (tmp_path / "notes.txt").write_text("hi", encoding="utf-8")
    d = load_dir(str(tmp_path))
    assert [f.rel_path for f in d.files] == ["query"]


# --- count_sql_files ----------------------------------------------------


def test_count_sql_files_recursive(tmp_path):
    _write(tmp_path / "a.sql")
    _write(tmp_path / "sub" / "b.sql")
    _write(tmp_path / "sub" / "deeper" / "c.sql")
    assert count_sql_files(str(tmp_path)) == 3


# --- find_query -----------------------------------------------------------


def test_find_query_with_and_without_extension(tmp_path):
    _write(tmp_path / "crm" / "top.sql")
    assert find_query(str(tmp_path), "crm/top").rel_path == "crm/top"
    assert find_query(str(tmp_path), "crm/top.sql").rel_path == "crm/top"


def test_find_query_tolerates_leading_trailing_slashes(tmp_path):
    _write(tmp_path / "crm" / "top.sql")
    assert find_query(str(tmp_path), "/crm/top/").rel_path == "crm/top"


def test_find_query_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_query(str(tmp_path), "nope")


@pytest.mark.parametrize("selector", ["../escape", "a/../../escape", "a//b", "a/./b", ""])
def test_find_query_rejects_path_traversal_and_malformed(tmp_path, selector):
    _write(tmp_path / "escape.sql")  # вне queries_root в реальности не положить, но и
    # не должно резолвиться даже при столь удачном совпадении имени
    with pytest.raises(FileNotFoundError):
        find_query(str(tmp_path), selector)
