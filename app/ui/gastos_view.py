# control_negocio/app/ui/gastos_view.py

import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar, END, messagebox
from app.models.finanzas import Finanzas


class GastosView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(
            self,
            text="📤 Consulta de Gastos",
            font=("Arial", 16, "bold"),
            bg="white",
        ).pack(pady=10)

        self.texto = Text(self, width=100, height=22)
        self.texto.pack(padx=10, pady=5, fill="both", expand=True)

        scrollbar = Scrollbar(self, orient="vertical", command=self.texto.yview)
        scrollbar.pack(side="right", fill="y")
        self.texto.configure(yscrollcommand=scrollbar.set)

        self.mostrar_gastos()

    def _fmt_monto(self, x) -> str:
        try:
            return f"${float(x or 0):,.2f}"
        except Exception:
            return "$0.00"

    def mostrar_gastos(self):
        """Carga y muestra gastos con totales por estado y total general."""
        try:
            gastos = Finanzas.listar_gastos()
        except Exception as e:
            return messagebox.showerror("Error", f"No se pudieron cargar los gastos.\n\n{str(e)}")

        total_general = 0.0
        totales_por_estado = {
            "pendiente": 0.0,
            "pagado": 0.0,
            "rechazado": 0.0,
        }

        # Limpia el texto previo
        self.texto.delete("1.0", END)
        self.texto.insert(END, "📄 Gastos registrados (más recientes primero):\n\n")

        if not gastos:
            self.texto.insert(END, "— No hay gastos registrados —")
            return

        for g in gastos:
            # g = (id, nombre, descripcion, monto, estado, fecha)
            _id, nombre, _desc, monto_raw, estado, fecha = g
            try:
                monto = float(monto_raw or 0)
            except (TypeError, ValueError):
                monto = 0.0

            total_general += monto
            estado_l = (estado or "").lower()
            if estado_l in totales_por_estado:
                totales_por_estado[estado_l] += monto

            nombre = nombre or "(sin nombre)"
            fecha = fecha or "-"
            estado = estado or "-"

            self.texto.insert(
                END,
                f"• {nombre}  "
                f"(estado: {estado}, fecha: {fecha})  "
                f"→ {self._fmt_monto(monto)}\n"
            )

        # Resumen por estado
        self.texto.insert(END, "\n📑 Totales por estado:\n")
        for est in ("pendiente", "pagado", "rechazado"):
            self.texto.insert(END, f"   • {est.capitalize():10s}: {self._fmt_monto(totales_por_estado[est])}\n")

        # Total general
        self.texto.insert(END, f"\n🔴 Total de Gastos: {self._fmt_monto(total_general)}\n")
