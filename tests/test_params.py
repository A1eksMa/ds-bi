import pytest

from src.params import (
    bound_params,
    cast_value,
    dynamic_fields,
    parse_kv_args,
    substitute_identifiers,
    validate_identifier,
)


# --- parse_kv_args ----------------------------------------------------------


def test_parse_kv_args_basic():
    assert parse_kv_args(["a=1", "b=hello world"]) == {"a": "1", "b": "hello world"}


def test_parse_kv_args_ignores_non_kv():
    assert parse_kv_args(["justastring", "a=1"]) == {"a": "1"}


def test_parse_kv_args_value_may_contain_equals():
    assert parse_kv_args(["url=http://x?a=b"]) == {"url": "http://x?a=b"}


# --- cast_value ---------------------------------------------------------


@pytest.mark.parametrize("raw,expected", [
    ("5", 5),
    ("-5", -5),
    ("0", 0),
    ("3.14", 3.14),
    ("-3.14", -3.14),
    ("hello", "hello"),
    ("", ""),
])
def test_cast_value(raw, expected):
    assert cast_value(raw) == expected


# --- dynamic_fields / bound_params ---------------------------------------


def test_dynamic_fields_order_and_dedup():
    sql = "SELECT * FROM {table} WHERE {table}.{col} = 1"
    assert dynamic_fields(sql) == ["table", "col"]


def test_dynamic_fields_empty_when_none():
    assert dynamic_fields("SELECT 1") == []


def test_bound_params_sorted_and_deduped():
    sql = "WHERE b = :b AND a = :a AND b = :b"
    assert bound_params(sql) == ["a", "b"]


# --- validate_identifier --------------------------------------------------


@pytest.mark.parametrize("value", ["CRM", "crm_2026", "_private", "a1"])
def test_validate_identifier_accepts(value):
    validate_identifier("x", value)  # no raise


@pytest.mark.parametrize("value", ["crm; DROP TABLE srcs", "crm-x", "crm x", "crm.x", ""])
def test_validate_identifier_rejects(value):
    with pytest.raises(ValueError):
        validate_identifier("x", value)


# --- substitute_identifiers ------------------------------------------------


def test_substitute_identifiers_basic():
    out = substitute_identifiers("SELECT * FROM {table}", {"table": "srcs"})
    assert out == "SELECT * FROM srcs"


def test_substitute_identifiers_rejects_bad_value():
    with pytest.raises(ValueError):
        substitute_identifiers("SELECT * FROM {table}", {"table": "srcs; DROP TABLE srcs"})


def test_substitute_identifiers_leaves_unrelated_braces_untouched():
    """Не str.format(): JSON-подобный литерал в запросе не должен ни падать, ни ломаться."""
    sql = "SELECT json_extract(payload, '$.foo') FROM t WHERE payload = '{\"a\": 1}'"
    out = substitute_identifiers(sql, {})
    assert out == sql


def test_substitute_identifiers_only_replaces_known_names():
    out = substitute_identifiers("SELECT * FROM {table} WHERE {col} = 1", {"table": "srcs"})
    assert out == "SELECT * FROM srcs WHERE {col} = 1"
