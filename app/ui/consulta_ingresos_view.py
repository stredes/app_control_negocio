# control_negocio/app/ui/consulta_ingresos_view.py

import tkinter as tk
from tkinter import Frame, Label, ttk
from app.models.finanzas import Finanzas

class ConsultaIngresosView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="🧾 Consulta de Ingresos", font=("Arial", 16, "bold"), bg="white")\
            .pack(pady=10)

        cols = ("ID", "Nombre", "Monto", "Estado", "Fecha")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.monto_total_lbl = Label(self, text="", bg="white", font=("Arial", 12, "bold"))
        self.monto_total_lbl.pack(pady=5)

        self.mostrar_ingresos()

    def mostrar_ingresos(self):
        # limpia tabla
        for r in self.tree.get_children():
            self.tree.delete(r)

        ingresos = Finanzas.listar_ingresos()
        total = 0.0
        for i in ingresos:
            # i = (id, nombre, descripcion, monto, estado, fecha)
            monto = float(i[3])  # convierte a float
            total += monto
            self.tree.insert("", tk.END, values=(i[0], i[1], monto, i[4], i[5]))

        self.monto_total_lbl.config(text=f"Total ingresado: ${total:,.2f}")
