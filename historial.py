# historial.py

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

def cargar_historial_ventas(tree, ventas_col):
    """Carga los documentos de la colección de ventas al Treeview con separadores semanales."""
    from datetime import datetime
    for item in tree.get_children(): 
        tree.delete(item)

    try:
        ventas = list(ventas_col.find().sort("fecha_hora", -1))
        semana_actual = None

        total_semana = 0.0
        ganancia_semana = 0.0
        items_semana = 0

        for venta in ventas:
            fecha_str = venta.get("fecha_hora", "")
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            except:
                continue

            semana_venta = fecha.strftime("%Y-%W")  # Año-Semana

            # Cuando cambia la semana, insertamos resumen
            if semana_actual and semana_actual != semana_venta:
                tree.insert("", "end", values=(
                    f"--- CIERRE DE SEMANA {semana_actual} ---",
                    "",
                    "",
                    f"Total: ${total_semana:.2f}",
                    f"Ganancia: ${ganancia_semana:.2f}",
                    f"Items: {items_semana}"
                ), tags=("resumen",))

                # Reset
                total_semana = 0.0
                ganancia_semana = 0.0
                items_semana = 0

            semana_actual = semana_venta

            # Acumular valores
            total_semana += venta.get("total_venta", 0.0)
            ganancia_semana += venta.get("ganancia_total", 0.0)
            items_semana += sum(p.get("cantidad", 0) for p in venta.get("productos", []))

            # Insertar venta individual
            tree.insert("", "end", iid=str(venta.get("_id")), values=(
                venta.get("transaccion_id"),
                venta.get("fecha_hora"),
                venta.get("cajero", "N/A"),
                f"${venta.get('total_venta', 0.0):.2f}",
                f"${venta.get('ganancia_total', 0.0):.2f}",
                sum(p.get('cantidad', 0) for p in venta.get('productos', []))
            ))

        # Insertar el resumen de la última semana mostrada
        if semana_actual:
            tree.insert("", "end", values=(
                f"--- CIERRE DE SEMANA {semana_actual} ---",
                "",
                "",
                f"Total: ${total_semana:.2f}",
                f"Ganancia: ${ganancia_semana:.2f}",
                f"Productos: {items_semana}"
            ), tags=("resumen",))

        # Estilo visual para separadores
        tree.tag_configure("resumen", background="#6c757d", font=("Roboto", 11, "bold"))

    except Exception as e:
        messagebox.showerror("Error DB", f"Fallo al cargar historial: {e}")



def abrir_historial_window(pos_window, ventas_col):
    if ventas_col is None:
        messagebox.showerror("Error", "No hay conexión a la colección de ventas.")
        return

    historial_window = ctk.CTkToplevel(pos_window)
    historial_window.title("📊 Historial de Ventas por Semana")
    historial_window.geometry("1000x700")
    historial_window.transient(pos_window)
    historial_window.grab_set()

    frame_acciones = ctk.CTkFrame(historial_window)
    frame_acciones.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(frame_acciones, text="RESUMEN SEMANAL DE VENTAS", font=("Roboto", 16, "bold")).pack(side="left", padx=10)

    ctk.CTkButton(frame_acciones, text="🔄 Recargar",
                  command=lambda: cargar_historial_ventas(tree_historial, ventas_col),
                  fg_color="#6c757d").pack(side="right", padx=10)

    columnas = ("semana", "inicio", "fin", "total", "ganancia", "items")
    tree_historial = ttk.Treeview(historial_window, columns=columnas, show="headings")

    tree_historial.heading("semana", text="ID Venta"); tree_historial.column("semana", width=100)
    tree_historial.heading("inicio", text="Fecha y Hora"); tree_historial.column("inicio", width=120)
    tree_historial.heading("fin", text="Usuario"); tree_historial.column("fin", width=120)
    tree_historial.heading("total", text="Total Ventas"); tree_historial.column("total", width=120, anchor='e')
    tree_historial.heading("ganancia", text="Ganancia"); tree_historial.column("ganancia", width=120, anchor='e')
    tree_historial.heading("items", text="Productos vendidos"); tree_historial.column("items", width=120, anchor='center')

    tree_historial.pack(fill="both", expand=True, padx=20, pady=10)

    cargar_historial_ventas(tree_historial, ventas_col)

    historial_window.wait_window()
