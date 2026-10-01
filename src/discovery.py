from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Tuple

# Запросы живут деревом папок под queries_dir (любая вложенность). Каждый .sql файл
# адресуется путём относительно корня с "/" как разделителем, без расширения:
# queries/crm/revenue/top.sql -> "crm/revenue/top".

_TITLE_RE = re.compile(r"--\s*НАЗВАНИЕ:\s*(.*)")
_DESC_RE = re.compile(r"--\s*ОПИСАНИЕ:\s*(.*)")
_NO_DESCRIPTION = "Описание отсутствует"


@dataclass(frozen=True)
class QueryFile:
    """Один найденный файл запроса."""
    rel_path: str   # путь относительно queries_dir, "/" как разделитель, без ".sql"
    abs_path: str
    title: str
    description: str
    sql: str


@dataclass(frozen=True)
class QueryDir:
    """Один уровень дерева запросов (без рекурсии вглубь)."""
    rel_path: str          # "" для корня
    abs_path: str
    dirs: Tuple[str, ...]      # имена подпапок на этом уровне
    files: Tuple[QueryFile, ...]  # .sql файлы на этом уровне


def _parse_metadata(content: str, fallback_title: str) -> Tuple[str, str]:
    title_match = _TITLE_RE.search(content)
    desc_match = _DESC_RE.search(content)
    title = title_match.group(1).strip() if title_match else fallback_title
    description = desc_match.group(1).strip() if desc_match else _NO_DESCRIPTION
    return title, description


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _to_posix_rel(root: str, abs_path: str) -> str:
    rel = os.path.relpath(abs_path, root)
    return rel.replace(os.sep, "/")


def _load_file(queries_root: str, abs_path: str) -> QueryFile:
    content = _read(abs_path)
    rel = _to_posix_rel(queries_root, abs_path)
    if rel.endswith(".sql"):
        rel = rel[:-4]
    fallback_title = rel.rsplit("/", 1)[-1]
    title, description = _parse_metadata(content, fallback_title)
    return QueryFile(rel_path=rel, abs_path=abs_path, title=title, description=description, sql=content)


def load_dir(queries_root: str, rel_path: str = "") -> QueryDir:
    """Прочитать один уровень дерева запросов. FileNotFoundError — нет такой папки."""
    abs_dir = os.path.join(queries_root, *rel_path.split("/")) if rel_path else queries_root
    if not os.path.isdir(abs_dir):
        raise FileNotFoundError(abs_dir)

    dirs: List[str] = []
    files: List[QueryFile] = []
    for name in sorted(os.listdir(abs_dir)):
        full = os.path.join(abs_dir, name)
        if os.path.isdir(full):
            dirs.append(name)
        elif name.endswith(".sql"):
            files.append(_load_file(queries_root, full))
    return QueryDir(rel_path=rel_path, abs_path=abs_dir, dirs=tuple(dirs), files=tuple(files))


def count_sql_files(abs_dir: str) -> int:
    """Сколько .sql файлов в поддереве (рекурсивно) — для подписи папок в навигации."""
    total = 0
    for _, _, filenames in os.walk(abs_dir):
        total += sum(1 for n in filenames if n.endswith(".sql"))
    return total


def _split_selector(selector: str) -> List[str]:
    """Разобрать путь-селектор в список имён папок/файла, отклонив попытки выйти за
    пределы queries_root (".."), пустые сегменты (двойные "/") и т.п."""
    sel = selector.strip().strip("/")
    if sel.endswith(".sql"):
        sel = sel[:-4]
    parts = sel.split("/")
    if not sel or any(p in ("", ".", "..") for p in parts):
        raise FileNotFoundError(selector)
    return parts


def find_query(queries_root: str, selector: str) -> QueryFile:
    """Найти файл запроса по пути-селектору (с ".sql" или без, "/" — разделитель).
    FileNotFoundError, если файла нет или путь некорректен."""
    parts = _split_selector(selector)
    abs_path = os.path.join(queries_root, *parts) + ".sql"
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(selector)
    return _load_file(queries_root, abs_path)
