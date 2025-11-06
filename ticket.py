# ticket.py

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import time

def generar_ticket(carrito, total_compra, pos_window):

    if not carrito:
        messagebox.showwarning("Ticket Vacío", "No hay productos en el carrito")
        return

    # --- Construcción del Encabezado del Ticket ---
    # Usamos espacios fijos y alineación para simular una impresora de texto fijo
    ticket_lines = []
    ticket_lines.append("=" * 35)
    ticket_lines.append("       TIENDA 'EL PINZÁN'     ")
    ticket_lines.append("         PUNTO DE VENTA   ")
    ticket_lines.append("=" * 35)
    ticket_lines.append(f"FECHA: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    ticket_lines.append("-" * 35)
    
    # --- Encabezados de Productos ---
    ticket_lines.append(f"{'CANT':<5}{'PRODUCTO':<20}{'TOTAL':>10}")
    ticket_lines.append("-" * 35)

    # --- Detalle de Productos ---
    for item in carrito:
        subtotal = item['cantidad'] * item['precio']
        line = f"{item['cantidad']:<5}{item['nombre'][:19]:<20}${subtotal:>8.2f}"
        ticket_lines.append(line)
    
    ticket_lines.append("-" * 35)

    # --- Totales ---
    ticket_lines.append(f"{'SUBTOTAL:':<25}${total_compra:>8.2f}")
    ticket_lines.append(f"{'TOTAL A PAGAR:':<25}${total_compra:>8.2f}") 
    
    ticket_lines.append("=" * 35)
    ticket_lines.append("      ¡GRACIAS POR SU COMPRA!     ")
    ticket_lines.append("\n\n")

    # Muestra el ticket en la nueva ventana CTk
    mostrar_ticket_ventana("\n".join(ticket_lines), pos_window=pos_window)


def mostrar_ticket_ventana(ticket_content, pos_window):
    """Crea una ventana CTk Toplevel para mostrar el contenido del ticket."""
    
    # 🟢 CTK Toplevel 🟢
    ventana_ticket = ctk.CTkToplevel(pos_window)
    ventana_ticket.title("Ticket de Venta")
    ventana_ticket.geometry("400x550")
    ventana_ticket.transient(pos_window)
    ventana_ticket.grab_set()

    # Usamos un CTkTextbox ya que es más moderno que tk.Text
    ticket_text = ctk.CTkTextbox(ventana_ticket, 
                                 wrap='word', 
                                 font=('Consolas', 12), # Fuente monoespacio para alineación perfecta
                                 activate_scrollbars=True,
                                 fg_color="white", 
                                 text_color="black",
                                 border_width=0)
    ticket_text.pack(expand=True, fill='both', padx=10, pady=10)
    
    # Insertar el contenido y hacerlo de solo lectura
    ticket_text.insert("end", ticket_content)
    ticket_text.configure(state="disabled") # Usamos .configure en CTk

    # 🟢 CTK Button 🟢
    ctk.CTkButton(ventana_ticket, text="Cerrar / Listo", command=ventana_ticket.destroy, 
                  fg_color="#0056b3").pack(pady=10)
    
    ventana_ticket.wait_window()