# inventario.py (Migrado a MongoDB)

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from bson.objectid import ObjectId # Necesario para manejar IDs de MongoDB

# --- Funciones de Utilidad (MongoDB) ---

def cargar_inventario(tree, productos_col):
    """Carga los productos desde la colección de MongoDB al Treeview."""
    for item in tree.get_children(): tree.delete(item)
    
    try:
        # 🟢 CONSULTA A MONGODB
        for item in productos_col.find():
            mongo_id = str(item.get("_id"))
            
            # Usar valores del documento de MongoDB
            codigo = item.get("codigo_barras", "N/A")
            nombre = item.get("nombre", "Sin Nombre")
            precio = item.get("precio", 0.0)
            stock = item.get("stock", 0) 
            
            # Insertar el ID completo en el iid y el ID acortado en la columna
            tree.insert("", "end", iid=mongo_id, values=(
                codigo, 
                nombre, 
                stock, 
                f"${precio:.2f}", 
                mongo_id[:5] + "..."
            ))
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al cargar inventario: {e}")


def eliminar_producto_simulado(tree_inventario, productos_col):
    """Elimina el producto seleccionado de MongoDB."""
    seleccion = tree_inventario.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un producto."); return

    # 🟢 OBTENER ID CORRECTO: Usar el iid que contiene el ObjectId completo
    mongo_id = seleccion[0] 
    nombre = tree_inventario.item(seleccion, 'values')[1]
    
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar '{nombre}'?"):
        try:
            # 🟢 OPERACIÓN MONGODB: Eliminar un documento por _id 🟢
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

    # 🟢 OBTENER ID CORRECTO
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
    e_codigo = tk.StringVar(value=item_original.get('codigo_barras', ''))
    e_nombre = tk.StringVar(value=item_original.get('nombre', ''))
    e_precio = tk.StringVar(value=f"{item_original.get('precio', 0.0):.2f}")
    e_stock = tk.StringVar(value=str(item_original.get('stock', 0)))
    
    # --- Widgets y Campos ---
    ctk.CTkLabel(ventana_editar, text="Código de Barras:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    # Mostrar el código (no editable)
    ctk.CTkLabel(ventana_editar, text=item_original.get('codigo_barras', 'N/A'), font=('Roboto', 10, 'bold')).grid(row=0, column=1, padx=10, pady=10, sticky="w")
    
    ctk.CTkLabel(ventana_editar, text="Nombre:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_editar, textvariable=e_nombre, width=200).grid(row=1, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_editar, text="Precio:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_editar, textvariable=e_precio, width=200).grid(row=2, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_editar, text="Stock Actual:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_editar, textvariable=e_stock, width=200).grid(row=3, column=1, padx=10, pady=10)

    def guardar_edicion():
        nombre = e_nombre.get().strip()
        try:
            precio = float(e_precio.get()); stock = int(e_stock.get())
        except ValueError:
            messagebox.showerror("Error", "El Precio y el Stock deben ser números válidos."); return
        if not nombre:
            messagebox.showwarning("Advertencia", "El Nombre es obligatorio."); return

        # 🟢 OPERACIÓN MONGODB: Actualización 🟢
        update_data = {"$set": {"nombre": nombre, "precio": precio, "stock": stock}}
        
        try:
            productos_col.update_one({"_id": ObjectId(mongo_id)}, update_data)
            messagebox.showinfo("Éxito", f"Producto '{nombre}' actualizado en DB.")
            cargar_inventario(tree_inventario, productos_col); ventana_editar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al actualizar: {e}")

    # 🟢 CTK Button 🟢
    ctk.CTkButton(ventana_editar, text="💾 Guardar Cambios", command=guardar_edicion, fg_color="#0056b3").grid(row=4, column=0, columnspan=2, pady=10)
    
    ventana_editar.transient(ventana_editar.master); ventana_editar.grab_set(); ventana_editar.wait_window()


def agregar_producto_simulado(tree_inventario, productos_col):
    """Abre un formulario para ingresar un nuevo producto en MongoDB."""
    parent_window = tree_inventario.winfo_toplevel() 
    
    ventana_agregar = ctk.CTkToplevel(parent_window)
    ventana_agregar.title("➕ Agregar Nuevo Producto"); ventana_agregar.geometry("350x330"); ventana_agregar.resizable(False, False)
    
    # --- Variables de Control ---
    e_codigo = tk.StringVar(); e_nombre = tk.StringVar(); e_precio = tk.StringVar(); e_stock = tk.StringVar()
    
    # --- Widgets y Campos ---
    ctk.CTkLabel(ventana_agregar, text="Código de Barras:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_codigo, width=200).grid(row=0, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_agregar, text="Nombre:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_nombre, width=200).grid(row=1, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_agregar, text="Precio:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_precio, width=200).grid(row=2, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_agregar, text="Stock Inicial:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_stock, width=200).grid(row=3, column=1, padx=10, pady=10)

    def guardar_producto():
        codigo = e_codigo.get().strip(); nombre = e_nombre.get().strip()
        try:
            precio = float(e_precio.get()); stock = int(e_stock.get())
        except ValueError:
            messagebox.showerror("Error", "El Precio y el Stock deben ser números válidos."); return
        if not codigo or not nombre:
            messagebox.showwarning("Advertencia", "El Código y el Nombre son obligatorios."); return
            
        # Opcional: Verificar si el código de barras ya existe
        if productos_col.find_one({"codigo_barras": codigo}):
            messagebox.showerror("Error", "Ese código de barras ya existe en la DB."); return

        # 🟢 INSERCIÓN MONGODB 🟢
        nuevo_producto = {
            "codigo_barras": codigo, 
            "nombre": nombre, 
            "precio": precio, 
            "stock": stock
        }
        try:
            productos_col.insert_one(nuevo_producto)
            messagebox.showinfo("Éxito", f"Producto '{nombre}' agregado a la DB.")
            cargar_inventario(tree_inventario, productos_col); ventana_agregar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al insertar: {e}")

    ctk.CTkButton(ventana_agregar, text="💾 Guardar", command=guardar_producto, fg_color="#28a745").grid(row=4, column=0, columnspan=2, pady=15)
    
    ventana_agregar.transient(ventana_agregar.master); ventana_agregar.grab_set(); ventana_agregar.wait_window()


def abrir_inventario_window(pos_window, productos_col):
    """Crea la ventana de gestión de inventario."""
    if not pos_window: 
        messagebox.showerror("Error", "La ventana principal no está abierta."); return

    inventario_window = ctk.CTkToplevel(pos_window) 
    inventario_window.title("📦 Gestión de Inventario"); inventario_window.geometry("1000x600")
    inventario_window.transient(pos_window); inventario_window.grab_set()

    frame_acciones = ctk.CTkFrame(inventario_window, corner_radius=0); frame_acciones.pack(fill="x", padx=10, pady=10)

    columnas = ("codigo", "nombre", "stock", "precio", "id_db")
    tree_inventario = ttk.Treeview(inventario_window, columns=columnas, show='headings')

    # 🟢 CTK Buttons (Ahora llaman a las funciones que usan la colección de DB) 🟢
    ctk.CTkButton(frame_acciones, text="➕ Agregar Producto", 
                  command=lambda:agregar_producto_simulado(tree_inventario, productos_col),
                  fg_color="#28a745", hover_color="#218838").pack(side="left", padx=10, pady=5)
    
    ctk.CTkButton(frame_acciones, text="✏️ Editar Producto", 
                  command=lambda:editar_producto_simulado(tree_inventario, productos_col),
                  fg_color="#007bff", hover_color="#0069d9").pack(side="left", padx=10, pady=5)
    
    ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Producto", 
                  command=lambda:eliminar_producto_simulado(tree_inventario, productos_col),
                  fg_color="#dc3545", hover_color="#c82333").pack(side="left", padx=10, pady=5)

    ctk.CTkButton(frame_acciones, text="🔄 Recargar", 
                  command=lambda: cargar_inventario(tree_inventario, productos_col),
                  fg_color="#6c757d", hover_color="#5a6268").pack(side="right", padx=10, pady=5)

    # Configuración del Treeview (ttk)
    tree_inventario.heading("codigo", text="Código"); tree_inventario.heading("nombre", text="Producto")
    tree_inventario.heading("stock", text="Stock"); tree_inventario.heading("precio", text="Precio Venta")
    tree_inventario.heading("id_db", text="ID (MongoDB)")

    tree_inventario.column("codigo", width=100, anchor='center'); tree_inventario.column("nombre", width=300)
    tree_inventario.column("stock", width=80, anchor='center'); tree_inventario.column("precio", width=100, anchor='e')
    tree_inventario.column("id_db", width=100, stretch=tk.NO)

    tree_inventario.pack(fill="both", expand=True, padx=10, pady=5)
    cargar_inventario(tree_inventario, productos_col)

    inventario_window.wait_window()