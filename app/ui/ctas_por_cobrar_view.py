from tkinter import Frame, Label, Button, messagebox
from tkinter import ttk
from app.models.finanzas import Finanzas

class CtasPorCobrarView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="📋 Cuentas por Cobrar", font=("Arial", 16, "bold")).pack(pady=10)

        # Tabla de cuentas por cobrar
        self.tabla_ctas = ttk.Treeview(self, columns=("ID", "Número", "Cliente", "Monto", "Estado", "Fecha"), show="headings")
        for col in self.tabla_ctas["columns"]:
            self.tabla_ctas.heading(col, text=col)
            self.tabla_ctas.column(col, anchor="center", width=100)
        self.tabla_ctas.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = Frame(self)
        btn_frame.pack(pady=5)

        Button(btn_frame, text="🔄 Actualizar", command=self.cargar_datos).pack(side="left", padx=5)
        Button(btn_frame, text="✅ Marcar como Pagada", command=self.marcar_pagada).pack(side="left", padx=5)

        self.cargar_datos()

    def cargar_datos(self):
        for row in self.tabla_ctas.get_children():
            self.tabla_ctas.delete(row)
        try:
            facturas = Finanzas.listar_facturas()
            ctas_cobrar = [f for f in facturas if f[6] == "cliente" and f[4] in ("pendiente", "vencida")]
            for f in ctas_cobrar:
                self.tabla_ctas.insert("", "end", values=(f[0], f[1], f[2], f[3], f[4], f[5]))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las cuentas por cobrar: {e}")

    def marcar_pagada(self):
        seleccionado = self.tabla_ctas.focus()
        if not seleccionado:
            messagebox.showwarning("Aviso", "Selecciona una cuenta para marcar como pagada.")
            return
        id_factura = self.tabla_ctas.item(seleccionado)["values"][0]
        try:
            Finanzas.cambiar_estado_factura(id_factura, "pagada")
            self.cargar_datos()
            messagebox.showinfo("Éxito", "Factura marcada como pagada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la factura: {e}")
