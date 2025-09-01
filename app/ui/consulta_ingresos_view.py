# app/ui/consulta_ingresos_view.py

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from app.models.finanzas import Finanzas


class ConsultaIngresosView(tk.Frame):
    """
    Vista de consulta de ingresos:
    - No hace pack/place/grid en __init__ (lo maneja MainWindow).
    - Tabla con scroll y columnas claras (incluye descripción).
    - Filtro por estado (Todos | recibido | pendiente | pagado | ...).
    - Formato de montos con separador de miles.
    """

    COLS = ("id", "nombre", "descripcion", "monto", "estado", "fecha")

    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.var_estado = tk.StringVar(value="Todos")
        self._build_ui()
        # Carga inicial deferida para asegurar layout listo
        self.after(0, self.cargar_datos)

    # ---------------- UI ----------------

    def _build_ui(self):
        tk.Label(
            self,
            text="🧾 Consulta de Ingresos",
            font=("Segoe UI", 16, "bold"),
            bg="white",
        ).pack(pady=10)

        toolbar = tk.Frame(self, bg="white")
        toolbar.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(toolbar, text="Estado:", bg="white").pack(side="left", padx=(0, 6))
        self.cmb_estado = ttk.Combobox(
            toolbar,
            textvariable=self.var_estado,
            state="readonly",
            width=18,
            values=["Todos", "recibido", "pendiente", "pagado", "anulado"],
        )
        self.cmb_estado.pack(side="left")
        self.cmb_estado.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        ttk.Button(toolbar, text="Recargar", command=self.cargar_datos, width=12).pack(
            side="right"
        )

        # Contenedor de tabla + scroll
        table_box = tk.Frame(self, bg="white")
        table_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_box, columns=self.COLS, show="headings")
        # Headings
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.heading("monto", text="Monto")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("fecha", text="Fecha")

        # Column sizing/alignment
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("nombre", width=180, anchor="w")
        self.tree.column("descripcion", width=260, anchor="w")
        self.tree.column("monto", width=120, anchor="e")
        self.tree.column("estado", width=110, anchor="center")
        self.tree.column("fecha", width=120, anchor="center")

        yscroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        yscroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(fill="both", expand=True)

        # Total
        self.monto_total_lbl = tk.Label(
            self, text="", bg="white", font=("Segoe UI", 12, "bold"), anchor="e"
        )
        self.monto_total_lbl.pack(fill="x", padx=12, pady=(0, 10))

    # ------------- Datos -------------

    def _formato_money(self, x) -> str:
        try:
            val = float(x or 0)
        except Exception:
            val = 0.0
        # Si trabajas sin decimales en CLP, cambia a: f"${val:,.0f}"
        return f"${val:,.2f}"

    def _filtrar_por_estado(self, filas):
        estado = self.var_estado.get()
        if not filas:
            return filas
        if estado == "Todos":
            return filas
        # filas: (id, nombre, descripcion, monto, estado, fecha)
        return [f for f in filas if (f[4] or "").strip().lower() == estado.lower()]

    def cargar_datos(self):
        try:
            # Limpia tabla
            for r in self.tree.get_children():
                self.tree.delete(r)

            ingresos = Finanzas.listar_ingresos()  # (id, nombre, descripcion, monto, estado, fecha)
            ingresos = self._filtrar_por_estado(ingresos)

            total = 0.0
            for i in ingresos:
                # i = (id, nombre, descripcion, monto, estado, fecha)
                try:
                    monto_f = float(i[3] or 0)
                except Exception:
                    monto_f = 0.0
                total += monto_f
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        i[0],
                        i[1],
                        i[2] or "",
                        self._formato_money(monto_f),
                        i[4] or "",
                        i[5] or "",
                    ),
                )

            self.monto_total_lbl.config(text=f"Total ingresado (filtro: {self.var_estado.get()}): {self._formato_money(total)}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los ingresos.\n\n{e}")
