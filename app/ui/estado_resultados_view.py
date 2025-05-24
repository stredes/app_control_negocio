# control_negocio/app/ui/estado_resultados_view.py

import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar, END, Button
from app.models.finanzas import Finanzas

class EstadoResultadosView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self,
              text="📊 Estado de Resultados",
              font=("Arial", 16, "bold"),
              bg="white")\
            .pack(pady=10)

        Button(self,
               text="🔄 Actualizar",
               command=self.mostrar_resultados)\
            .pack(pady=5)

        self.texto = Text(self, width=100, height=20)
        self.texto.pack(padx=10, pady=5, fill="both", expand=True)

        sb = Scrollbar(self, command=self.texto.yview)
        sb.pack(side="right", fill="y")
        self.texto.configure(yscrollcommand=sb.set)

        self.mostrar_resultados()

    def mostrar_resultados(self):
        ingresos = Finanzas.listar_ingresos()
        gastos   = Finanzas.listar_gastos()
        total_ingresos, total_gastos, utilidad = Finanzas.estado_resultado()

        self.texto.delete("1.0", END)
        self.texto.insert(END, "📋 Ingresos:\n")
        for i in ingresos:
            # i = (id, nombre, descripcion, monto, estado, fecha)
            try:
                monto = float(i[3])
            except (TypeError, ValueError):
                monto = 0.0
            self.texto.insert(END, f"- {i[1]} ({i[4]}): ${monto:,.2f}\n")

        self.texto.insert(END, "\n💸 Gastos:\n")
        for g in gastos:
            # g = (id, nombre, descripcion, monto, estado, fecha)
            try:
                monto = float(g[3])
            except (TypeError, ValueError):
                monto = 0.0
            self.texto.insert(END, f"- {g[1]} ({g[4]}): ${monto:,.2f}\n")

        self.texto.insert(END, "\n📑 Resumen:\n")
        self.texto.insert(END, f"🟢 Total Ingresos: ${float(total_ingresos):,.2f}\n")
        self.texto.insert(END, f"🔴 Total Gastos:   ${float(total_gastos):,.2f}\n")
        self.texto.insert(END, f"💰 Utilidad Neta:  ${float(utilidad):,.2f}\n")
