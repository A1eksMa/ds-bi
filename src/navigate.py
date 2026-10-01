from __future__ import annotations

import os
from typing import Callable, List, Optional, Tuple, Union

from src.discovery import QueryFile, count_sql_files, find_query, load_dir

_Entry = Tuple[str, str, Union[str, QueryFile]]  # (подпись, "dir"|"file", значение)


def _list_entries(queries_root: str, rel: str, print_fn: Callable[[str], None]) -> List[_Entry]:
    d = load_dir(queries_root, rel)
    print_fn("\n📁 queries/" + rel)

    entries: List[_Entry] = []
    for name in d.dirs:
        sub_rel = (rel + "/" + name) if rel else name
        n = count_sql_files(os.path.join(queries_root, *sub_rel.split("/")))
        entries.append((name + "/", "dir", sub_rel))
        print_fn("  {0}. 📁 {1}  ({2} файл(ов))".format(len(entries), name, n))
    for f in d.files:
        entries.append((f.title, "file", f))
        print_fn("  {0}. {1}".format(len(entries), f.title))
        print_fn("      {0}".format(f.description))

    if not entries:
        print_fn("  (пусто)")
    return entries


def choose_query_interactively(
    queries_root: str,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> Optional[QueryFile]:
    """Пошаговая навигация по дереву queries/: на каждом уровне — пронумерованный список
    подпапок и файлов. Можно вместо номера сразу ввести путь целиком (с любого уровня
    вложенности) — так опытный пользователь пропускает навигацию. Пустой ввод/"q" — выход
    (None), ".." — на уровень выше.
    """
    rel = ""
    while True:
        try:
            entries = _list_entries(queries_root, rel, print_fn)
        except FileNotFoundError:
            print_fn("❌ Папка не найдена: queries/" + rel)
            return None

        if not entries and not rel:
            # в корне вообще нечего выбрать -- нет смысла спрашивать "какой номер"
            return None

        hint = "Выбери номер"
        if rel:
            hint += ", '..' — на уровень выше"
        hint += ", либо путь целиком (например crm/revenue/top): "
        choice = input_fn(hint).strip()

        if choice.lower() in ("", "q", "quit", "exit"):
            return None
        if choice == "..":
            rel = rel.rsplit("/", 1)[0] if "/" in rel else ""
            continue
        if choice.isdigit():
            idx = int(choice)
            if not (1 <= idx <= len(entries)):
                print_fn("❌ Нет пункта с номером " + choice)
                continue
            _, kind, value = entries[idx - 1]
            if kind == "dir":
                rel = value  # type: ignore[assignment]
                continue
            return value  # type: ignore[return-value]  # QueryFile

        try:
            return find_query(queries_root, choice)
        except FileNotFoundError:
            print_fn("❌ Не найдено: " + choice)
            continue
