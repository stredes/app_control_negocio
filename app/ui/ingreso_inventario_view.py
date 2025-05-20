# control_negocio/app/ui/ingreso_inventario_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.ingreso_inventario import IngresoInventario

class IngresoInventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Ingreso de Productos al Inventario", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        campos = ["Código Interno", "Cantidad", "Ubicación", "Método"]
        self.entradas = {}

        for i, campo in enumerate(campos):
            tk.Label(form, text=campo + ":", bg="white").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=i, column=1, padx=5)
            self.entradas[campo.lower().replace(" ", "_")] = entry

        self.entradas["método"].insert(0, "manual")

        ttk.Button(self, text="Registrar Ingreso", command=self.registrar).pack(pady=10)

        self.tabla = ttk.Treeview(self, columns=("ID", "Código", "Tipo", "Cantidad", "Ubicación", "Método", "Fecha"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=120)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def registrar(self):
        try:
            datos = {k: v.get() for k, v in self.entradas.items()}
            IngresoInventario.registrar(
                datos["código_interno"],
                int(datos["cantidad"]),
                datos["ubicación"],
                datos["método"]
            )
            self.cargar_tabla()
            self.limpiar()
            messagebox.showinfo("Ingreso registrado", "🟢 Stock actualizado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for entrada in IngresoInventario.listar_entradas():
            self.tabla.insert("", "end", values=entrada)

    def limpiar(self):
        for entry in self.entradas.values():
            entry.delete(0, tk.END)
        self.entradas["método"].insert(0, "manual")
