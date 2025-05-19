from tkinter import Frame, Label, Text, Scrollbar, END, Button
from app.models.finanzas import Finanzas

class EstadoResultadosView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="📊 Estado de Resultados", font=("Arial", 16, "bold")).pack(pady=10)

        Button(self, text="🔄 Actualizar", command=self.mostrar_resultados).pack(pady=5)

        self.texto = Text(self, width=100, height=20)
        self.texto.pack(padx=10, pady=5)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        self.texto.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.texto.yview)

        self.mostrar_resultados()

    def mostrar_resultados(self):
        ingresos = Finanzas.listar_ingresos()
        gastos = Finanzas.listar_gastos()
        total_ingresos, total_gastos, utilidad = Finanzas.estado_resultado()

        self.texto.delete("1.0", END)
        self.texto.insert(END, "📋 Ingresos:\n")
        for i in ingresos:
            self.texto.insert(END, f"- {i[1]}: ${i[2]:,.0f}\n")

        self.texto.insert(END, "\n💸 Gastos:\n")
        for g in gastos:
            self.texto.insert(END, f"- {g[1]}: ${g[2]:,.0f}\n")

        self.texto.insert(END, "\n📑 Resumen:\n")
        self.texto.insert(END, f"🟢 Total Ingresos: ${total_ingresos:,.0f}\n")
        self.texto.insert(END, f"🔴 Total Gastos: ${total_gastos:,.0f}\n")
        self.texto.insert(END, f"💰 Utilidad Neta: ${utilidad:,.0f}\n")
