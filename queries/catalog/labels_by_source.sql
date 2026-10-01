-- НАЗВАНИЕ: Показатели источника
-- ОПИСАНИЕ: Список показателей (lbs) для источника по имени -- параметр :source_name.
SELECT l.lb_id, l.name, l.description, l.p
FROM lbs l
JOIN srcs s ON s.src_id = l.src_id
WHERE s.name = :source_name
ORDER BY l.name;
