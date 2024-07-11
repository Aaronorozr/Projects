import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk, simpledialog
import pandas as pd
import sqlite3
from ttkthemes import ThemedTk
import os
import sys
import re

db_path = ""
porcentaje_global = 5.0
dias_global = 4.0
def import_excel_data():
    global db_path
    if not db_path:
        messagebox.showwarning("Advertencia", "Primero selecciona una base de datos")
        return

    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if file_path:
        df = pd.read_excel(file_path)
        store_data(df)
        show_data(df)

def create_database():
    global db_path
    db_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite database", "*.db")])
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS excel_data (
                CONSECUTIVO INTEGER PRIMARY KEY AUTOINCREMENT,
                No_Parte TEXT,
                DESCRIPCIÓN TEXT,
                CANTIDAD INTEGER,
                UNIDAD TEXT,
                Precio_Proveedor1 REAL,
                Precio_Proveedor2 REAL,
                Entrega_Proveedor1 TEXT,
                Entrega_Proveedor2 TEXT,
                Mejor_Proveedor TEXT
            )
        ''')
        conn.commit()
        conn.close()
        messagebox.showinfo("Información", f"Base de datos creada: {db_path}")
        

        for i in tree.get_children():
            tree.delete(i)
        load_data_from_db() 
        
def select_database():
    global db_path
    db_path = filedialog.askopenfilename(filetypes=[("SQLite database", "*.db")])
    if db_path:

        for i in tree.get_children():
            tree.delete(i)

        tree["columns"] = []
        messagebox.showinfo("Información", f"Base de datos seleccionada: {db_path}")
        load_data_from_db()

def update_column_name_in_db(old_name, new_name):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(excel_data)")
        columns = [row[1] for row in cursor.fetchall()]
        columns = [new_name if col == old_name else col for col in columns]
        columns_with_types = [f"{col} TEXT" for col in columns]
        cursor.execute(f"CREATE TABLE excel_data_new ({', '.join(columns_with_types)})")
        columns_str = ', '.join(columns)
        cursor.execute(f"INSERT INTO excel_data_new ({columns_str}) SELECT * FROM excel_data")
        cursor.execute("DROP TABLE excel_data")
        cursor.execute("ALTER TABLE excel_data_new RENAME TO excel_data")
        conn.commit()
        messagebox.showinfo("Éxito", "Nombre de columna actualizado en la base de datos")
    except sqlite3.OperationalError as e:
        messagebox.showerror("Error", f"Error al actualizar el nombre de la columna en la base de datos: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")
    finally:
        if conn:
            conn.close()

def store_data(df):
    global db_path
    if not db_path:
        messagebox.showwarning("Advertencia", "Primero selecciona una base de datos")
        return   
    try:
        conn = sqlite3.connect(db_path)

        df.to_sql('excel_data', conn, if_exists='replace', index=False)
        conn.close()
        messagebox.showinfo("Información", "Datos almacenados correctamente en la base de datos")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al almacenar los datos: {e}")

def ima_columna():
    global columnas_añadidas
    if columnas_añadidas:
        ultima_columna = columnas_añadidas.pop()
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(f"ALTER TABLE excel_data DROP COLUMN {ultima_columna}")
            conn.commit()
            conn.close()
            load_data_from_db()  
            messagebox.showinfo("Información", f"Columna '{ultima_columna}' eliminada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al eliminar la columna: {e}")
            columnas_añadidas.append(ultima_columna)  
    else:
        messagebox.showinfo("Información", "No hay columnas recientemente añadidas para eliminar.")

def load_data_from_db():
    global db_path
    if db_path:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()       

        cursor.execute("SELECT * FROM excel_data")
        column_names = [description[0] for description in cursor.description]       

        tree["columns"] = column_names
        tree["show"] = "headings"
        for column in column_names:
            tree.heading(column, text=column)
            tree.column(column, width=100)      

        rows = cursor.fetchall()
        for row in rows:
            tree.insert("", "end", values=row)        
        if not rows:
            messagebox.showinfo("Información", "La base de datos está vacía.")      
        conn.close()

def show_data(df):
    for i in tree.get_children():
        tree.delete(i)
    tree["column"] = list(df.columns)
    tree["show"] = "headings"
    ancho_minimo_columna = 85  
    for column in tree["column"]:
        tree.heading(column, text=column)
        tree.column(column, width=ancho_minimo_columna, minwidth=ancho_minimo_columna, stretch=False)
    for col in tree["columns"]:
        tree.heading(col, text=col, command=lambda _col=col: sort_by_column(tree, _col, False))
    df_rows = df.fillna('').to_numpy().tolist()
    for row in df_rows:
        tree.insert("", "end", values=row)

def on_double_click(event):
    region = tree.identify_region(event.x, event.y)
    if region == "cell":
        item = tree.selection()[0]
        column_id = tree.identify_column(event.x)
        column = int(column_id.lstrip('#')) - 1
        if tree.heading(column_id, 'text') == "CONSECUTIVO":
            return
        old_value = tree.set(item, column)
        entry_edit = ttk.Entry(root)
        entry_edit.insert(0, old_value)
        x, y, width, height = tree.bbox(item, column)
        entry_edit.place(x=x, y=y, width=width, height=height)
        def save_edit(event=None):
            new_value = entry_edit.get()
            tree.set(item, column, new_value)
            entry_edit.destroy()
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                column_name = tree['columns'][column]
                consecutivo_value = tree.item(item, 'values')[0] 
                query = f"UPDATE excel_data SET \"{column_name}\" = ? WHERE CONSECUTIVO = ?"
                cursor.execute(query, (new_value, consecutivo_value))
                conn.commit()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar la base de datos: {e}")
            finally:
                if conn:
                    conn.close()
        def on_focus_out(event):
            save_edit()
        entry_edit.bind('<Return>', save_edit)
        entry_edit.bind('<FocusOut>', on_focus_out)
        entry_edit.focus()
    elif region == "heading":
        column_id = tree.identify_column(event.x)
        column_index = int(column_id.replace('#', '')) - 1
        old_column_name = tree.heading(column_id, 'text')
        def rename_column():
            new_name = simpledialog.askstring("Renombrar columna", "Nombre de la nueva columna:", initialvalue=old_column_name)
            if new_name and new_name != old_column_name:
                tree.heading(column_id, text=new_name)
                update_column_name_in_db(old_column_name, new_name) 
        rename_column()

def rename_column():
    def perform_rename():
        old_name = column_to_rename_var.get()
        new_name = new_name_entry.get()
        if old_name == "CONSECUTIVO":
            messagebox.showwarning("Advertencia", "No se puede cambiar el nombre de la columna 'CONSECUTIVO'.")
            return
        if old_name and new_name and old_name in tree['columns']:
            try:
                conn = sqlite3.connect(db_path)
                conn.execute(f"ALTER TABLE excel_data RENAME COLUMN \"{old_name}\" TO \"{new_name}\"")
                conn.commit()
                conn.close()
                load_data_from_db()
                rename_window.destroy()
                messagebox.showinfo("Éxito", f"Columna '{old_name}' renombrada a '{new_name}'.")
            except sqlite3.OperationalError as e:
                messagebox.showerror("Error", f"Error al renombrar la columna: {e}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if conn:
                    conn.close()
        else:
            messagebox.showwarning("Advertencia", "Nombre de columna no válido o campo de nuevo nombre vacío.")

    rename_window = tk.Toplevel(root)
    rename_window.title("Renombrar Columna")

    ttk.Label(rename_window, text="Seleccionar columna:").grid(row=0, column=0)
    column_to_rename_var = tk.StringVar(rename_window)
    column_to_rename_dropdown = ttk.Combobox(rename_window, textvariable=column_to_rename_var, values=tree['columns'])
    column_to_rename_dropdown.grid(row=0, column=1)


    ttk.Label(rename_window, text="Nuevo nombre de la columna:").grid(row=1, column=0)
    new_name_entry = ttk.Entry(rename_window)
    new_name_entry.grid(row=1, column=1)

    rename_button = ttk.Button(rename_window, text="Renombrar", command=perform_rename)
    rename_button.grid(row=2, column=0, columnspan=2)

def add_row():
    new_row_window = tk.Toplevel(root)
    new_row_window.title("Agregar nueva fila")
    entries = []
    def save_new_row():
        nonlocal entries  
        new_values = [entry.get() for entry in entries]  
        print(f"Valores a insertar: {new_values}") 
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            columns = [column for column in tree['columns']]  
            placeholders = ', '.join('?' * len(columns))  
            query = f"INSERT INTO excel_data ({', '.join(columns)}) VALUES ({placeholders})"
            print(f"Consulta SQL: {query}")  
            cursor.execute(query, new_values)
            conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar en la base de datos: {e}")
        finally:
            cursor.close()
            conn.close()
        tree.insert('', 'end', values=new_values)
        new_row_window.destroy()
    for i, column in enumerate(tree['columns']):
        ttk.Label(new_row_window, text=column).grid(row=i, column=0)
        entry = ttk.Entry(new_row_window)
        entry.grid(row=i, column=1)
        entries.append(entry)
    save_button = ttk.Button(new_row_window, text="Guardar", command=save_new_row)
    save_button.grid(row=len(tree['columns']), column=0, columnspan=2)


def delete_row():
    selected_items = tree.selection()
    if not selected_items:
        messagebox.showinfo("Información", "Selecciona al menos una fila para eliminar.")
        return
    respuesta = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas eliminar las filas seleccionadas?")
    if respuesta:
        for item in selected_items:
            tree.delete(item)
        messagebox.showinfo("Información", f"Se han eliminado {len(selected_items)} filas.")

def exportar_a_excel():
    datos = []  
    for fila in tree.get_children():
        datos.append(tree.item(fila)['values'])   
    if not tree["columns"]:
        messagebox.showerror("Error", "No hay columnas para exportar.")
        return    
    df = pd.DataFrame(datos, columns=tree['columns'])  
    filepath = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("All Files", "*.*")]
    )
    if not filepath:
        return  
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')  
    df.to_excel(writer, sheet_name='Hoja1', index=False)
    workbook  = writer.book
    worksheet = writer.sheets['Hoja1']
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1})
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    for column in df:
        column_width = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        worksheet.set_column(col_idx, col_idx, column_width)
    writer.close()
    messagebox.showinfo("Exportación exitosa", f"Los datos se han exportado a {filepath}")


def limpiar_valor_precio(valor):

    if valor is None:
        valor = ''
    else:
        valor = str(valor)
    valor_limpio = re.sub(r'[^\d.]', '', valor)
    return valor_limpio


def limpiar_valor_precio(valor):

    if valor is None:
        valor = ''
    else:
        valor = str(valor)
    valor_limpio = re.sub(r'[^\d.]', '', valor)
    try:
        return float(valor_limpio)  
    except ValueError:
        return float('inf') 

def encontrar_mejor_proveedor():
    global porcentaje_global, dias_global
    tree.tag_configure('no_disponible', background='red')
    indices_precios = [(i, col.replace("Precio_", "")) for i, col in enumerate(tree['columns']) if col.startswith("Precio_")]
    indices_entrega = {col.replace("Entrega_", ""): i for i, col in enumerate(tree['columns']) if col.startswith("Entrega_")}

    for child in tree.get_children():
        valores = tree.item(child)["values"]
        proveedores = []
        for indice, proveedor in indices_precios:
            valor_precio = valores[indice]
            precio = limpiar_valor_precio(valor_precio) if valor_precio not in ['nan', '-', ''] else float('inf')
            indice_entrega = indices_entrega[proveedor]
            dias = float(valores[indice_entrega]) if valores[indice_entrega] not in ['nan', '-', '', 'None'] else float('inf')
            proveedores.append((proveedor, precio, dias))

        proveedores_validos = [prov for prov in proveedores if prov[1] != float('inf') and prov[2] != float('inf')]

        if len(proveedores_validos) == 1:
            tree.set(child, "Mejor_Proveedor", proveedores_validos[0][0])
            tree.item(child, tags=('no_disponible',))
        elif len(proveedores_validos) < 1:
            tree.set(child, "Mejor_Proveedor", "No asignado")
            tree.item(child, tags=('no_disponible',))
        else:
            mejor_proveedor = min(proveedores_validos, key=lambda x: (x[1], x[2]))
            mejor_precio, mejores_dias = mejor_proveedor[1:]
            for proveedor, precio, dias in proveedores_validos:
                if proveedor != mejor_proveedor[0]:
                    if precio <= mejor_precio * (1 + porcentaje_global / 100) and (mejores_dias - dias) >= dias_global:
                        mejor_proveedor = (proveedor, precio, dias)
                        mejor_precio, mejores_dias = precio, dias
            tree.set(child, "Mejor_Proveedor", mejor_proveedor[0] if mejor_proveedor[1] != float('inf') else "No asignado")
            if len(proveedores_validos) > 1:
                tree.item(child, tags=())  




def ajustar_parametros_proveedor():
    global porcentaje_global, dias_global
    
    def aplicar_cambios():
        global porcentaje_global, dias_global
        try:
            porcentaje_global = float(porcentaje_entry.get())
            dias_global = float(dias_entry.get())
            parametros_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa valores numéricos válidos.")

    parametros_window = tk.Toplevel(root)
    parametros_window.title("Ajustar regla de constantes")

    ttk.Label(parametros_window, text="Porcentaje (%):").grid(row=0, column=0)
    porcentaje_entry = ttk.Entry(parametros_window)
    porcentaje_entry.grid(row=0, column=1)
    porcentaje_entry.insert(0, str(porcentaje_global))  

    ttk.Label(parametros_window, text="Días de diferencia:").grid(row=1, column=0)
    dias_entry = ttk.Entry(parametros_window)
    dias_entry.grid(row=1, column=1)
    dias_entry.insert(0, str(dias_global))  

    aplicar_btn = ttk.Button(parametros_window, text="Aplicar Cambios", command=aplicar_cambios)
    aplicar_btn.grid(row=2, column=0, columnspan=2)

def on_heading_click(event):
    region = tree.identify("region", event.x, event.y)
    if region == "heading":
        column_id = tree.identify_column(event.x)
        column_index = int(column_id.replace('#', '')) - 1
        old_name = tree.heading(column_id)['text']

        if old_name == "CONSECUTIVO":
            messagebox.showwarning("Advertencia", "No se puede cambiar el nombre de la columna 'CONSECUTIVO'.")
            return

        rename_window = tk.Toplevel(root)
        rename_window.title("Renombrar Columna")

        ttk.Label(rename_window, text="Nuevo nombre de la columna:").grid(row=0, column=0)
        new_name_entry = ttk.Entry(rename_window)
        new_name_entry.insert(0, old_name)
        new_name_entry.grid(row=0, column=1)

        def perform_rename():
            new_name = new_name_entry.get()
            if new_name and new_name != old_name:
                tree.heading(column_id, text=new_name)
                update_column_name_in_db(old_name, new_name) 

        rename_button = ttk.Button(rename_window, text="Renombrar", command=perform_rename)
        rename_button.grid(row=1, column=0, columnspan=2)

def sort_by_column(tree, col, reverse):

    data_list = [(tree.set(k, col), k) for k in tree.get_children('')]


    try:
        data_list = [(float(data), iid) if data else (0, iid) for data, iid in data_list]
    except ValueError:
        pass  


    data_list.sort(reverse=reverse)


    for index, (val, k) in enumerate(data_list):
        tree.move(k, '', index)


    tree.heading(col, command=lambda: sort_by_column(tree, col, not reverse))

def eliminar_columna_seleccionada():
    def confirmar_y_eliminar():
        columna_a_eliminar = column_to_delete_var.get()
        if not columna_a_eliminar:
            messagebox.showwarning("Advertencia", "Selecciona una columna para eliminar.")
            return
        try:
            conn = sqlite3.connect(db_path)

            df = pd.read_sql('SELECT * FROM excel_data', conn)
            columnas_restantes = df.columns.drop(columna_a_eliminar).tolist()


            df_temp = df[columnas_restantes]
            df_temp.to_sql('excel_data_temp', conn, if_exists='replace', index=False)


            conn.execute("DROP TABLE excel_data")
            conn.execute("ALTER TABLE excel_data_temp RENAME TO excel_data")
            conn.commit()
            conn.close()
            load_data_from_db()  
            delete_window.destroy()
            messagebox.showinfo("Éxito", f"Columna '{columna_a_eliminar}' eliminada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la columna: {e}")

    delete_window = tk.Toplevel(root)
    delete_window.title("Eliminar Columna")

    ttk.Label(delete_window, text="Seleccionar columna:").grid(row=0, column=0)
    column_to_delete_var = tk.StringVar(delete_window)
    column_to_delete_dropdown = ttk.Combobox(delete_window, textvariable=column_to_delete_var, values=tree['columns'])
    column_to_delete_dropdown.grid(row=0, column=1)

    delete_button = ttk.Button(delete_window, text="Eliminar", command=confirmar_y_eliminar)
    delete_button.grid(row=1, column=0, columnspan=2)

def editar_fila_seleccionada():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Advertencia", "Selecciona una fila para editar")
        return

    valores_actuales = tree.item(selected_item[0], 'values')
    edit_window = tk.Toplevel(root)
    edit_window.title("Editar Fila")

    entries = []
    for i, column in enumerate(tree['columns']):
        ttk.Label(edit_window, text=column).grid(row=i, column=0)
        entry = ttk.Entry(edit_window)
        entry.insert(0, valores_actuales[i])
        entry.grid(row=i, column=1)
        entries.append(entry)

    def save_edited_row():
        new_values = [entry.get() for entry in entries]

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()


            consecutivo = valores_actuales[0]
            columns_for_update = [f'"{col}" = ?' for col in tree['columns']]
            update_query = "UPDATE excel_data SET " + ", ".join(columns_for_update) + f" WHERE CONSECUTIVO = ?"
            cursor.execute(update_query, new_values + [consecutivo])
            conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la base de datos: {e}")
        finally:
            if conn:
                conn.close()

        tree.item(selected_item[0], values=new_values)
        edit_window.destroy()

    save_button = ttk.Button(edit_window, text="Guardar Cambios", command=save_edited_row)
    save_button.grid(row=len(tree['columns']), column=0, columnspan=2)

def add_column():
    def add():
        column_name = entry_column_name.get()
      

        if not column_name:
            messagebox.showwarning("Advertencia", "Ingresa un nombre para la columna.")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"ALTER TABLE excel_data ADD COLUMN {column_name} TEXT")  
            conn.commit()
            conn.close()
            messagebox.showinfo("Información", f"Columna '{column_name}' agregada al final.")
            load_data_from_db()  
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al agregar la columna: {e}")


    entry_window = tk.Toplevel(root)
    entry_window.title("Agregar Columna")


    ttk.Label(entry_window, text="Nombre de la columna:").grid(row=0, column=0)
    entry_column_name = ttk.Entry(entry_window)
    entry_column_name.grid(row=0, column=1)


    add_button = ttk.Button(entry_window, text="Agregar", command=add)
    add_button.grid(row=1, column=0, columnspan=2)

def mostrar_informacion():
    messagebox.showinfo(
        "Instrucciones para 'Encontrar Mejor Proveedor'",
        "Para que la función 'Encontrar Mejor Proveedor' funcione correctamente:\n\n"
        "- Siempre debe existir una columna con el nombre 'CONSECUTIVO' diferenciando por numeros consecutivos cada fila.\n"
        "- Los proveedores y su fecha de entrega deben estar en columnas tituladas 'Entrega_NOMBREPROVEEDOR'.\n"
        "- Los precios correspondientes deben estar en columnas tituladas 'Precio_NOMBREPROVEEDOR'.\n"
        "- Deberas cambiar NOMBREPROVEEDOR por el nombre real del provedor en cada caso.\n"
        "- Debe existir una columna llamada 'Mejor_Proveedor' para visualizar el resultado."
    )

def pegar_desde_portapapeles(event):
    if not db_path:
        messagebox.showerror("Error", "Por favor, selecciona una base de datos primero.")
        return
    

    try:
        item_id = tree.focus()
        column_id = tree.identify_column(event.x).lstrip('#')
        if not item_id or not column_id:
            messagebox.showerror("Error", "Selecciona una celda para pegar los datos.")
            return

        selected_row_index = tree.index(item_id)
        selected_column_index = int(column_id) - 1  
    except Exception as e:
        messagebox.showerror("Error", f"Error al identificar la celda seleccionada: {e}")
        return

    clipboard_data = root.clipboard_get().strip()
    rows_data = clipboard_data.split("\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for r_idx, row in enumerate(rows_data):
        column_data = row.split("\t")
        for c_idx, cell in enumerate(column_data):

            if selected_row_index + r_idx < len(tree.get_children()) and selected_column_index + c_idx < len(tree["columns"]):
                target_item = tree.get_children()[selected_row_index + r_idx]
                target_column = tree["columns"][selected_column_index + c_idx]

                tree.set(target_item, target_column, cell)

                cursor.execute(f"UPDATE excel_data SET {target_column} = ? WHERE CONSECUTIVO = ?", (cell, tree.item(target_item)['values'][0]))
    
    conn.commit()
    conn.close()
    load_data_from_db() 

columna_seleccionada = None  

def mostrar_menu_contextual(event):
    try:
 
        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)      
      
        if item_id and column_id:
            menu_contextual.entryconfig("Pegar", command=lambda: pegar_desde_portapapeles(event))
            menu_contextual.tk_popup(event.x_root, event.y_root)
    finally:
 
        menu_contextual.grab_release()

def agregar_filas_vacias():
    cantidad = simpledialog.askinteger("Agregar Filas Vacías", "¿Cuántas filas vacías deseas agregar?", minvalue=1)
    if cantidad:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for _ in range(cantidad):
                cursor.execute('''
                    INSERT INTO excel_data (No_Parte, DESCRIPCIÓN, CANTIDAD, UNIDAD, Precio_Proveedor1, Precio_Proveedor2, Entrega_Proveedor1, Entrega_Proveedor2, Mejor_Proveedor) 
                    VALUES (NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
                ''')
            conn.commit()
            messagebox.showinfo("Éxito", f"Se han agregado {cantidad} filas vacías.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al agregar filas vacías: {e}")
        finally:
            if conn:
                conn.close()
        load_data_from_db()

def corregir_consecutivos():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT CONSECUTIVO FROM excel_data ORDER BY CONSECUTIVO ASC")
        filas = cursor.fetchall()
   
        consecutivo_actual = 1
        for fila in filas:
            if fila[0] != consecutivo_actual:
                cursor.execute("UPDATE excel_data SET CONSECUTIVO = ? WHERE CONSECUTIVO = ?", (consecutivo_actual, fila[0]))
            consecutivo_actual += 1
        conn.commit()
        messagebox.showinfo("Éxito", "Los números consecutivos han sido corregidos.")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al corregir los consecutivos: {e}")
    finally:
        if conn:
            conn.close()
        load_data_from_db()

root = ThemedTk(theme="winnative")
root.title("V1.0")
root.geometry("1200x670") 
root.minsize(1000, 700)
menu_contextual = tk.Menu(root, tearoff=0)
menu_contextual.add_command(label="Pegar", command=lambda: pegar_desde_portapapeles(None))
style = ttk.Style()
style.configure('Green.TButton', background='#FBC974', foreground='Black')
style.configure('Blue.TButton', background='blue', foreground='Black')
#style.configure('Red.TButton', background='white', foreground='Red')
style.configure('Accent.TButton', background='black', foreground='Red')

barra_lateral = ttk.Frame(root, style='Card.TFrame')
barra_lateral.grid(row=0, column=1, sticky="ns")


importar_excel_btn = ttk.Button(barra_lateral, text="Importar de Excel", style='Blue.TButton', command=import_excel_data)
importar_excel_btn.pack(fill='x', padx=5, pady=5)

exportar_excel_btn = ttk.Button(barra_lateral, text="Exportar a Excel", style='Blue.TButton', command=exportar_a_excel)
exportar_excel_btn.pack(fill='x', padx=5, pady=5)

mejor_proveedor_btn = ttk.Button(barra_lateral, text="Encontrar Mejor Proveedor", style='Accent.TButton', command=encontrar_mejor_proveedor)
mejor_proveedor_btn.pack(fill='x', padx=5, pady=5)

boton_agregar_filas_vacias = ttk.Button(barra_lateral, text="Agregar Filas Vacías", style='Green.TButton', command=agregar_filas_vacias)
boton_agregar_filas_vacias.pack(fill='x', padx=5, pady=5)

boton_corregir_consecutivos = ttk.Button(barra_lateral, text="Corregir Consecutivos", style='Green.TButton', command=corregir_consecutivos)
boton_corregir_consecutivos.pack(fill='x', padx=5, pady=5)


boton_agregar_columna = ttk.Button(barra_lateral, text="Agregar Columna", style='Green.TButton', command=add_column)
boton_agregar_columna.pack(fill='x', padx=5, pady=(90, 5))

boton_renombrar_columna = ttk.Button(barra_lateral, text="Renombrar Columna", style='Green.TButton',command=rename_column)
boton_renombrar_columna.pack(fill='x', padx=5, pady=5)

boton_eliminar_columna = ttk.Button(barra_lateral, text="Eliminar Columna", style='Green.TButton', command=eliminar_columna_seleccionada)
boton_eliminar_columna.pack(fill='x', padx=5, pady=5)

boton_agregar_fila = ttk.Button(barra_lateral, text="Agregar Fila", style='Green.TButton', command=add_row)
boton_agregar_fila.pack(fill='x', padx=5, pady=5)

boton_editar_fila = ttk.Button(barra_lateral, text="Editar Fila", style='Green.TButton', command=editar_fila_seleccionada)
boton_editar_fila.pack(fill='x', padx=5, pady=5)

boton_eliminar_fila = ttk.Button(barra_lateral, text="Eliminar Fila", style='Green.TButton', command=delete_row)
boton_eliminar_fila.pack(fill='x', padx=5, pady=5)

ajustar_proveedor_btn = ttk.Button(barra_lateral, text="Ajustar variables", style='Accent.TButton', command=ajustar_parametros_proveedor)
ajustar_proveedor_btn.pack(fill='x', padx=5, pady=(90, 5))
boton_ayuda = ttk.Button(barra_lateral, text="Ayuda", command=mostrar_informacion)
boton_ayuda.pack(fill='x', padx=5, pady=5)
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Crear Base de Datos", command=create_database)
file_menu.add_command(label="Seleccionar Base de Datos", command=select_database)
menu_bar.add_cascade(label="Archivo", menu=file_menu)
file_menu.add_command(label="Importar Excel", command=import_excel_data)
file_menu.add_command(label="Exportar a Excel", command=exportar_a_excel)
edit_menu = tk.Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="Agregar Columna", command=add_column)
edit_menu.add_command(label="Renombrar Columna", command=rename_column)
edit_menu.add_command(label="Eliminar Columna", command=eliminar_columna_seleccionada)
edit_menu.add_command(label="Agregar Fila", command=add_row)
edit_menu.add_command(label="Editar Fila", command=editar_fila_seleccionada)
edit_menu.add_command(label="Eliminar Fila", command=delete_row)
option_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Editar", menu=edit_menu)
edit_menu.add_command(label="Encontrar Mejor Proveedor", command=encontrar_mejor_proveedor)
menu_bar.add_cascade(label="Opciones", menu=option_menu)
option_menu.add_command(label="Cambiar parámetros de criterio", command=ajustar_parametros_proveedor)
root.config(menu=menu_bar)
tree = ttk.Treeview(root)
tree.grid(row=0, column=0, sticky='nsew')

tree.bind("<Button-3>", mostrar_menu_contextual)
tree.bind("<Control-v>", pegar_desde_portapapeles)
tree.grid(row=0, column=0, sticky='nsew')
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
scrollbar.grid(row=0, column=1, sticky='ns')
tree.configure(yscrollcommand=scrollbar.set)
tree.bind('<Double-1>', on_double_click)
root.config(menu=menu_bar)
encontrar_mejor_proveedor()
scrollbar.grid(row=0, column=0, sticky='nse')

hscrollbar = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
hscrollbar.grid(row=1, column=0, sticky='ew')
tree.configure(xscrollcommand=hscrollbar.set)
tree.bind('<Double-1>', on_double_click)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
if getattr(sys, 'frozen', False):

    application_path = sys._MEIPASS
else:

    application_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(application_path, 'carpeta.ico')
root.iconbitmap(icon_path)
root.mainloop()

