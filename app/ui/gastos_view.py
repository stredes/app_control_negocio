from tkinter import Frame, Label, Text, Scrollbar, END
from app.models.finanzas import Finanzas

class GastosView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="📤 Consulta de Gastos", font=("Arial", 16, "bold")).pack(pady=10)

        self.texto = Text(self, width=100, height=20)
        self.texto.pack(padx=10, pady=5)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        self.texto.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.texto.yview)

        self.mostrar_gastos()

    def mostrar_gastos(self):
        gastos = Finanzas.listar_gastos()
        total = sum(g[2] for g in gastos)

        self.texto.delete("1.0", END)
        self.texto.insert(END, "📄 Gastos Registrados:\n\n")
        for gasto in gastos:
            self.texto.insert(END, f"• {gasto[1]}: ${gasto[2]:,.0f}\n")

        self.texto.insert(END, f"\n🔴 Total de Gastos: ${total:,.0f}")
