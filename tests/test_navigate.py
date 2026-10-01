from src.navigate import choose_query_interactively


def _write(path, content="-- НАЗВАНИЕ: Т\nSELECT 1;"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scripted_input(answers):
    it = iter(answers)

    def fake_input(_prompt):
        return next(it)

    return fake_input


def test_navigate_picks_file_at_root_by_number(tmp_path):
    _write(tmp_path / "a.sql")
    logs = []
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input(["1"]), print_fn=logs.append,
    )
    assert result is not None and result.rel_path == "a"


def test_navigate_descends_into_subfolder_then_picks_file(tmp_path):
    _write(tmp_path / "crm" / "top.sql")
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input(["1", "1"]), print_fn=lambda _m: None,
    )
    assert result is not None and result.rel_path == "crm/top"


def test_navigate_full_path_shortcut_skips_browsing(tmp_path):
    _write(tmp_path / "crm" / "deep" / "top.sql")
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input(["crm/deep/top"]), print_fn=lambda _m: None,
    )
    assert result is not None and result.rel_path == "crm/deep/top"


def test_navigate_dotdot_goes_up_a_level(tmp_path):
    _write(tmp_path / "crm" / "top.sql")
    _write(tmp_path / "root.sql")
    # внутрь crm/, затем ".." назад в корень, затем выбрать root.sql (единственный файл там)
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input(["1", "..", "2"]), print_fn=lambda _m: None,
    )
    assert result is not None and result.rel_path == "root"


def test_navigate_empty_input_quits(tmp_path):
    _write(tmp_path / "a.sql")
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input([""]), print_fn=lambda _m: None,
    )
    assert result is None


def test_navigate_invalid_number_reprompts(tmp_path):
    _write(tmp_path / "a.sql")
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input(["99", "1"]), print_fn=lambda _m: None,
    )
    assert result is not None and result.rel_path == "a"


def test_navigate_bad_typed_path_reprompts(tmp_path):
    _write(tmp_path / "a.sql")
    result = choose_query_interactively(
        str(tmp_path), input_fn=_scripted_input(["nope/where", "1"]), print_fn=lambda _m: None,
    )
    assert result is not None and result.rel_path == "a"
