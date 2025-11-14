# inicio.py

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
# Importar módulos auxiliares
import inventario
import clientes
import usuarios # Modulo de gestión de usuarios/registro
import historial # Modulo para ver historial de ventas
import ticket    # Modulo para generar ticket
from pymongo import MongoClient 
from bson.regex import Regex
from bson.objectid import ObjectId 
import time
import random
from bson.objectid import ObjectId # Necesario para buscar por ID


# ======================================================================================
# 1. CONEXIÓN A MONGODB Y CONFIGURACIÓN GLOBAL
# ======================================================================================

# ⚠️ CRÍTICO: REEMPLAZA ESTA URI CON TUS DATOS REALES ⚠️
MONGO_URI = "mongodb+srv://Carlosbernal:CarBer1998@cluster0.z31tlvd.mongodb.net/?appName=Cluster0"
DB_NAME = "Tienda"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    productos_col = db['productos']
    ventas_col = db['ventas']        
    clientes_col = db['clientes']
    usuarios_col = db['usuarios']
    
    print("✅ Conexión a MongoDB exitosamente.")
except Exception as e:
    messagebox.showerror("Error de Conexión DB", f"No se pudo conectar a MongoDB: {e}")
    productos_col, ventas_col, clientes_col, usuarios_col = None, None, None, None
    

# ======================================================================================
# 2. VARIABLES GLOBALES Y UTILIDADES
# ======================================================================================

carrito = []
total_compra = 0.00
entry_codigo = None
lista_productos = None
lbl_total_valor = None
pos_window = None
root = None 
usuario_global = None 
rol_global = None     
frame_sugerencias = None # Para la búsqueda predictiva
sugerencias_visibles = {}


# --- Funciones de Lógica de Venta y Carrito ---

def finalizar_venta():
    global carrito, total_compra, usuario_global

    if not carrito: messagebox.showwarning("Venta Vacía", "No hay productos en el carrito para cobrar."); return
    if ventas_col is None or productos_col is None:
        messagebox.showerror("Error", "No se puede guardar la venta. Conexión DB perdida."); return
    
    compra_id = time.strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999)) 
    
    productos_vendidos = []
    ganancia_total = 0.0
    stock_updates = []
    
    try:
        # --- CALCULAR GANANCIA Y PREPARAR ACTUALIZACIONES ---
        for item in carrito:
            precio = item.get('precio', 0.0)
            precio_compra = item.get('precio_compra', 0.0)
            cantidad = item.get('cantidad', 0)
            
            ganancia_item = (precio - precio_compra) * cantidad
            ganancia_total += ganancia_item
            
            productos_vendidos.append(item.copy())
            stock_updates.append({"codigo_barras": item['codigo'], "cantidad": cantidad})
            
        documento_ticket = {
            "transaccion_id": compra_id,
            "fecha_hora": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cajero": usuario_global, 
            "total_venta": total_compra,
            "ganancia_total": ganancia_total, 
            "productos": productos_vendidos,
            "metodo_pago": "Efectivo"
        }

        # 🟢 GUARDAR VENTA E INVENTARIO 🟢
        ventas_col.insert_one(documento_ticket)
        
        for update in stock_updates:
            productos_col.update_one(
                {"codigo_barras": update['codigo_barras']},
                {"$inc": {"stock": -update['cantidad']}}
            )
        
        messagebox.showinfo("Venta Exitosa", f"ID: {compra_id}\nTotal: ${total_compra:.2f}\nGanancia Estimada: ${ganancia_total:.2f}")
        
        carrito.clear()
        actualizar_carrito()
        
    except Exception as e:
        messagebox.showerror("Error de Escritura", f"Fallo en transacción: {e}")

def actualizar_carrito():
    global total_compra, lista_productos, lbl_total_valor
    if lista_productos is None or lbl_total_valor is None: return
    
    lista_productos.delete(*lista_productos.get_children())
    total_compra = 0.00
    
    for i, item in enumerate(carrito):
        subtotal = item['cantidad'] * item['precio']
        total_compra += subtotal
        lista_productos.insert("", "end", iid=i, 
                               values=(item['codigo'], item['nombre'], item['cantidad'], 
                                       f"${item['precio']:.2f}", f"${subtotal:.2f}"))
                                       
    lbl_total_valor.configure(text=f"${total_compra:.2f}")

def aumentar_cantidad_doble_click(event):
    global carrito, lista_productos
    if lista_productos is None or productos_col is None: return
    
    item_seleccionado = lista_productos.selection()
    if not item_seleccionado: return
    
    valores = lista_productos.item(item_seleccionado, 'values')
    if not valores: return
        
    codigo_a_aumentar = valores[0] 
    producto_encontrado = False
    
    try:
        producto_db = productos_col.find_one({"codigo_barras": codigo_a_aumentar})
        
        if not producto_db:
            messagebox.showwarning("Error", "Producto no encontrado en DB."); return
            
        stock_disponible = producto_db.get("stock", 0)
        nombre_producto = producto_db.get("nombre")

        for item in carrito:
            if item['codigo'] == codigo_a_aumentar:
                cantidad_actual = item['cantidad']
                
                if cantidad_actual >= stock_disponible:
                    messagebox.showwarning("Fuera de Stock", f"No hay más stock disponible para '{nombre_producto}'. Límite: {stock_disponible}."); return 
                    
                item['cantidad'] += 1
                producto_encontrado = True
                break
            
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al verificar stock: {e}"); return
            
    if producto_encontrado:
        actualizar_carrito()

def agregar_producto_por_codigo(event=None):
    global carrito, entry_codigo
    if entry_codigo is None or productos_col is None: return
    
    busqueda = entry_codigo.get().strip()
    entry_codigo.delete(0, tk.END); entry_codigo.focus()
    if not busqueda: return
    
    producto = None
    
    try:
        # 1. Búsqueda por Código de Barras Exacto
        producto = productos_col.find_one({"codigo_barras": busqueda})
        
        # 2. Si no se encontró, buscar por Nombre (coincidencia parcial)
        if producto is None:
            producto = productos_col.find_one({'nombre': Regex(f'.*{busqueda}.*', 'i')})
            
    except Exception as e:
        messagebox.showerror("Error", f"Error de búsqueda en DB: {e}"); return
        
    if not producto:
        messagebox.showwarning("Producto No Encontrado", f"'{busqueda}' no coincide con ningún producto."); return

    codigo = producto.get("codigo_barras")
    nombre = producto.get("nombre")
    stock = producto.get("stock", 0)
    precio_venta = producto.get("precio_venta", 0.0)
    precio_compra = producto.get("precio_compra", 0.0)

    # --- Si el producto ya está en el carrito ---
    for item in carrito:
        if item["codigo"] == codigo:
            if item["cantidad"] >= stock:
                messagebox.showwarning("Fuera de Stock", f"No hay más stock disponible. Stock: {stock}."); return
            item["cantidad"] += 1
            actualizar_carrito()
            return

    # --- Si es un producto nuevo ---
    if stock <= 0:
        messagebox.showwarning("Sin Stock", f"No queda stock disponible de '{nombre}'."); return

    carrito.append({
        "codigo": codigo,
        "nombre": nombre,
        "precio": precio_venta,
        "precio_compra": precio_compra,
        "cantidad": 1
    })

    actualizar_carrito()

def disminuir_cantidad_tecla(event=None):
    global carrito, lista_productos
    
    seleccion_ids = lista_productos.selection()
    if not seleccion_ids: messagebox.showwarning("Selección", "Debes seleccionar un producto del carrito."); return
    
    item_id = seleccion_ids[0] 
    valores = lista_productos.item(item_id, 'values')
    if not valores: return
        
    codigo_a_disminuir = valores[0] 
    producto_modificado = False
    
    for i, item in enumerate(carrito):
        if item['codigo'] == codigo_a_disminuir:
            cantidad_actual = item['cantidad']
            nombre = item['nombre']
            
            if cantidad_actual <= 1:
                if messagebox.askyesno("Eliminar Producto", f"¿Desea eliminar completamente '{nombre}' del carrito?"):
                    carrito.pop(i) 
                    producto_modificado = True
                break
            else:
                item['cantidad'] -= 1
                producto_modificado = True
                break
            
    if producto_modificado:
        actualizar_carrito()

def salir_sistema():
    global pos_window, root
    if messagebox.askyesno("Cerrar Sesión", "¿Deseas cerrar sesión y volver al inicio?"):
        if pos_window:
            pos_window.destroy()  # Cerrar la ventana del POS
        root.deiconify()          # Mostrar la ventana de login nuevamente
        root.focus_force()        # Asegurar que el login reciba el foco


# --- Funciones de Búsqueda Predictiva ---

def seleccionar_sugerencia(codigo):
    global entry_codigo, frame_sugerencias
    entry_codigo.delete(0, tk.END)
    entry_codigo.insert(0, codigo)
    frame_sugerencias.place_forget()
    agregar_producto_por_codigo()
    

def mostrar_sugerencias(event):
    global entry_codigo, frame_sugerencias, sugerencias_visibles
    
    texto_busqueda = entry_codigo.get().strip()
    
    if len(texto_busqueda) < 3 or productos_col is None:
        frame_sugerencias.place_forget()
        return

    for widget in frame_sugerencias.winfo_children():
        widget.destroy()
    sugerencias_visibles.clear()

    try:
        query = {
            "$or": [
                {"codigo_barras": Regex(f'.*{texto_busqueda}.*', 'i')}, 
                {"nombre": Regex(f'.*{texto_busqueda}.*', 'i')}
            ]
        }
        
        resultados = productos_col.find(query).limit(10)
        row = 0
        
        for producto in resultados:
            codigo = producto.get('codigo_barras')
            nombre = producto.get('nombre')
            
            display_text = f"{nombre[:35]} ({codigo})"
            
            btn = ctk.CTkButton(frame_sugerencias, text=display_text, anchor="w",
                                command=lambda c=codigo: seleccionar_sugerencia(c),
                                fg_color="transparent", hover_color="#3a3a3a",
                                text_color="white", width=400)
            btn.pack(fill="x", padx=5, pady=2)
            sugerencias_visibles[codigo] = True
            row += 1
            
        if row > 0:
            # POSICIONAR BAJO EL ENTRY (x=190 es un estimado de la posición del entry)
            frame_sugerencias.place(x=190, y=45) 
        else:
            frame_sugerencias.place_forget()

    except Exception as e:
        print(f"Error en la búsqueda predictiva: {e}")
        frame_sugerencias.place_forget()

# --- Función Login y Diseño de Interfaces ---

def login():
    global root, usuario_global, rol_global
    usuario_ingresado = entry_usuario.get()
    pin = entry_pin.get()
    
    if usuarios_col is None:
        messagebox.showerror("Error", "No hay conexión a la base de datos para iniciar sesión.")
        return

    try:
        user = usuarios_col.find_one({"usuario": usuario_ingresado, "pin": pin}) 
        
        if user:
            usuario_global = user.get("usuario")
            rol_global = user.get("rol", "cajero")

            # 🟢 OCULTAR login y abrir POS
            root.withdraw()  
            crear_interfaz_pos(usuario_global)

            # 🧹 Limpiar los campos después de entrar
            entry_usuario.delete(0, tk.END)
            entry_pin.delete(0, tk.END)
        else:
            messagebox.showerror("Error de Autenticación", "Usuario o PIN incorrectos. Inténtalo de nuevo.")
            
    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo en la autenticación: {e}")



def crear_interfaz_pos(usuario):
    global pos_window, entry_codigo, lista_productos, lbl_total_valor, rol_global, frame_sugerencias 

    pos_window = ctk.CTkToplevel(root) 
    pos_window.title(f"POS | {usuario} ({rol_global}) - Tienda de Abarrotes")
    pos_window.geometry("1200x700")
    try: pos_window.state('zoomed')
    except: pass

    def on_close_pos():
        pos_window.destroy()
        root.deiconify() 
    pos_window.protocol("WM_DELETE_WINDOW", on_close_pos)

    # --- Lateral ---
    frame_nav = ctk.CTkFrame(pos_window, width=200, corner_radius=0)
    frame_nav.pack(side="left", fill="y")
    ctk.CTkLabel(frame_nav, text="Menú Principal", font=("Roboto",16,"bold")).pack(pady=20)
    
    # Lógica de Permisos
    es_admin = (rol_global == 'administrador')
    estado_admin = "normal" if es_admin else "disabled"
    estado_admin_color = "#0056b3" if es_admin else "#4a4a4a"

    # 1. BOTÓN: Historial de Ventas (Controlado por Rol)
    if es_admin:
        ctk.CTkButton(frame_nav,text="🛒 Historial de Ventas", 
                      command=lambda:historial.abrir_historial_window(pos_window, ventas_col), 
                      fg_color="#0056b3").pack(fill="x",padx=10,pady=5)
    else:
        ctk.CTkButton(frame_nav,text="🚫 Historial", 
                      state="disabled", fg_color="#4a4a4a").pack(fill="x",padx=10,pady=5)
        
    # 2. BOTÓN: Inventario (Pasa el rol)
    ctk.CTkButton(frame_nav,text="📦 Inventario",command=lambda: inventario.abrir_inventario_window(pos_window,productos_col, rol_global)).pack(fill="x",padx=10,pady=5)
    
    # 3. BOTÓN: Imprimir Ticket
    ctk.CTkButton(frame_nav,text="🧾 Imprimir Ticket",command=lambda: ticket.generar_ticket(carrito,total_compra,pos_window)).pack(fill="x",padx=10,pady=5)
    
    # 4. BOTÓN: Clientes
    ctk.CTkButton(frame_nav,text="👤 Clientes",command=lambda: clientes.abrir_clientes_window(pos_window,clientes_col)).pack(fill="x",padx=10,pady=5)
    
    # 5. BOTÓN: ADMINISTRAR USUARIOS
    ctk.CTkButton(frame_nav, text="👤 Administrar Usuarios", 
                  command=lambda: usuarios.abrir_gestion_usuarios_window(pos_window, usuarios_col), 
                  fg_color=estado_admin_color, 
                  state=estado_admin).pack(fill="x", padx=10, pady=5)
    
    # --- Etiqueta y Cerrar Sesión (AL FINAL) ---
    ctk.CTkLabel(frame_nav, text=f"\nCajero: {usuario}").pack(pady=(50,5))
    ctk.CTkButton(frame_nav,text="🚪 Cerrar Sesión",command=salir_sistema,fg_color="#cc0000").pack(fill="x",padx=10,pady=5)

    # --- Contenedor principal ---
    frame_content = ctk.CTkFrame(pos_window); frame_content.pack(side="right", fill="both", expand=True)

    # --- Entrada producto ---
    frame_venta = ctk.CTkFrame(frame_content); frame_venta.pack(fill="x", padx=20, pady=20)
    ctk.CTkLabel(frame_venta,text="Escribir nombre o código de producto:").pack(side="left",padx=5)
    entry_codigo = ctk.CTkEntry(frame_venta,width=400,font=("Roboto",14))
    entry_codigo.pack(side="left",fill="x",expand=True,padx=10)
    entry_codigo.focus()
    entry_codigo.bind('<Return>',agregar_producto_por_codigo)
    entry_codigo.bind('<KeyRelease>', mostrar_sugerencias)
    ctk.CTkButton(frame_venta,text="Agregar",command=agregar_producto_por_codigo).pack(side="left",padx=5)
    
    # 🟢 DEFINICIÓN DEL FRAME DE SUGERENCIAS 🟢
    frame_sugerencias = ctk.CTkScrollableFrame(
    frame_venta,
    width=400,
    height=200,
    fg_color="#1f1f1f",
    label_text="Coincidencias:",
    label_fg_color="#0056b3",
    label_text_color="white",
    border_color="#0056b3",
    border_width=2)
    frame_sugerencias.place_forget() 

    # --- TABLA (CORREGIDA) ---
    frame_lista = ctk.CTkFrame(frame_content); frame_lista.pack(fill="both",expand=True,padx=20,pady=(0,20))

    style = ttk.Style(); style.theme_use("clam")
    style.configure("Treeview", background="#2b2b2b", foreground="#ffffff", rowheight=28, fieldbackground="#2b2b2b", font=("Roboto",11))
    style.configure("Treeview.Heading", background="#3a3a3a", foreground="#ffffff", font=("Roboto",12,"bold"))

    columnas = ("codigo","nombre","cantidad","precio_unitario","subtotal")
    lista_productos = ttk.Treeview(frame_lista,columns=columnas,show="headings")

    for col,titulo in zip(columnas,["Código","Producto","Cant.","P. Unitario","Subtotal"]):
        lista_productos.heading(col,text=titulo)
        lista_productos.column(col,anchor="center",minwidth=80,width=120)

    lista_productos.pack(fill="both",expand=True)
    lista_productos.bind("<Double-1>",aumentar_cantidad_doble_click)
    lista_productos.bind("<Delete>", disminuir_cantidad_tecla)
    lista_productos.bind("<Key-Delete>", disminuir_cantidad_tecla)

    # --- TOTAL Y PAGO ---
    frame_resumen = ctk.CTkFrame(frame_content); frame_resumen.pack(fill="x",padx=20,pady=20)
    frame_total = ctk.CTkFrame(frame_resumen,fg_color="transparent"); frame_total.pack(side="left",padx=20)
    ctk.CTkLabel(frame_total,text="TOTAL:",font=("Roboto",18,"bold")).pack()
    lbl_total_valor = ctk.CTkLabel(frame_total,text="$0.00",font=("Roboto",38,"bold"),text_color="#00ff99"); lbl_total_valor.pack()
    frame_pagos = ctk.CTkFrame(frame_resumen,fg_color="transparent"); frame_pagos.pack(side="right")
    ctk.CTkButton(frame_pagos,text="💰 EFECTIVO",fg_color="#28a745",command=finalizar_venta).pack(side="left",padx=10)
    ctk.CTkButton(frame_pagos,text="🚫 CANCELAR",fg_color="#dc3545",command=lambda:[carrito.clear(),actualizar_carrito()]).pack(side="left",padx=10)

# ----------------------------------------------------------------------------------------------------------------------
## 4. Ejecución Principal (Migrada a CTk)

# Configuración inicial de CTk
ctk.set_appearance_mode("System") 
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
ctk.CTkButton(frame_opciones, text="Modificar Contraseña", command=lambda:usuarios.abrir_modificar_contrasena(usuarios_col, root), fg_color="gray", hover_color="darkgray", text_color="white", width=120).pack(side="left", padx=5)

# Botón para Registrar Nuevo Usuario
ctk.CTkButton(frame_opciones, text="Registrar Usuario", command=lambda: usuarios.abrir_registro_usuario(usuarios_col, root), 
fg_color="gray", hover_color="darkgray", text_color="white", width=120).pack(side="left", padx=5)

# Configurar el evento Enter para el botón de login
root.bind('<Return>', lambda event: login())

root.mainloop()