from __future__ import annotations

import sqlite3
from typing import Dict, List, Sequence, Tuple


def run_query(
    db_path: str, sql: str, params: Dict[str, object],
) -> Tuple[List[str], List[Sequence[object]]]:
    """Выполнить SQL-текст по именованным параметрам (:name), вернуть (заголовки, строки).

    Пустой список заголовков -- запрос не вернул набор строк (INSERT/UPDATE/DDL и т.п.).
    Инструмент разработчика: соединение открывается на чтение и запись без ограничений --
    при необходимости можно руками поправить что-то в data.db тем же запросом.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if cursor.description is None:
            conn.commit()
            return [], []
        headers = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        conn.commit()
        return headers, rows
