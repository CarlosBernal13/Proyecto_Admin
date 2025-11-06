import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import inventario
import ticket
import time
import random
import clientes
import usuario
from pymongo import MongoClient # ⬅️ NUEVA IMPORTACIÓN
from bson.regex import Regex

# --- 1. CONFIGURACIÓN DE DATOS GLOBALES (AHORA SON COLECCIONES) ---

# ⚠️ Reemplaza esta URI con tu cadena de conexión real de MongoDB Atlas
MONGO_URI = "mongodb+srv://Carlosbernal:CarBer1998@cluster0.z31tlvd.mongodb.net/?appName=Cluster0"
DB_NAME = "Tienda"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    productos_col = db['productos']
    ventas_col = db['ventas']        # Historial de ventas
    clientes_col = db['clientes']
    usuarios_col = db['usuarios']    # Para el login
    
    print("✅ Conexión a MongoDB exitosamente.")
except Exception as e:
    messagebox.showerror("Error de Conexión DB", f"No se pudo conectar a MongoDB: {e}")
    # Si la conexión falla, las colecciones serán None, lo que afectará todas las funciones.
    productos_col = None
    ventas_col = None
    clientes_col = None
    usuarios_col = None
    
carrito = []
total_compra = 0.00

# --- Variables de Interfaz Globales ---
entry_codigo = None
lista_productos = None
lbl_total_valor = None
pos_window = None
root = None # Añadida 'root' aquí para claridad
historial_ventas_simulado = []

# ======================================================================================
# BLOQUE DE FUNCIONES (TODAS DEFINIDAS ANTES DE SER LLAMADAS)
# ======================================================================================

# --- Funciones de Lógica de Venta ---

def finalizar_venta():
    global carrito, total_compra
    
    if not carrito:
        messagebox.showwarning("Venta Vacía", "No hay productos en el carrito para cobrar."); return
    
    if ventas_col is None or productos_col is None:
        messagebox.showerror("Error", "No se puede guardar la venta. Conexión DB perdida."); return

    compra_id = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999)) 
    
    productos_vendidos = [item.copy() for item in carrito] # Copia de productos
    
    documento_ticket = {
        "transaccion_id": compra_id, # Usaremos este campo como identificador
        "fecha_hora": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cajero": "cajero01", 
        "total": total_compra,
        "productos": productos_vendidos,
        "metodo_pago": "Efectivo"
    }

    try:
        # 🟢 INSERCIÓN EN MONGODB: Guardar la transacción 🟢
        ventas_col.insert_one(documento_ticket)
        
        # 🟢 ACTUALIZACIÓN DE INVENTARIO (Crucial): Reducir el stock 🟢
        for item in carrito:
            productos_col.update_one(
                {"codigo_barras": item['codigo']},
                {"$inc": {"stock": -item['cantidad']}} # Decrementar el stock
            )
        
        messagebox.showinfo("Venta Exitosa", f"Venta ID: {compra_id}\nTotal: ${total_compra:.2f}\nGuardado en MongoDB!")
        
        carrito.clear()
        actualizar_carrito()
        
    except Exception as e:
        messagebox.showerror("Error de Escritura", f"Fallo al guardar o actualizar inventario en MongoDB: {e}")

def actualizar_carrito():
    global total_compra, lista_productos, lbl_total_valor
    
    # ⚠️ CRÍTICO: Verificar si los widgets existen antes de usarlos
    if lista_productos is None or lbl_total_valor is None: 
        return
        
    lista_productos.delete(*lista_productos.get_children())
    total_compra = 0.00
    
    for i, item in enumerate(carrito):
        subtotal = item['cantidad'] * item['precio']
        total_compra += subtotal
        lista_productos.insert("", "end", iid=i, 
                               values=(item['codigo'], item['nombre'], item['cantidad'], 
                                       f"${item['precio']:.2f}", f"${subtotal:.2f}"))
                                       
    # La forma de actualizar el texto en un CTkLabel es usando .configure, no .config
    lbl_total_valor.configure(text=f"${total_compra:.2f}") # ⬅️ USAR .configure

# Asegúrate de importar ObjectId: from bson.objectid import ObjectId

def aumentar_cantidad_doble_click(event):
    """Detecta el doble clic en el carrito, busca el producto por código
       y aumenta la cantidad con verificación de stock de la DB."""
    global carrito, lista_productos
    
    if lista_productos is None or productos_col is None: return
    
    item_seleccionado = lista_productos.selection()
    if not item_seleccionado: return
    
    valores = lista_productos.item(item_seleccionado, 'values')
    if not valores: return
        
    codigo_a_aumentar = valores[0] 
    producto_encontrado = False
    
    try:
        # 🟢 1. CONSULTA A MONGODB PARA OBTENER EL STOCK 🟢
        producto_db = productos_col.find_one({"codigo_barras": codigo_a_aumentar})
        
        if not producto_db:
            messagebox.showwarning("Error", "Producto no encontrado en DB."); return
            
        stock_disponible = producto_db.get("stock", 0)
        nombre_producto = producto_db.get("nombre")

        # 2. Recorrer la lista 'carrito' para encontrar el producto
        for item in carrito:
            if item['codigo'] == codigo_a_aumentar:
                cantidad_actual = item['cantidad']
                
                # 3. Lógica de Verificación
                if cantidad_actual >= stock_disponible:
                    messagebox.showwarning("Fuera de Stock", 
                                           f"No hay más stock disponible para '{nombre_producto}'. Límite: {stock_disponible}.")
                    return 
                    
                # 4. Incrementar (si pasa la verificación)
                item['cantidad'] += 1
                producto_encontrado = True
                break
            
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al verificar stock: {e}")
        return
            
    if producto_encontrado:
        actualizar_carrito()
    else:
        messagebox.showwarning("Error de Carrito", "No se encontró el producto para aumentar su cantidad.")

def agregar_producto_por_codigo(event=None):
    global carrito, entry_codigo
    if entry_codigo is None or productos_col is None: return
    
    busqueda = entry_codigo.get().strip()
    entry_codigo.delete(0, tk.END); entry_codigo.focus()
    if not busqueda: return
    
    try:
        producto = productos_col.find_one({"codigo_barras": busqueda})

        if producto is None:
            producto = productos_col.find_one({'nombre': busqueda})

    except Exception as e:
        messagebox.showerror("Error", f"Error de búsqueda en la base de datos: {e}"); return
        
    if producto:
        codigo = producto['codigo_barras']
        stock_disponible = producto.get("stock", 0)
        nombre_producto = producto.get("nombre")
        encontrado = False
        
        # --- FLUJO 1: Producto ya en el Carrito (Incremento) ---
        for item in carrito:
            if item['codigo'] == codigo:
                cantidad_actual = item['cantidad']
                
                if cantidad_actual >= stock_disponible:
                    messagebox.showwarning("Fuera de Stock", f"No hay más stock para '{nombre_producto}'. Límite: {stock_disponible}.")
                    return
                
                item['cantidad'] += 1
                encontrado = True
                break
        
        # --- FLUJO 2: Producto Nuevo (Añadir) ---
        if not encontrado:
            if stock_disponible < 1:
                 messagebox.showwarning("Fuera de Stock", f"'{nombre_producto}' no tiene stock disponible (0)."); return
                 
            # Añadir el producto
            carrito.append({
                "codigo": codigo, 
                "nombre": producto['nombre'], 
                "precio": producto['precio'], 
                "cantidad": 1
            })
            
        actualizar_carrito()
        
    else:
        messagebox.showwarning("Producto No Encontrado", f"El código {codigo} no existe.")

def salir_sistema():
    global pos_window
    if messagebox.askyesno("Salir", "¿Deseas cerrar la sesión y salir del sistema?"):
        if pos_window: pos_window.destroy()
# --- Función Login y Diseño de Interfaces ---

def login():
    global root
    usuario = entry_usuario.get()
    pin = entry_pin.get()
    
    if usuarios_col is None:
        messagebox.showerror("Error", "No hay conexión a la base de datos para iniciar sesión.")
        return

    try:
        # 🟢 CONSULTA A MONGODB: Busca el usuario y el PIN 🟢
        # Nota: En producción, el PIN se debería comparar con un hash cifrado.
        user = usuarios_col.find_one({"usuario": usuario, "pin": pin}) 
        
        if user:
            root.withdraw() 
            crear_interfaz_pos(usuario)
        else:
            messagebox.showerror("Error de Autenticación", "Usuario o PIN incorrectos. Inténtalo de nuevo.")
            
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo en la autenticación: {e}")


def crear_interfaz_pos(usuario="Admin"):
    global pos_window, entry_codigo, lista_productos, lbl_total_valor 

    pos_window = ctk.CTkToplevel(root) 
    pos_window.title(f"POS | {usuario} - Tienda de Abarrotes")
    pos_window.geometry("1200x700")
    try: pos_window.state('zoomed')
    except: pass

    def on_close_pos():
        pos_window.destroy()
        root.destroy()
    pos_window.protocol("WM_DELETE_WINDOW", on_close_pos)

    # --- Lateral ---
    frame_nav = ctk.CTkFrame(pos_window, width=200, corner_radius=0)
    frame_nav.pack(side="left", fill="y")
    ctk.CTkLabel(frame_nav, text="Menú Principal", font=("Roboto",16,"bold")).pack(pady=20)
    ctk.CTkButton(frame_nav,text="🛒 Historial de Ventas").pack(fill="x",padx=10,pady=5)
    ctk.CTkButton(frame_nav,text="📦 Inventario",command=lambda: inventario.abrir_inventario_window(pos_window,productos_col)).pack(fill="x",padx=10,pady=5)
    ctk.CTkButton(frame_nav,text="🧾 Imprimir Ticket",command=lambda: ticket.generar_ticket(carrito,total_compra,pos_window)).pack(fill="x",padx=10,pady=5)
    ctk.CTkButton(frame_nav,text="👤 Clientes",command=lambda: clientes.abrir_clientes_window(pos_window,clientes_col)).pack(fill="x",padx=10,pady=5)
    ctk.CTkLabel(frame_nav, text=f"\nCajero: {usuario}").pack(pady=(50,5))
    ctk.CTkButton(frame_nav,text="🚪 Cerrar Sesión",command=salir_sistema,fg_color="#cc0000").pack(fill="x",padx=10,pady=5)

    # --- Contenedor principal ---
    frame_content = ctk.CTkFrame(pos_window)
    frame_content.pack(side="right", fill="both", expand=True)

    # --- Entrada producto ---
    frame_venta = ctk.CTkFrame(frame_content)
    frame_venta.pack(fill="x", padx=20, pady=20)
    ctk.CTkLabel(frame_venta,text="Escanear Código:").pack(side="left",padx=5)
    entry_codigo = ctk.CTkEntry(frame_venta,width=400,font=("Roboto",14))
    entry_codigo.pack(side="left",fill="x",expand=True,padx=10)
    entry_codigo.focus()
    entry_codigo.bind('<Return>',agregar_producto_por_codigo)
    ctk.CTkButton(frame_venta,text="Agregar",command=agregar_producto_por_codigo).pack(side="left",padx=5)

    # --- TABLA (CORREGIDA) ---
    frame_lista = ctk.CTkFrame(frame_content)
    frame_lista.pack(fill="both",expand=True,padx=20,pady=(0,20))

    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Treeview",
                    background="#2b2b2b",
                    foreground="#ffffff",
                    rowheight=28,
                    fieldbackground="#2b2b2b",
                    font=("Roboto",11))

    style.configure("Treeview.Heading",
                    background="#3a3a3a",
                    foreground="#ffffff",
                    font=("Roboto",12,"bold"))

    columnas = ("codigo","nombre","cantidad","precio_unitario","subtotal")
    lista_productos = ttk.Treeview(frame_lista,columns=columnas,show="headings")

    for col,titulo in zip(columnas,["Código","Producto","Cant.","P. Unitario","Subtotal"]):
        lista_productos.heading(col,text=titulo)
        lista_productos.column(col,anchor="center",minwidth=80,width=120)

    lista_productos.pack(fill="both",expand=True)
    lista_productos.bind("<Double-1>",aumentar_cantidad_doble_click)

    # --- TOTAL Y PAGO ---
    frame_resumen = ctk.CTkFrame(frame_content)
    frame_resumen.pack(fill="x",padx=20,pady=20)

    frame_total = ctk.CTkFrame(frame_resumen,fg_color="transparent")
    frame_total.pack(side="left",padx=20)
    ctk.CTkLabel(frame_total,text="TOTAL:",font=("Roboto",18,"bold")).pack()
    lbl_total_valor = ctk.CTkLabel(frame_total,text="$0.00",font=("Roboto",38,"bold"),text_color="#00ff99")
    lbl_total_valor.pack()

    frame_pagos = ctk.CTkFrame(frame_resumen,fg_color="transparent")
    frame_pagos.pack(side="right")
    ctk.CTkButton(frame_pagos,text="💰 EFECTIVO",fg_color="#28a745",command=finalizar_venta).pack(side="left",padx=10)
    ctk.CTkButton(frame_pagos,text="🚫 CANCELAR",fg_color="#dc3545",command=lambda:[carrito.clear(),actualizar_carrito()]).pack(side="left",padx=10)

# ----------------------------------------------------------------------------------------------------------------------
## 4. Ejecución Principal (Migrada a CTk)

# Configuración inicial de CTk
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")

# Configuración Principal de la Ventana de Login (ctk.CTk)
root = ctk.CTk()
root.title("Sistema de Ventas - Login")

root.state('normal')
root.update_idletasks() # Obliga a Tkinter a procesar los comandos pendientes

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Establecer la geometría al tamaño máximo del escritorio
root.geometry(f"{screen_width}x{screen_height}+0+0")

# Luego, si quieres que se muestre con los botones de maximizar/minimizar (maximizada)
root.state('zoomed')

# --- Contenedor Principal (Centrado) ---
frame_login = ctk.CTkFrame(root, width=400, height=300, corner_radius=10)
frame_login.place(relx=0.5, rely=0.5, anchor=tk.CENTER) # Centrar en la pantalla

# --- Elementos de la Interfaz de Login ---

ctk.CTkLabel(frame_login, text="Tienda El Pinzán", font=("Roboto", 24, "bold"), text_color="#0056b3").pack(pady=20)

# 1. Campo de Usuario/Cajero
entry_usuario = ctk.CTkEntry(frame_login, placeholder_text="Usuario/Cajero", width=250)
entry_usuario.pack(pady=10, padx=20)
entry_usuario.focus() 

# 2. Campo de Contraseña/PIN
entry_pin = ctk.CTkEntry(frame_login, placeholder_text="PIN/Contraseña", show="*", width=250)
entry_pin.pack(pady=10, padx=20)

# 3. Botón de Iniciar Sesión
btn_login = ctk.CTkButton(frame_login, text="🔑 INICIAR SESIÓN", command=login, width=250, fg_color="#0056b3")
btn_login.pack(pady=20, padx=20)

frame_opciones = ctk.CTkFrame(frame_login, fg_color="transparent")
frame_opciones.pack(pady=(0, 10))

# Botón para Modificar Contraseña
ctk.CTkButton(frame_opciones, text="Modificar Contraseña", 
              command=lambda:usuario.abrir_modificar_contrasena(usuarios_col, root), 
              fg_color="gray", hover_color="darkgray", text_color="white", width=120).pack(side="left", padx=5)

# Botón para Registrar Nuevo Usuario
ctk.CTkButton(frame_opciones, text="Registrar Usuario", 
              command=lambda: usuario.abrir_registro_usuario(usuarios_col, root), 
              fg_color="gray", hover_color="darkgray", text_color="white", width=120).pack(side="left", padx=5)

# Configurar el evento Enter para el botón de login
root.bind('<Return>', lambda event: login())

root.mainloop()