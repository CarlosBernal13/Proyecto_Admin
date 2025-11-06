import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from bson.objectid import ObjectId
import time

# --- Funciones de Utilidad (MongoDB) ---

def cargar_clientes(tree, clientes_col):
    """Carga los clientes desde la colección de MongoDB al Treeview."""
    for item in tree.get_children(): tree.delete(item)
    
    try:
        # 🟢 CONSULTA A MONGODB
        for i, cliente in enumerate(clientes_col.find()):
            mongo_id = str(cliente.get("_id"))
            saldo = cliente.get("saldo_pendiente", 0.0)
            
            estado_credito = "Sí" if cliente.get("credito") else "No"
            estado_deuda = "Sí" if saldo > 0 else "No"
            
            # Insertar los valores en la tabla
            tree.insert("", "end", iid=mongo_id, values=(
                mongo_id[:5] + "...", # ID acortado para visualización
                cliente.get("nombre", "N/A"),
                cliente.get("telefono", "N/A"),
                estado_credito,
                f"${saldo:.2f}",
                estado_deuda
            ))
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al cargar clientes: {e}")


def eliminar_cliente_simulado(tree_clientes, clientes_col):
    """Elimina el cliente seleccionado de MongoDB."""
    seleccion = tree_clientes.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un cliente."); return

    # 🟢 CORRECCIÓN: Obtener el ID de MongoDB (guardado en el 'iid') 🟢
    mongo_id = seleccion[0]
    nombre = tree_clientes.item(seleccion, 'values')[1]
    
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar a {nombre}?"):
        try:
            # Usamos ObjectId() para convertir el string del ID al tipo que MongoDB espera
            clientes_col.delete_one({"_id": ObjectId(mongo_id)}) 
            messagebox.showinfo("Éxito", f"Cliente {nombre} eliminado de la DB.")
            cargar_clientes(tree_clientes, clientes_col)
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al eliminar: {e}")

def editar_cliente_simulado(tree_clientes, clientes_col):
    """Abre un formulario para editar el cliente seleccionado."""
    seleccion = tree_clientes.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un cliente."); return

    # 1. Obtener datos iniciales y mongo_id
    mongo_id = seleccion[0]
    
    try:
        cliente_original = clientes_col.find_one({"_id": ObjectId(mongo_id)})
        if not cliente_original: raise ValueError("Cliente no existe.")
    except Exception as e:
        messagebox.showerror("Error DB", f"No se pudo cargar el cliente para editar: {e}"); return
        
    nombre_cliente = cliente_original.get('nombre')
    id_visible = mongo_id[:5] + "..." 
    
    parent_window = tree_clientes.winfo_toplevel()
    ventana_editar = ctk.CTkToplevel(parent_window)
    ventana_editar.title(f"✏️ Editar: {nombre_cliente}"); ventana_editar.geometry("350x330"); ventana_editar.resizable(False, False)
    
    # --- Variables de Control (Estas variables están en el scope principal) ---
    e_nombre = tk.StringVar(value=nombre_cliente)
    e_telefono = tk.StringVar(value=cliente_original['telefono'])
    e_credito = tk.BooleanVar(value=cliente_original.get('credito', False))
    e_saldo = tk.StringVar(value=f"{cliente_original.get('saldo_pendiente', 0.0):.2f}")
    
    # --- Widgets y Campos ---
    # ... (Widgets de formulario con las variables e_nombre, e_telefono, etc.) ...
    ctk.CTkLabel(ventana_editar, text="ID Cliente:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkLabel(ventana_editar, text=id_visible, font=('Roboto', 10, 'bold')).grid(row=0, column=1, padx=10, pady=10, sticky="w")
    ctk.CTkLabel(ventana_editar, text="Nombre:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_editar, textvariable=e_nombre, width=200).grid(row=1, column=1, padx=10, pady=10)
    ctk.CTkLabel(ventana_editar, text="Teléfono:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_editar, textvariable=e_telefono, width=200).grid(row=2, column=1, padx=10, pady=10)
    ctk.CTkLabel(ventana_editar, text="Saldo Pendiente:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_editar, textvariable=e_saldo, width=200).grid(row=3, column=1, padx=10, pady=10)
    ctk.CTkLabel(ventana_editar, text="Habilitar Crédito:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkCheckBox(ventana_editar, text="Crédito", variable=e_credito).grid(row=4, column=1, padx=10, pady=10, sticky="w")

    
    # 2. DEFINICIÓN ÚNICA DE LA FUNCIÓN DE GUARDADO
    def guardar_edicion_final():
        nombre = e_nombre.get().strip(); telefono = e_telefono.get().strip()
        try:
            saldo = float(e_saldo.get())
        except ValueError:
            messagebox.showerror("Error", "El Saldo debe ser un número válido."); return
        if not nombre or not telefono:
            messagebox.showwarning("Advertencia", "Nombre y Teléfono son obligatorios."); return

        # 🟢 ACTUALIZACIÓN MONGODB 🟢
        update_data = {
            "$set": {
                "nombre": nombre,
                "telefono": telefono,
                "credito": e_credito.get(),
                "saldo_pendiente": saldo
            }
        }
        try:
            clientes_col.update_one({"_id": ObjectId(mongo_id)}, update_data)
            messagebox.showinfo("Éxito", f"Cliente {nombre} actualizado en DB.")
            cargar_clientes(tree_clientes, clientes_col); ventana_editar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al actualizar: {e}")

    # 3. CONEXIÓN DEL BOTÓN (Usamos la función definida arriba)
    # 🚨 Eliminamos el primer botón y la segunda definición.
    ctk.CTkButton(ventana_editar, text="💾 Guardar Cambios", command=guardar_edicion_final, fg_color="#007bff").grid(row=5, column=0, columnspan=2, pady=15)
    
    ventana_editar.transient(ventana_editar.master); ventana_editar.grab_set(); ventana_editar.wait_window()

def agregar_cliente_simulado(tree_clientes, clientes_col):
    """Abre un formulario para ingresar un nuevo cliente en MongoDB."""
    parent_window = tree_clientes.winfo_toplevel() 
    
    ventana_agregar = ctk.CTkToplevel(parent_window)
    ventana_agregar.title("➕ Agregar Nuevo Cliente"); ventana_agregar.geometry("350x330"); ventana_agregar.resizable(False, False)
    
    # --- Variables de Control ---
    e_nombre = tk.StringVar(); e_telefono = tk.StringVar(); e_credito = tk.BooleanVar(value=False)
    e_saldo = tk.StringVar(value="0.00")
    
    # --- Widgets y Campos (CORREGIDOS) ---
    ctk.CTkLabel(ventana_agregar, text="Nombre:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_nombre, width=200).grid(row=0, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_agregar, text="Teléfono:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_telefono, width=200).grid(row=1, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_agregar, text="Saldo Inicial:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana_agregar, textvariable=e_saldo, width=200).grid(row=2, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana_agregar, text="Habilitar Crédito:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkCheckBox(ventana_agregar, text="Crédito", variable=e_credito).grid(row=3, column=1, padx=10, pady=10, sticky="w")

    def guardar_producto():
        nombre = e_nombre.get().strip(); telefono = e_telefono.get().strip()
        try:
            saldo = float(e_saldo.get())
        except ValueError:
            messagebox.showerror("Error", "El Saldo debe ser un número válido."); return
        if not nombre or not telefono:
            messagebox.showwarning("Advertencia", "Nombre y Teléfono son obligatorios."); return

        # 🟢 INSERCIÓN MONGODB 🟢
        nuevo_cliente = {
            "nombre": nombre,
            "telefono": telefono,
            "credito": e_credito.get(),
            "saldo_pendiente": saldo,
            "creacion_fecha": time.time()
        }
        try:
            clientes_col.insert_one(nuevo_cliente)
            messagebox.showinfo("Éxito", f"Cliente {nombre} agregado a la DB.")
            cargar_clientes(tree_clientes, clientes_col); ventana_agregar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al insertar: {e}")

    ctk.CTkButton(ventana_agregar, text="💾 Guardar", command=guardar_producto, fg_color="#28a745").grid(row=4, column=0, columnspan=2, pady=15)
    ventana_agregar.transient(ventana_agregar.master); ventana_agregar.grab_set(); ventana_agregar.wait_window()


def abrir_clientes_window(pos_window, clientes_col):
    """Crea la ventana de administración de clientes."""
    if not pos_window: return

    clientes_window = ctk.CTkToplevel(pos_window)
    clientes_window.title("👤 Administración de Clientes"); clientes_window.geometry("1000x600")
    clientes_window.transient(pos_window); clientes_window.grab_set()

    frame_acciones = ctk.CTkFrame(clientes_window, corner_radius=0); frame_acciones.pack(fill="x", padx=20, pady=10)

    columnas = ("id", "nombre", "telefono", "credito", "saldo_pendiente", "debe")
    tree_clientes = ttk.Treeview(clientes_window, columns=columnas, show='headings')

    # CONEXIÓN DE BOTONES CRUD
    ctk.CTkButton(frame_acciones, text="➕ Agregar Cliente", 
                  command=lambda: agregar_cliente_simulado(tree_clientes, clientes_col),
                  fg_color="#28a745").pack(side="left", padx=10)
    ctk.CTkButton(frame_acciones, text="✏️ Editar Cliente", 
                  command=lambda: editar_cliente_simulado(tree_clientes, clientes_col),
                  fg_color="#007bff").pack(side="left", padx=10)
    ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Cliente", 
                  command=lambda: eliminar_cliente_simulado(tree_clientes, clientes_col), 
                  fg_color="#dc3545").pack(side="left", padx=10)

    ctk.CTkButton(frame_acciones, text="🔄 Recargar", 
                  command=lambda: cargar_clientes(tree_clientes, clientes_col), 
                  fg_color="#6c757d").pack(side="right", padx=10)

    # 🟢 Treeview y Configuración (ttk) 🟢
    tree_clientes.heading("id", text="ID"); tree_clientes.heading("nombre", text="Nombre")
    tree_clientes.heading("telefono", text="Teléfono"); tree_clientes.heading("credito", text="Crédito")
    tree_clientes.heading("saldo_pendiente", text="Saldo Pendiente"); tree_clientes.heading("debe", text="Debe")

    tree_clientes.column("id", width=50, anchor='center'); tree_clientes.column("nombre", width=250)
    tree_clientes.column("telefono", width=150); tree_clientes.column("credito", width=80, anchor='center')
    tree_clientes.column("saldo_pendiente", width=120, anchor='e'); tree_clientes.column("debe", width=80, anchor='center')

    tree_clientes.pack(fill="both", expand=True, padx=20, pady=10)
    cargar_clientes(tree_clientes, clientes_col)

    clientes_window.wait_window()