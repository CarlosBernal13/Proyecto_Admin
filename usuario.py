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
    """Abre la ventana para registrar un nuevo usuario/cajero."""
    if usuarios_col is None:
        messagebox.showerror("Error", "No hay conexión a la base de datos."); return

    ventana = ctk.CTkToplevel(root)
    ventana.title("Registro de Nuevo Usuario"); ventana.geometry("350x250"); ventana.resizable(False, False)
    
    e_usuario = tk.StringVar()
    e_pin = tk.StringVar()

    ctk.CTkLabel(ventana, text="Nuevo Usuario:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana, textvariable=e_usuario, width=200).grid(row=0, column=1, padx=10, pady=10)
    
    ctk.CTkLabel(ventana, text="PIN (4+ dígitos):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    ctk.CTkEntry(ventana, textvariable=e_pin, show="*", width=200).grid(row=1, column=1, padx=10, pady=10)

    def registrar():
        usuario = e_usuario.get()
        pin = e_pin.get()
        
        if len(pin) < 4 or not usuario:
            messagebox.showwarning("Advertencia", "El PIN debe ser de 4+ dígitos y el usuario obligatorio."); return
            
        try:
            # 1. Verificar si el usuario ya existe
            if usuarios_col.find_one({"usuario": usuario}):
                messagebox.showerror("Error", "Ese nombre de usuario ya existe."); return
            
            # 2. 🟢 INSERCIÓN MONGODB: Registrar nuevo usuario
            nuevo_usuario = {"usuario": usuario, "pin": pin, "rol": "cajero"} # Rol por defecto
            usuarios_col.insert_one(nuevo_usuario)
            
            messagebox.showinfo("Éxito", f"Usuario '{usuario}' registrado correctamente.")
            ventana.destroy()
                
        except Exception as e:
            messagebox.showerror("Error DB", f"Fallo al registrar usuario: {e}")

    ctk.CTkButton(ventana, text="Registrar Usuario", command=registrar, fg_color="#28a745").grid(row=2, column=0, columnspan=2, pady=15)
    ventana.transient(root); ventana.grab_set(); ventana.wait_window()