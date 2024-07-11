import pandas as pd
import sqlite3
from tqdm import tqdm


excel_file = 'RUTA'
sqlite_db = 'base.db'


conn = sqlite3.connect(sqlite_db)
cursor = conn.cursor()


try:
    df = pd.read_excel(excel_file)
except Exception as e:
    print(f"Error al leer el archivo Excel: {e}")


df.columns = [c.replace(' ', '_') for c in df.columns]


df.insert(0, 'ID', range(1, 1 + len(df)))


df = df.where(pd.notnull(df), None)

table_exists = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nombre_tabla'").fetchone()
if not table_exists:

    columns_sql = ', '.join([f"{col} TEXT" for col in df.columns[1:]])  
    create_table_sql = f"CREATE TABLE nombre_tabla (ID INTEGER PRIMARY KEY, {columns_sql})"
    cursor.execute(create_table_sql)


for i, row in tqdm(df.iterrows(), total=df.shape[0], desc="Transfiriendo datos"):
    placeholders = ', '.join(['?'] * len(row))
    insert_sql = f"REPLACE INTO nombre_tabla VALUES ({placeholders})"
    try:
        cursor.execute(insert_sql, tuple(row))
    except Exception as e:
        print(f"Error insertando datos: {e}")
    conn.commit()


conn.close()
