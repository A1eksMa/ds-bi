-- НАЗВАНИЕ: Последние транзакции по источнику
-- ОПИСАНИЕ: Сырые транзакции с расшифровкой (источник/показатель/id/значение). {txn_table} -- "transactions" или "transactions_archive"; :source_name -- имя источника; :row_limit -- сколько строк.
SELECT
    t.cnt,
    a.name AS action,
    datetime(t.dt, 'unixepoch') AS dt,
    s.name AS source,
    l.name AS label,
    i.value AS entity_id,
    v.value AS value,
    t.created_at
FROM {txn_table} t
JOIN srcs s ON s.src_id = t.src
JOIN lbs  l ON l.lb_id  = t.lb
JOIN ids  i ON i.id_id  = t.id
JOIN acts a ON a.act_id = t.act
LEFT JOIN vals v ON v.val_id = t.val
WHERE s.name = :source_name
ORDER BY t.dt DESC, t.cnt DESC
LIMIT :row_limit;
