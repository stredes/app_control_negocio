from tkinter import Frame, Label, Text, Scrollbar, END
from app.models.finanzas import Finanzas

class ConsultaIngresosView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="📥 Consulta de Ingresos", font=("Arial", 16, "bold")).pack(pady=10)

        self.texto = Text(self, width=100, height=20)
        self.texto.pack(padx=10, pady=5)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        self.texto.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.texto.yview)

        self.mostrar_ingresos()

    def mostrar_ingresos(self):
        ingresos = Finanzas.listar_ingresos()
        total = sum(i[2] for i in ingresos)

        self.texto.delete("1.0", END)
        self.texto.insert(END, "🧾 Ingresos Registrados:\n\n")
        for ingreso in ingresos:
            self.texto.insert(END, f"• {ingreso[1]}: ${ingreso[2]:,.0f}\n")

        self.texto.insert(END, f"\n💰 Total de Ingresos: ${total:,.0f}")
