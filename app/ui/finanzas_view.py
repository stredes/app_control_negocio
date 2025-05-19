# control_negocio/app/ui/finanzas_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.finanzas import Finanzas

class FinanzasView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.mostrar_estado()

    def crear_widgets(self):
        tk.Label(self, text="Módulo Financiero", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        form_frame = tk.Frame(self, bg="white")
        form_frame.pack(pady=10)

        self.desc_ingreso = ttk.Entry(form_frame, width=30)
        self.monto_ingreso = ttk.Entry(form_frame, width=10)
        ttk.Label(form_frame, text="Ingreso:", background="white").grid(row=0, column=0)
        self.desc_ingreso.grid(row=0, column=1)
        self.monto_ingreso.grid(row=0, column=2)
        ttk.Button(form_frame, text="Registrar", command=self.registrar_ingreso).grid(row=0, column=3, padx=10)

        self.desc_gasto = ttk.Entry(form_frame, width=30)
        self.monto_gasto = ttk.Entry(form_frame, width=10)
        ttk.Label(form_frame, text="Gasto:", background="white").grid(row=1, column=0)
        self.desc_gasto.grid(row=1, column=1)
        self.monto_gasto.grid(row=1, column=2)
        ttk.Button(form_frame, text="Registrar", command=self.registrar_gasto).grid(row=1, column=3, padx=10)

        self.resultado_lbl = tk.Label(self, text="", font=("Arial", 14), bg="white")
        self.resultado_lbl.pack(pady=20)

    def registrar_ingreso(self):
        try:
            desc = self.desc_ingreso.get()
            monto = float(self.monto_ingreso.get())
            Finanzas.registrar_ingreso(desc, monto)
            self.desc_ingreso.delete(0, tk.END)
            self.monto_ingreso.delete(0, tk.END)
            self.mostrar_estado()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar ingreso: {e}")

    def registrar_gasto(self):
        try:
            desc = self.desc_gasto.get()
            monto = float(self.monto_gasto.get())
            Finanzas.registrar_gasto(desc, monto)
            self.desc_gasto.delete(0, tk.END)
            self.monto_gasto.delete(0, tk.END)
            self.mostrar_estado()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar gasto: {e}")

    def mostrar_estado(self):
        ingresos, gastos, total = Finanzas.estado_resultado()
        self.resultado_lbl.config(
            text=f"💰 Total Ingresos: ${ingresos:.0f}    💸 Total Gastos: ${gastos:.0f}    📊 Resultado: ${total:.0f}"
        )
