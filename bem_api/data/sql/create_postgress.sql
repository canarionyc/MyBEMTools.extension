-- 1. Create the Parent Table
-- use revit_families_database;


CREATE TABLE construction_elements AS
SELECT
    uuid() AS element_id, -- Generate a unique ID for the FK
    category.key AS category,
    element.key AS element_name,
    (element.value->>'total_thickness_m')::DOUBLE AS total_thickness_m
FROM json_each(read_json_auto('catalog.json')) AS category,
     json_each(category.value) AS element;

-- 2. Create the Child (Auxiliary) Table with Foreign Keys
CREATE TABLE element_layers AS
SELECT
    ce.element_id, -- Link back to parent
    (layer.value->>'layer_index')::INT AS layer_index,
    (layer.value->>'thickness_m')::DOUBLE AS thickness_m,
    (layer.value->>'material') AS material,
    (layer.value->>'conductivity')::DOUBLE AS conductivity,
    (layer.value->>'r_value')::DOUBLE AS r_value
FROM construction_elements ce
         JOIN (
    SELECT
        category.key AS cat,
        element.key AS el,
        unnest(element.value->'layers') AS value
    FROM json_each(read_json_auto('catalog.json')) AS category,
         json_each(category.value) AS element
) AS layer ON ce.category = layer.cat AND ce.element_name = layer.el;