from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional

from src.db import run_query
from src.discovery import QueryFile, find_query
from src.navigate import choose_query_interactively
from src.output import FORMATS, render
from src.params import bound_params, cast_value, dynamic_fields, parse_kv_args, substitute_identifiers

_DEFAULT_DB = os.environ.get("DS_BI_DB", "data.db")
_DEFAULT_QUERIES_DIR = os.environ.get("DS_BI_QUERIES_DIR", "queries")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ds-bi",
        description="Библиотека сохранённых SQL-запросов к базе ds — с параметрами "
                     "и группировкой по папкам.",
    )
    p.add_argument("--db", default=_DEFAULT_DB,
                   help="путь к data.db (по умолчанию: $DS_BI_DB или 'data.db')")
    p.add_argument("--queries-dir", default=_DEFAULT_QUERIES_DIR,
                   help="корень дерева запросов (по умолчанию: $DS_BI_QUERIES_DIR или 'queries')")
    p.add_argument("--format", choices=FORMATS, default="table", help="формат вывода результата")
    p.add_argument("--out", default=None,
                   help="записать результат в файл вместо вывода в терминал")
    p.add_argument(
        "query", nargs="?", default=None,
        help="путь к запросу в queries/ (например crm/revenue/top_customers); "
             "без него — интерактивная навигация по папкам",
    )
    p.add_argument("params", nargs="*", help="параметры запроса вида имя=значение")
    return p


def _resolve_query(args: argparse.Namespace) -> Optional[QueryFile]:
    if args.query:
        try:
            return find_query(args.queries_dir, args.query)
        except FileNotFoundError:
            print("❌ Запрос не найден: " + args.query, file=sys.stderr)
            return None
    return choose_query_interactively(args.queries_dir)


def _collect_values(names: List[str], cli_values: Dict[str, str], prompt: str) -> Dict[str, str]:
    out = {}
    for name in names:
        out[name] = cli_values[name] if name in cli_values else input(prompt.format(name=name)).strip()
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not os.path.isdir(args.queries_dir):
        os.makedirs(args.queries_dir, exist_ok=True)

    # sqlite3.connect на несуществующий путь тихо создаёт новый пустой файл —
    # почти всегда опечатка в --db (см. src/db.py), а не намеренное "создать
    # новую базу". Явная проверка здесь, ДО выбора запроса/запроса параметров --
    # не заставлять вводить значения, чтобы потом узнать, что путь был неверным.
    if not os.path.isfile(args.db):
        print("❌ Файл БД не найден: " + args.db, file=sys.stderr)
        return 1

    selected = _resolve_query(args)
    if selected is None:
        return 1

    cli_values = parse_kv_args(args.params)
    sql_text = selected.sql

    # {идентификаторы} -- имена таблиц/колонок, текстовая подстановка с проверкой
    fields = dynamic_fields(sql_text)
    if fields:
        field_values = _collect_values(fields, cli_values, " Введите имя для {{{name}}}: ")
        try:
            sql_text = substitute_identifiers(sql_text, field_values)
        except ValueError as exc:
            print("❌ " + str(exc), file=sys.stderr)
            return 1

    # :параметры -- значения, именованный биндинг sqlite3 (безопасно от инъекции)
    names = bound_params(sql_text)
    param_values: Dict[str, object] = {}
    if names:
        raw_values = _collect_values(names, cli_values, " Введите значение для :{name}: ")
        param_values = {k: cast_value(v) for k, v in raw_values.items()}

    try:
        headers, rows = run_query(args.db, sql_text, param_values)
    except Exception as exc:  # noqa: BLE001 -- sqlite3.Error и любая другая ошибка драйвера
        print("❌ Ошибка SQL при выполнении: " + str(exc), file=sys.stderr)
        return 1

    if not headers:
        print("\n[ Запрос успешно выполнен, данные не возвращены ]")
        return 0

    print("\nРезультат запроса '" + selected.title + "':")
    text = render(args.format, headers, rows)
    if args.out:
        encoding = "utf-8-sig" if args.format == "csv" else "utf-8"  # BOM -- иначе Excel
        newline = "" if args.format == "csv" else None               # не плодить \r\r\n
        with open(args.out, "w", encoding=encoding, newline=newline) as f:
            f.write(text)
        print("-> " + args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
