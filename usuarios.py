import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from pymongo import MongoClient # ⬅️ NUEVA IMPORTACIÓN
from bson.objectid import ObjectId 

# --- Nuevas Funciones de Gestión de Usuarios ---

def abrir_modificar_contrasena(usuarios_col, root):
    """Abre la ventana para que el usuario cambie su PIN/Contraseña."""
    if usuarios_col is None:
        messagebox.showerror("Error", "No hay conexión a la base de datos."); return

    ventana = ctk.CTkToplevel(root)
    ventana.title("Modificar Contraseña"); ventana.geometry("350x250"); ventana.resizable(False, False)
    
    e_usuario = tk.StringVar()
    e_pin_antiguo = tk.StringVar()
    e_pin_nuevo = tk.StringVar()

    ctk.CTkLabel(ventana, text="Usuario:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana, textvariable=e_usuario, width=200).grid(row=0, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana, text="PIN Antiguo:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana, textvariable=e_pin_antiguo, show="*", width=200).grid(row=1, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana, text="PIN Nuevo:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana, textvariable=e_pin_nuevo, show="*", width=200).grid(row=2, column=1, padx=10, pady=10)

    def guardar_cambio():
        usuario = e_usuario.get()
        pin_antiguo = e_pin_antiguo.get()
        pin_nuevo = e_pin_nuevo.get()
        
        if len(pin_nuevo) < 4:
            messagebox.showwarning("Error", "El nuevo PIN debe tener al menos 4 caracteres."); return
            
        try:
            # 1. Verificar credenciales antiguas
            filtro = {"usuario": usuario, "pin": pin_antiguo}
            
            # 2. Actualizar la contraseña
            resultado = usuarios_col.update_one(filtro, {"$set": {"pin": pin_nuevo}})
            
            if resultado.matched_count == 1:
                messagebox.showinfo("Éxito", "Contraseña modificada correctamente.")
                ventana.destroy()
            else:
                messagebox.showerror("Error", "Usuario o PIN antiguo incorrectos.")
                
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al modificar contraseña: {e}")

    ctk.CTkButton(ventana, text="Guardar Nuevo PIN", command=guardar_cambio, fg_color="#007bff").grid(row=3, column=0, columnspan=2, pady=15)
    ventana.transient(root); ventana.grab_set(); ventana.wait_window()


def abrir_registro_usuario(usuarios_col, root):
    """Abre la ventana para registrar un nuevo usuario/cajero con campos completos, incluyendo Rol."""
    if usuarios_col is None:
        messagebox.showerror("Error", "No hay conexión a la base de datos."); return

    ventana = ctk.CTkToplevel(root)
    ventana.title("Registro de Nuevo Usuario"); 
    ventana.geometry("350x490"); # Aumentamos el tamaño
    ventana.resizable(False, False)
    
    # --- Variables de Control ---
    e_nombres = tk.StringVar()
    e_apellido_p = tk.StringVar()
    e_apellido_m = tk.StringVar()
    e_telefono = tk.StringVar()
    e_usuario = tk.StringVar()
    e_pin = tk.StringVar()
    e_rol = ctk.StringVar(value="cajero") # ⬅️ Variable para el rol (valor por defecto)

    # --- Widgets y Campos ---
    row = 0
    
    # Nombres
    ctk.CTkLabel(ventana, text="Nombre(s):").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana, textvariable=e_nombres, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Apellido Paterno
    ctk.CTkLabel(ventana, text="Ape. Paterno:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana, textvariable=e_apellido_p, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Apellido Materno
    ctk.CTkLabel(ventana, text="Ape. Materno:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana, textvariable=e_apellido_m, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Teléfono
    ctk.CTkLabel(ventana, text="Teléfono:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana, textvariable=e_telefono, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Usuario (Login)
    ctk.CTkLabel(ventana, text="Usuario (Login):").grid(row=row, column=0, padx=10, pady=10, sticky="w"); row+=1
    ctk.CTkEntry(ventana, textvariable=e_usuario, width=200).grid(row=row-1, column=1, padx=10, pady=10)
    
    # Contraseña/PIN
    ctk.CTkLabel(ventana, text="Contraseña/PIN:").grid(row=row, column=0, padx=10, pady=10, sticky="w"); row+=1
    ctk.CTkEntry(ventana, textvariable=e_pin, show="*", width=200).grid(row=row-1, column=1, padx=10, pady=10)

    # 🟢 Selección de Rol 🟢
    ctk.CTkLabel(ventana, text="Rol:").grid(row=row, column=0, padx=10, pady=10, sticky="w"); row+=1
    ctk.CTkComboBox(ventana, 
                    values=["cajero", "administrador"], 
                    variable=e_rol, 
                    width=200).grid(row=row-1, column=1, padx=10, pady=10)


    def registrar():
        nombres = e_nombres.get().strip()
        apellido_p = e_apellido_p.get().strip()
        apellido_m = e_apellido_m.get().strip()
        telefono = e_telefono.get().strip()
        usuario = e_usuario.get().strip()
        pin = e_pin.get().strip()
        rol = e_rol.get() # ⬅️ Obtener el valor del rol
        
        if len(pin) < 4 or not usuario or not nombres:
            messagebox.showwarning("Advertencia", "Nombre, Usuario y PIN (4+ dígitos) son obligatorios."); return
            
        try:
            if usuarios_col.find_one({"usuario": usuario}):
                messagebox.showerror("Error", "Ese nombre de usuario ya existe."); return
            
            # 🟢 INSERCIÓN MONGODB: Incluyendo el campo 'rol' 🟢
            nuevo_usuario = {
                "nombres": nombres,
                "apellido_paterno": apellido_p,
                "apellido_materno": apellido_m,
                "telefono": telefono,
                "usuario": usuario,
                "pin": pin, 
                "rol": rol # ⬅️ Guardamos el rol
            }
            usuarios_col.insert_one(nuevo_usuario)
            
            messagebox.showinfo("Éxito", f"Usuario '{nombres}' registrado como '{rol}'.")
            ventana.destroy()
                
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al registrar usuario: {e}")

    ctk.CTkButton(ventana, text="Registrar Usuario", command=registrar, fg_color="#28a745").grid(row=row, column=0, columnspan=2, pady=15)
    ventana.transient(root); ventana.grab_set(); ventana.wait_window()

def cargar_usuarios_gestion(tree, usuarios_col):
    """Carga los usuarios de MongoDB al Treeview de gestión."""
    for item in tree.get_children(): tree.delete(item)
    
    try:
        # 🟢 CONSULTA A MONGODB: Listar todos los usuarios 🟢
        for item in usuarios_col.find():
            mongo_id = str(item.get("_id"))
            
            # Se listan solo los campos necesarios
            tree.insert("", "end", iid=mongo_id, values=(
                item.get("usuario", "N/A"),
                item.get("rol", "cajero"),
                item.get("nombres", ""),
                item.get("apellido_paterno", ""),
                item.get("telefono", ""),
                mongo_id[:5] + "..."
            ))
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al cargar usuarios: {e}")

def eliminar_usuario(tree_usuarios, usuarios_col):
    """Elimina el usuario seleccionado de MongoDB."""
    seleccion = tree_usuarios.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un usuario."); return

    mongo_id = seleccion[0]
    nombre_usuario = tree_usuarios.item(seleccion, 'values')[0]
    
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar al usuario {nombre_usuario}?"):
        try:
            # 🟢 OPERACIÓN MONGODB: Eliminar un documento por _id 🟢
            usuarios_col.delete_one({"_id": ObjectId(mongo_id)})
            messagebox.showinfo("Éxito", f"Usuario {nombre_usuario} eliminado de la DB.")
            cargar_usuarios_gestion(tree_usuarios, usuarios_col)
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al eliminar: {e}")

def abrir_gestion_usuarios_window(pos_window, usuarios_col):
    """Crea la ventana de gestión CRUD para usuarios (visible solo para admins)."""
    if usuarios_col is None:
        messagebox.showerror("Error DB", "No hay conexión a la base de datos de usuarios.")
        return

    gestion_window = ctk.CTkToplevel(pos_window) 
    gestion_window.title("🔑 Administración de Usuarios")
    gestion_window.geometry("800x500") 
    gestion_window.transient(pos_window); gestion_window.grab_set()

    # --- Contenedor Principal ---
    frame_main = ctk.CTkFrame(gestion_window, corner_radius=0)
    frame_main.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Botones CRUD ---
    frame_acciones = ctk.CTkFrame(frame_main, fg_color="transparent")
    frame_acciones.pack(fill="x", pady=5)
    
    # ⚠️ NOTA: El botón 'Agregar Usuario' ya existe en el login, pero podemos ponerlo aquí también
    ctk.CTkButton(frame_acciones, text="➕ Nuevo Usuario", command=lambda: abrir_registro_usuario(usuarios_col, gestion_window), fg_color="#28a745").pack(side="left", padx=5)
    
    ctk.CTkButton(frame_acciones, text="✏️ Editar Usuario", fg_color="#007bff", command=lambda: editar_usuario(tree_usuarios, usuarios_col)).pack(side="left", padx=5) # Función de edición pendiente
    
    ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Usuario", 
                  command=lambda: eliminar_usuario(tree_usuarios, usuarios_col), 
                  fg_color="#dc3545").pack(side="left", padx=5)
    
    ctk.CTkButton(frame_acciones, text="🔄 Recargar", command=lambda: cargar_usuarios_gestion(tree_usuarios, usuarios_col), fg_color="#6c757d").pack(side="right", padx=5)

    # --- Treeview ---
    columnas = ("usuario", "rol", "nombres", "apellidos", "telefono", "id_db")
    tree_usuarios = ttk.Treeview(frame_main, columns=columnas, show='headings')

    tree_usuarios.heading("usuario", text="Usuario"); tree_usuarios.column("usuario", width=100)
    tree_usuarios.heading("rol", text="Rol"); tree_usuarios.column("rol", width=80, anchor='center')
    tree_usuarios.heading("nombres", text="Nombres"); tree_usuarios.column("nombres", width=120)
    tree_usuarios.heading("apellidos", text="Apellidos"); tree_usuarios.column("apellidos", width=120)
    tree_usuarios.heading("telefono", text="Teléfono"); tree_usuarios.column("telefono", width=100)
    tree_usuarios.heading("id_db", text="ID (DB)"); tree_usuarios.column("id_db", width=80, stretch=tk.NO)

    tree_usuarios.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Carga inicial de datos
    cargar_usuarios_gestion(tree_usuarios, usuarios_col)

    gestion_window.wait_window()

def editar_usuario(tree_usuarios, usuarios_col):
    """Abre un formulario para editar el usuario seleccionado."""
    seleccion = tree_usuarios.selection()
    if not seleccion: messagebox.showwarning("Selección", "Debes seleccionar un usuario para editar."); return

    mongo_id = seleccion[0]
    
    try:
        # 🟢 CONSULTA MONGODB: Cargar datos originales 🟢
        usuario_original = usuarios_col.find_one({"_id": ObjectId(mongo_id)})
        if not usuario_original: raise ValueError("Usuario no existe.")
    except Exception as e:
        messagebox.showerror("Error DB", f"No se pudo cargar el usuario para editar: {e}"); return
    
    
    parent_window = tree_usuarios.winfo_toplevel()
    ventana_editar = ctk.CTkToplevel(parent_window)
    ventana_editar.title(f"✏️ Editar: {usuario_original['usuario']}"); 
    ventana_editar.geometry("350x490"); 
    ventana_editar.resizable(False, False)
    
    # --- Variables de Control ---
    e_nombres = tk.StringVar(value=usuario_original.get('nombres', ''))
    e_apellido_p = tk.StringVar(value=usuario_original.get('apellido_paterno', ''))
    e_apellido_m = tk.StringVar(value=usuario_original.get('apellido_materno', ''))
    e_telefono = tk.StringVar(value=usuario_original.get('telefono', ''))
    e_usuario = tk.StringVar(value=usuario_original.get('usuario', ''))
    e_rol = ctk.StringVar(value=usuario_original.get('rol', 'cajero')) 
    
    # --- Widgets y Campos ---
    row = 0
    
    # ID (No editable)
    ctk.CTkLabel(ventana_editar, text="ID Usuario:").grid(row=row, column=0, padx=10, pady=5, sticky="w")
    ctk.CTkLabel(ventana_editar, text=str(mongo_id)[:5] + "...", font=('Roboto', 10, 'bold')).grid(row=row, column=1, padx=10, pady=5, sticky="w"); row+=1
    
    # Nombres
    ctk.CTkLabel(ventana_editar, text="Nombre(s):").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_nombres, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Apellido Paterno
    ctk.CTkLabel(ventana_editar, text="Ape. Paterno:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_apellido_p, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Apellido Materno
    ctk.CTkLabel(ventana_editar, text="Ape. Materno:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_apellido_m, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Teléfono
    ctk.CTkLabel(ventana_editar, text="Teléfono:").grid(row=row, column=0, padx=10, pady=5, sticky="w"); row+=1
    ctk.CTkEntry(ventana_editar, textvariable=e_telefono, width=200).grid(row=row-1, column=1, padx=10, pady=5)
    
    # Usuario (Login) - No editable para mantener la integridad de la clave
    ctk.CTkLabel(ventana_editar, text="Usuario (Login):").grid(row=row, column=0, padx=10, pady=10, sticky="w"); row+=1
    ctk.CTkLabel(ventana_editar, text=e_usuario.get(), font=('Roboto', 10, 'bold')).grid(row=row-1, column=1, padx=10, pady=10, sticky="w")
    
    # 🟢 Selección de Rol 🟢
    ctk.CTkLabel(ventana_editar, text="Rol:").grid(row=row, column=0, padx=10, pady=10, sticky="w"); row+=1
    ctk.CTkComboBox(ventana_editar, 
                    values=["cajero", "administrador"], 
                    variable=e_rol, 
                    width=200).grid(row=row-1, column=1, padx=10, pady=10)


    def guardar_edicion():
        nombres = e_nombres.get().strip()
        apellido_p = e_apellido_p.get().strip()
        apellido_m = e_apellido_m.get().strip()
        telefono = e_telefono.get().strip()
        rol = e_rol.get()
        
        if not nombres:
            messagebox.showwarning("Advertencia", "El Nombre es obligatorio."); return
            
        # 🟢 ACTUALIZACIÓN MONGODB 🟢
        update_data = {
            "$set": {
                "nombres": nombres,
                "apellido_paterno": apellido_p,
                "apellido_materno": apellido_m,
                "telefono": telefono,
                "rol": rol
            }
        }
        try:
            usuarios_col.update_one({"_id": ObjectId(mongo_id)}, update_data)
            messagebox.showinfo("Éxito", f"Usuario {nombres} actualizado en DB.")
            cargar_usuarios_gestion(tree_usuarios, usuarios_col)
            ventana_editar.destroy()
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al actualizar: {e}")

    ctk.CTkButton(ventana_editar, text="💾 Guardar Cambios", command=guardar_edicion, fg_color="#007bff").grid(row=row, column=0, columnspan=2, pady=15)
    ventana_editar.transient(ventana_editar.master); ventana_editar.grab_set(); ventana_editar.wait_window()