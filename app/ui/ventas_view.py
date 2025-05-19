# control_negocio/app/ui/ventas_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.venta import Venta

class VentasView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Registro de Ventas", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        campos = ["Cliente", "Producto", "Cantidad", "Precio Unitario"]
        self.entradas = {}

        for i, campo in enumerate(campos):
            tk.Label(formulario, text=campo + ":", bg="white").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            entrada = ttk.Entry(formulario, width=30)
            entrada.grid(row=i, column=1, pady=5, padx=5)
            self.entradas[campo.lower().replace(" ", "_")] = entrada

        botones = tk.Frame(self, bg="white")
        botones.pack(pady=10)

        ttk.Button(botones, text="Registrar Venta", command=self.registrar_venta, width=20).pack()

        self.tabla = ttk.Treeview(self, columns=("id", "cliente", "producto", "cantidad", "precio_unitario"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col.capitalize())
            self.tabla.column(col, width=130)
        self.tabla.pack(pady=10, fill="x")

    def registrar_venta(self):
        try:
            datos = {k: v.get() for k, v in self.entradas.items()}
            Venta.registrar(
                datos["cliente"],
                datos["producto"],
                int(datos["cantidad"]),
                float(datos["precio_unitario"])
            )
            self.limpiar_entradas()
            self.cargar_tabla()
            messagebox.showinfo("Éxito", "Venta registrada y stock actualizado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la venta: {e}")

    def limpiar_entradas(self):
        for entrada in self.entradas.values():
            entrada.delete(0, tk.END)

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        ventas = Venta.listar_todas()
        for v in ventas:
            self.tabla.insert("", tk.END, values=v)
