-- НАЗВАНИЕ: Список источников
-- ОПИСАНИЕ: Все источники в БД (таблица srcs), без параметров.
SELECT src_id, name, description, p, key_label
FROM srcs
ORDER BY name;
