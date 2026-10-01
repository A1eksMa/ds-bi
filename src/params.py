from __future__ import annotations

import re
from typing import Dict, List

# Два независимых механизма подстановки в тексте запроса:
# - :name   -- значение; идёт нетронутым в sqlite3 как именованный биндинг (безопасно
#              от SQL-инъекции штатными средствами драйвера, см. src/db.py);
# - {name}  -- идентификатор (имя таблицы/колонки), биндингом driver'а не подставляется
#              (sqlite3 не умеет параметризовать идентификаторы) -- подставляется текстом
#              после проверки по белому списку символов (validate_identifier).

_IDENTIFIER_RE = re.compile(r"^[a-zA-Z0-9_]+$")
_FIELD_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")
_PARAM_RE = re.compile(r":([a-zA-Z0-9_]+)")


def parse_kv_args(args: List[str]) -> Dict[str, str]:
    """Разобрать список 'key=value' в словарь. Аргумент без '=' просто игнорируется."""
    out: Dict[str, str] = {}
    for arg in args:
        if "=" in arg:
            key, val = arg.split("=", 1)
            out[key.strip()] = val.strip()
    return out


def cast_value(raw: str):
    """Привести строку к числу, если это возможно: int -> float -> исходная строка.
    (int() сам понимает ведущий '-', в отличие от naive .isdigit())."""
    try:
        return int(raw)
    except (TypeError, ValueError):
        pass
    try:
        return float(raw)
    except (TypeError, ValueError):
        pass
    return raw


def dynamic_fields(sql: str) -> List[str]:
    """Имена {идентификаторов} в тексте запроса, по первому появлению, без повторов."""
    seen: List[str] = []
    for name in _FIELD_RE.findall(sql):
        if name not in seen:
            seen.append(name)
    return seen


def bound_params(sql: str) -> List[str]:
    """Имена :именованных-параметров, по алфавиту, без повторов."""
    return sorted(set(_PARAM_RE.findall(sql)))


def validate_identifier(name: str, value: str) -> None:
    """ValueError, если value небезопасно подставлять как есть вместо {name}."""
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(
            "недопустимое имя для {" + name + "}: " + repr(value)
            + " (разрешены только латинские буквы, цифры и '_')"
        )


def substitute_identifiers(sql: str, values: Dict[str, str]) -> str:
    """Подставить каждое {name} -> values[name], провалидировав значения заранее.

    Намеренно НЕ использует str.format(): тот интерпретирует вообще любые "{...}" в
    тексте (например, JSON-литерал в запросе) и падает/портит их. Заменяются только
    вхождения, реально совпавшие с {идентификатор}.
    """
    for name, value in values.items():
        validate_identifier(name, value)

    def _sub(m: "re.Match[str]") -> str:
        name = m.group(1)
        return values[name] if name in values else m.group(0)

    return _FIELD_RE.sub(_sub, sql)
