#! python3
import sqlite3

# Path to your uploaded database
db_path = r"C:\ProyectosCTEyCEE\CTEHE2019\Proyectos\EjemploI_2526_Option1_Config1\output\hulc_data.sqlite"


def get_construction_details(name):
    try:
        # 1. Connect to the database
        conn = sqlite3.connect(db_path)

        # 2. Use a DictRow-like approach for easier access
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 3. Query the wallcons_long table
        # We join with materials to get thermal properties (Conductivity, etc.)
        query = """
                SELECT w.layer_order, w.material, w.thickness, m.conductivity
                FROM wallcons_long w
                         LEFT JOIN materials m ON w.material = m.name
                WHERE w.name = ?
                ORDER BY w.layer_order ASC \
                """

        cursor.execute(query, (name,))
        rows = cursor.fetchall()

        print(f"--- Layers for {name} ---")
        for row in rows:
            # thickness in DB is in meters, converting to mm
            print(f"Layer {row['layer_order']}: {row['material']} "
                  f"({row['thickness'] * 1000:.1f}mm) - λ: {row['conductivity']}")

        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")


get_construction_details("SOL CAM SANIT")