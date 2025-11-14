import subprocess
from tkinter import messagebox

def login():
    """Valida el usuario y abre el sistema de inventario si es administrador."""
    global root, usuario_global, rol_global
    usuario_ingresado = entry_usuario.get().strip()
    pin = entry_pin.get().strip()
    
    if usuarios_col is None:
        messagebox.showerror("Error", "No hay conexión a la base de datos para iniciar sesión.")
        return

    try:
        user = usuarios_col.find_one({"usuario": usuario_ingresado, "pin": pin})
        
        if user:
            rol_encontrado = user.get("rol", "").lower()

            if rol_encontrado != "administrador":
                messagebox.showwarning(
                    "Acceso Restringido", 
                    "Solo los administradores pueden acceder al sistema de inventario.\n"
                    f"Tu rol actual es: {rol_encontrado.capitalize()}"
                )
                return
            
            # 🟢 Si el rol es administrador, abrimos el sistema Flask
            messagebox.showinfo("Acceso concedido", "Bienvenido al sistema de inventario.")
            root.destroy()  # Cierra la ventana de login
            
            # Ejecutar el archivo Flask (app_inventario.py)
            subprocess.Popen(["python", "app_inventario.py"])

        else:
            messagebox.showerror("Error de Autenticación", "Usuario o PIN incorrectos.")
            
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo en la autenticación: {e}")
