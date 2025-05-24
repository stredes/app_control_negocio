# control_negocio/app/ui/gastos_view.py

import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar, END
from app.models.finanzas import Finanzas

class GastosView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self,
              text="📤 Consulta de Gastos",
              font=("Arial", 16, "bold"),
              bg="white")\
            .pack(pady=10)

        self.texto = Text(self, width=100, height=20)
        self.texto.pack(padx=10, pady=5, fill="both", expand=True)

        scrollbar = Scrollbar(self, orient="vertical", command=self.texto.yview)
        scrollbar.pack(side="right", fill="y")
        self.texto.configure(yscrollcommand=scrollbar.set)

        self.mostrar_gastos()

    def mostrar_gastos(self):
        gastos = Finanzas.listar_gastos()
        total = 0.0

        # Limpia el texto previo
        self.texto.delete("1.0", END)
        self.texto.insert(END, "📄 Gastos Registrados:\n\n")

        for gasto in gastos:
            # gasto = (id, nombre, descripcion, monto, estado, fecha)
            try:
                monto = float(gasto[3])
            except (TypeError, ValueError):
                monto = 0.0

            total += monto
            nombre = gasto[1]
            self.texto.insert(
                END,
                f"• {nombre}: ${monto:,.2f}\n"
            )

        self.texto.insert(
            END,
            f"\n🔴 Total de Gastos: ${total:,.2f}"
        )
