# inventario.py

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from bson.objectid import ObjectId 
from bson.regex import Regex # Necesario para la búsqueda con $regex

# --- Funciones de Utilidad (MongoDB) ---

def cargar_inventario(tree, productos_col, filtro=None):
    """Carga los productos de MongoDB al Treeview, aplicando un filtro de búsqueda."""
    
    # 🟢 DEFINICIÓN DE COLUMNAS 🟢
    columnas_tree = ("codigo", "nombre", "stock", "precio_v", "precio_c", "id_db")
    
    tree.config(columns=columnas_tree)
    for item in tree.get_children(): tree.delete(item)
    
    # Configuración de encabezados y anchos
    tree.heading("codigo", text="Código"); tree.column("codigo", width=120, anchor='center')
    tree.heading("nombre", text="Producto"); tree.column("nombre", width=200)
    tree.heading("stock", text="Stock"); tree.column("stock", width=80, anchor='center')
    tree.heading("precio_v", text="P. Venta"); tree.column("precio_v", width=100, anchor='e')
    tree.heading("precio_c", text="P. Compra"); tree.column("precio_c", width=100, anchor='e')
    tree.heading("id_db", text="ID (DB)"); tree.column("id_db", width=80, stretch=tk.NO)
    
    # 🟢 LÓGICA DE FILTRADO MONGODB (CON $REGEX) 🟢
    mongo_query = {}
    if filtro:
        # Busca por código EXACTO o por nombre (insensible a mayúsculas/minúsculas 'i')
        mongo_query = {
            "$or": [
                # 1. Búsqueda por código de barras exacto
                {"codigo_barras": filtro}, 
                # 2. Búsqueda por nombre parcial (insensible a mayúsculas/minúsculas)
                {"nombre": {"$regex": filtro, "$options": "i"}},
            ]
        }

    try:
        # 🟢 CONSULTA A MONGODB CON FILTRO
        for item in productos_col.find(mongo_query):
            mongo_id = str(item.get("_id"))
            
            tree.insert("", "end", iid=mongo_id, values=(
                item.get("codigo_barras", "N/A"),
                item.get("nombre", "Sin Nombre"),
                item.get("stock", 0),
                f"${item.get('precio_venta', 0.0):.2f}", 
                f"${item.get('precio_compra', 0.0):.2f}", 
                mongo_id[:5] + "..."
            ))
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al cargar inventario: {e}")


def eliminar_producto_simulado(tree_inventario, productos_col):
    """Elimina el producto seleccionado de MongoDB."""
    seleccion = tree_inventario.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un producto."); return

    mongo_id = seleccion[0] 
    nombre = tree_inventario.item(seleccion, 'values')[1]
    
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar '{nombre}'?"):
        try:
            # 🟢 OPERACIÓN MONGODB: Eliminar 🟢
            resultado = productos_col.delete_one({"_id": ObjectId(mongo_id)})
            
            if resultado.deleted_count == 1:
                messagebox.showinfo("Éxito", f"Producto {nombre} eliminado correctamente de DB.")
                cargar_inventario(tree_inventario, productos_col)
            else:
                messagebox.showwarning("Advertencia", "Producto no encontrado en la DB.")

        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al eliminar: {e}")


def editar_producto_simulado(tree_inventario, productos_col):
    """Abre un formulario para editar el producto seleccionado."""
    seleccion = tree_inventario.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un producto."); return

    mongo_id = seleccion[0] 
    
    try:
        # 🟢 CONSULTA MONGODB: Cargar datos originales 🟢
        item_original = productos_col.find_one({"_id": ObjectId(mongo_id)})
        if not item_original: raise ValueError("Producto no existe.")
    except Exception as e:
        messagebox.showerror("Error DB", f"No se pudo cargar el producto: {e}"); return
    
    parent_window = tree_inventario.winfo_toplevel() 
    
    ventana_editar = ctk.CTkToplevel(parent_window) 
    ventana_editar.title(f"✏️ Editar: {item_original['nombre']}"); ventana_editar.geometry("350x330"); ventana_editar.resizable(False, False)
    
    # --- Variables de Control ---
    e_nombre = tk.StringVar(value=item_original.get('nombre', ''))
    e_precio_v = tk.StringVar(value=f"{item_original.get('precio_venta', 0.0):.2f}")
    e_precio_c = tk.StringVar(value=f"{item_original.get('precio_compra', 0.0):.2f}")
    e_stock = tk.StringVar(value=str(item_original.get('stock', 0)))
    
    # --- Widgets y Campos (Filas ajustadas) ---
    row = 0
    ctk.CTkLabel(ventana_editar, text="Código de Barras:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkLabel(ventana_editar, text=item_original.get('codigo_barras', 'N/A'), font=('Roboto', 10, 'bold')).grid(row=0, column=1, padx=10, pady=5, sticky="w")
    
    ctk.CTkLabel(ventana_editar, text="Nombre:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_nombre, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    ctk.CTkLabel(ventana_editar, text="Precio Venta:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_precio_v, width=200).grid(row=row-1, column=1, padx=10, pady=5)

    ctk.CTkLabel(ventana_editar, text="Precio Compra:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_precio_c, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    ctk.CTkLabel(ventana_editar, text="Stock Actual:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_stock, width=200).grid(row=row-1, column=1, padx=10, pady=5)

    def guardar_edicion():
        nombre = e_nombre.get().strip()
        try:
            precio_v = float(e_precio_v.get()); precio_c = float(e_precio_c.get()); stock = int(e_stock.get())
        except ValueError:
            messagebox.showerror("Error", "Los campos numéricos deben ser válidos."); return
        if not nombre:
            messagebox.showwarning("Advertencia", "El Nombre es obligatorio."); return

        # 🟢 OPERACIÓN MONGODB: Actualización 🟢
        update_data = {
            "$set": {
                "nombre": nombre, 
                "precio_venta": precio_v, 
                "precio_compra": precio_c, 
                "stock": stock
            }
        }
        
        try:
            productos_col.update_one({"_id": ObjectId(mongo_id)}, update_data)
            messagebox.showinfo("Éxito", f"Producto '{nombre}' actualizado en DB.")
            cargar_inventario(tree_inventario, productos_col); ventana_editar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al actualizar: {e}")

    # 🟢 CTK Button 🟢
    ctk.CTkButton(ventana_editar, text="💾 Guardar Cambios", command=guardar_edicion, fg_color="#0056b3").grid(row=row, column=0, columnspan=2, pady=10)
    
    ventana_editar.transient(ventana_editar.master); ventana_editar.grab_set(); ventana_editar.wait_window()


def agregar_producto_simulado(tree_inventario, productos_col):
    """Abre un formulario para ingresar un nuevo producto en MongoDB."""
    parent_window = tree_inventario.winfo_toplevel() 
    
    ventana_agregar = ctk.CTkToplevel(parent_window)
    ventana_agregar.title("➕ Agregar Nuevo Producto"); ventana_agregar.geometry("350x330"); ventana_agregar.resizable(False, False)
    
    # --- Variables de Control ---
    e_codigo = tk.StringVar(); e_nombre = tk.StringVar(); e_precio_v = tk.StringVar(); 
    e_precio_c = tk.StringVar(); e_stock = tk.StringVar()
    
    # --- Widgets y Campos (Filas ajustadas) ---
    row = 0
    ctk.CTkLabel(ventana_agregar, text="Código de Barras:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_agregar, textvariable=e_codigo, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    ctk.CTkLabel(ventana_agregar, text="Nombre:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_agregar, textvariable=e_nombre, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    ctk.CTkLabel(ventana_agregar, text="Precio Venta:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_agregar, textvariable=e_precio_v, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    ctk.CTkLabel(ventana_agregar, text="Precio Compra:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_agregar, textvariable=e_precio_c, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    ctk.CTkLabel(ventana_agregar, text="Stock Inicial:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_agregar, textvariable=e_stock, width=200).grid(row=row-1, column=1, padx=10, pady=5)

    # ------------------------------------------------
    def guardar_producto():
        codigo = e_codigo.get().strip(); nombre = e_nombre.get().strip()
        try:
            precio_v = float(e_precio_v.get()); precio_c = float(e_precio_c.get()); stock = int(e_stock.get())
        except ValueError:
            messagebox.showerror("Error", "Los campos numéricos deben ser válidos."); return
        if not codigo or not nombre:
            messagebox.showwarning("Advertencia", "El Código y el Nombre son obligatorios."); return
            
        if productos_col.find_one({"codigo_barras": codigo}):
            messagebox.showerror("Error", "Ese código de barras ya existe en la DB."); return

        # 🟢 INSERCIÓN MONGODB 🟢
        nuevo_producto = {
            "codigo_barras": codigo, 
            "nombre": nombre, 
            "precio_venta": precio_v, 
            "precio_compra": precio_c,
            "stock": stock
        }
        try:
            productos_col.insert_one(nuevo_producto)
            messagebox.showinfo("Éxito", f"Producto '{nombre}' agregado a la DB.")
            cargar_inventario(tree_inventario, productos_col); ventana_agregar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al insertar: {e}")

    # 🟢 CONEXIÓN DEL BOTÓN 🟢
    ctk.CTkButton(ventana_agregar, text="💾 Guardar", command=guardar_producto, fg_color="#28a745").grid(row=row, column=0, columnspan=2, pady=15)
    
    ventana_agregar.transient(ventana_agregar.master); ventana_agregar.grab_set(); ventana_agregar.wait_window()


def abrir_inventario_window(pos_window, productos_col, rol):
    """Crea la ventana de gestión de inventario con barra de búsqueda."""
    if not pos_window: messagebox.showerror("Error", "La ventana principal no está abierta."); return

    inventario_window = ctk.CTkToplevel(pos_window) 
    inventario_window.title("📦 Gestión de Inventario"); inventario_window.geometry("1100x600") 
    inventario_window.transient(pos_window); inventario_window.grab_set()

    es_admin = (rol == 'administrador')
    estado_crud = "normal" if es_admin else "disabled"

    # --- CONTENEDOR PRINCIPAL DE ACCIONES Y BÚSQUEDA ---
    frame_top = ctk.CTkFrame(inventario_window, corner_radius=0); frame_top.pack(fill="x", padx=20, pady=10)

    # 🟢 BARRA DE BÚSQUEDA Y FILTRO DINÁMICO 🟢
    frame_busqueda = ctk.CTkFrame(frame_top, fg_color="transparent")
    frame_busqueda.pack(fill="x", pady=(0, 10))
    
    ctk.CTkLabel(frame_busqueda, text="Buscar:", font=('Roboto', 14, 'bold')).pack(side="left", padx=(0, 10))
    
    # 1. Variable de control para el campo de texto
    entry_busqueda_var = tk.StringVar() 
    
    entry_busqueda = ctk.CTkEntry(frame_busqueda, 
                                  placeholder_text="Código o Nombre...", 
                                  width=350, 
                                  font=('Roboto', 14),
                                  textvariable=entry_busqueda_var) # Vinculamos la variable
    entry_busqueda.pack(side="left", padx=5)

    def ejecutar_busqueda(*args):
        """Función ejecutada automáticamente al escribir."""
        filtro = entry_busqueda_var.get().strip()
        cargar_inventario(tree_inventario, productos_col, filtro)

    # 2. Vinculación: Ejecuta ejecutar_busqueda cada vez que la variable cambia ('w' de write)
    entry_busqueda_var.trace_add('write', ejecutar_busqueda)
    
    # Nota: El botón "🔍 Filtrar" se ha eliminado para priorizar la búsqueda dinámica.
    
    # ---------------------------------------------------
    
    # --- CONTENEDOR DE BOTONES CRUD ---
    frame_acciones = ctk.CTkFrame(frame_top, fg_color="transparent"); frame_acciones.pack(fill="x", padx=5, pady=5)
    
    # 🟢 Botones CRUD
    ctk.CTkButton(frame_acciones, text="➕ Agregar Producto", 
                  command=lambda:agregar_producto_simulado(tree_inventario, productos_col),
                  fg_color="#28a745", hover_color="#218838", state=estado_crud).pack(side="left", padx=5, pady=5)
    
    ctk.CTkButton(frame_acciones, text="✏️ Editar Producto", 
                  command=lambda:editar_producto_simulado(tree_inventario, productos_col),
                  fg_color="#007bff", hover_color="#0069d9", state=estado_crud).pack(side="left", padx=5, pady=5)
    
    ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Producto", 
                  command=lambda:eliminar_producto_simulado(tree_inventario, productos_col),
                  fg_color="#dc3545", hover_color="#c82333", state=estado_crud).pack(side="left", padx=5, pady=5)

    ctk.CTkButton(frame_acciones, text="🔄 Recargar", 
                  command=lambda: cargar_inventario(tree_inventario, productos_col), 
                  fg_color="#6c757d", hover_color="#5a6268").pack(side="right", padx=5, pady=5)

    # 🟢 Treeview 🟢
    columnas = ("codigo", "nombre", "stock", "precio_v", "precio_c", "id_db")
    tree_inventario = ttk.Treeview(inventario_window, columns=columnas, show='headings')

    # Configuración de Treeview y carga inicial
    tree_inventario.pack(fill="both", expand=True, padx=20, pady=5)
    
    # Llamamos a cargar_inventario sin filtro inicial para llenar la tabla
    cargar_inventario(tree_inventario, productos_col)

    inventario_window.wait_window()