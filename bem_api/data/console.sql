SELECT * FROM read_json_auto('C:\dev\MyBEMTools.extension\bem_api\data\catalog.json');

SELECT * FROM read_json('C:\dev\MyBEMTools.extension\bem_api\data\catalog.json');
    

WITH raw_file AS (
    -- 1. Force DuckDB to read the entire file as one raw JSON chunk
    SELECT json FROM read_json('C:\dev\MyBEMTools.extension\bem_api\data\catalog.json', columns={'json': 'JSON'})
)
SELECT
    category.key AS Category,
    family.key AS Family_Name,
    (family.value->>'total_thickness_m')::FLOAT AS Total_Thickness_m,
    json_array_length(family.value->'layers') AS Layer_Count,
    -- Note: Updated keys to match your actual catalog.json structure
    layer.value->>'material' AS Material_Name,
    (layer.value->>'thickness_m')::FLOAT AS Layer_Thickness_m,
    (layer.value->>'conductivity')::FLOAT AS Thermal_Conductivity_W_m_K,
    (layer.value->>'r_value')::FLOAT AS R_Value
FROM raw_file,
-- 2. Unpack the Top Level (Walls, Roofs) into Key/Value columns
    UNNEST(json_entries(json)) AS category(key, value),
-- 3. Unpack the Second Level (Family Names) into Key/Value columns
    UNNEST(json_entries(category.value)) AS family(key, value),
-- 4. Cast the Layers array to a list of JSON objects and Unpack
    UNNEST(CAST(family.value->'layers' AS JSON[])) AS layer(value);

WITH raw_file AS (
    -- 1. Read the file as raw JSON
    SELECT json FROM read_json('C:\dev\MyBEMTools.extension\bem_api\data\catalog.json', columns={'json': 'JSON'})
)
SELECT
    category.key AS Category,
    family.key AS Family_Name,
    (family.value->>'total_thickness_m')::FLOAT AS Total_Thickness_m,
    json_array_length(family.value->'layers') AS Layer_Count,
    layer.value->>'material' AS Material_Name,
    (layer.value->>'thickness_m')::FLOAT AS Layer_Thickness_m,
    (layer.value->>'conductivity')::FLOAT AS Thermal_Conductivity_W_m_K,
    (layer.value->>'r_value')::FLOAT AS R_Value
FROM raw_file,
-- 2. Cast the Top Level to a Map and Unnest into key/value
    UNNEST(CAST(json AS MAP(VARCHAR, JSON))) AS category,
-- 3. Cast the Second Level (Family Names) to a Map and Unnest into key/value
    UNNEST(CAST(category.value AS MAP(VARCHAR, JSON))) AS family,
-- 4. Cast the Layers array to a list of JSON objects and Unpack
    UNNEST(CAST(family.value->'layers' AS JSON[])) AS layer;



-- Connect to a persistent DuckDB database file (e.g., via CLI: duckdb catalog.duckdb)
-- Then execute the following statement to create and populate the table:

CREATE TABLE materials AS
WITH raw_file AS (
    -- Read the file as raw JSON
    SELECT json FROM read_json('C:\dev\MyBEMTools.extension\bem_api\data\catalog.json', columns ={'json': 'JSON'}))
SELECT category.key AS Category,
       family.key   AS Family_Name,
       (family.value ->>'total_thickness_m')::FLOAT AS Total_Thickness_m, 
    json_array_length(family.value -> 'layers') AS Layer_Count,
       (layer.value ->>'layer_index')::INT AS Layer_Index, layer.value ->>'material' AS Material_Name,
(
    layer.value->>'thickness_m'):: FLOAT AS Layer_Thickness_m,
(
    layer.value->>'conductivity'
):: FLOAT AS Thermal_Conductivity_W_m_K,
(
    layer.value
    ->>
    'r_value'
):: FLOAT AS R_Value
    FROM raw_file
    CROSS JOIN UNNEST
(
    json_keys(
    CAST (
    json AS
    MAP
(
    VARCHAR,
    JSON
))
    )
    ) AS category
(
    key
)
    CROSS JOIN UNNEST
(
    json_keys(
    CAST (
    json
    ->
    category
    .
    key AS
    MAP
(
    VARCHAR,
    JSON
))
    )
    ) AS family
(
    key
)
    CROSS JOIN UNNEST
(
    CAST (
    json
    ->
    category
    .
    key
    ->
    family
    .
    key
    ->
    'layers' AS
    JSON
[]
)
    ) AS layer
(
    value
);