# control_negocio/app/ui/estado_resultados_view.py

import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar, END, Button, messagebox
from app.models.finanzas import Finanzas


class EstadoResultadosView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        # Nota: muchos contenedores llaman pack() desde afuera; aquí
        # mantenemos el patrón existente del proyecto.
        self.pack(fill="both", expand=True)
        self._build_ui()
        self.mostrar_resultados()

    # ---------------- Utilidades ----------------
    def _fmt_money(self, x) -> str:
        try:
            return f"${float(x or 0):,.2f}"
        except Exception:
            return "$0.00"

    def _safe_float(self, x) -> float:
        try:
            return float(x or 0)
        except Exception:
            return 0.0

    # ---------------- UI ----------------
    def _build_ui(self):
        Label(
            self,
            text="📊 Estado de Resultados",
            font=("Arial", 16, "bold"),
            bg="white",
        ).pack(pady=10)

        Button(self, text="🔄 Actualizar", command=self.mostrar_resultados)\
            .pack(pady=5)

        # Área de texto con scroll
        box = Frame(self, bg="white")
        box.pack(padx=10, pady=5, fill="both", expand=True)

        self.texto = Text(box, width=100, height=22, wrap="word")
        self.texto.pack(side="left", fill="both", expand=True)

        sb = Scrollbar(box, command=self.texto.yview)
        sb.pack(side="right", fill="y")
        self.texto.configure(yscrollcommand=sb.set)

    # ---------------- Lógica ----------------
    def mostrar_resultados(self):
        try:
            ingresos = Finanzas.listar_ingresos()  # (id, nombre, desc, monto, estado, fecha)
            gastos   = Finanzas.listar_gastos()    # (id, nombre, desc, monto, estado, fecha)
            total_ingresos, total_gastos, utilidad = Finanzas.estado_resultado()
        except Exception as e:
            return messagebox.showerror("❌ Error", f"No se pudo obtener el estado de resultados.\n\n{e}")

        # Orden por fecha DESC si existe (índice 5)
        try:
            ingresos = sorted(ingresos, key=lambda r: (r[5] or ""), reverse=True)
            gastos   = sorted(gastos,   key=lambda r: (r[5] or ""), reverse=True)
        except Exception:
            pass

        self.texto.delete("1.0", END)

        # Ingresos
        self.texto.insert(END, "📋 Ingresos:\n")
        if not ingresos:
            self.texto.insert(END, "  (sin registros)\n")
        else:
            for i in ingresos:
                # i = (id, nombre, descripcion, monto, estado, fecha)
                monto = self._safe_float(i[3])
                estado = i[4] or ""
                fecha = i[5] or ""
                self.texto.insert(END, f"  • {i[1]}  [{estado}]  {fecha}  —  {self._fmt_money(monto)}\n")

        # Gastos
        self.texto.insert(END, "\n💸 Gastos:\n")
        if not gastos:
            self.texto.insert(END, "  (sin registros)\n")
        else:
            for g in gastos:
                monto = self._safe_float(g[3])
                estado = g[4] or ""
                fecha = g[5] or ""
                self.texto.insert(END, f"  • {g[1]}  [{estado}]  {fecha}  —  {self._fmt_money(monto)}\n")

        # Resumen
        self.texto.insert(END, "\n📑 Resumen:\n")
        self.texto.insert(END, f"  🟢 Total Ingresos: {self._fmt_money(total_ingresos)}\n")
        self.texto.insert(END, f"  🔴 Total Gastos:   {self._fmt_money(total_gastos)}\n")
        self.texto.insert(END, f"  💰 Utilidad Neta:  {self._fmt_money(utilidad)}\n")
