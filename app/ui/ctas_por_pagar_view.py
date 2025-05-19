from tkinter import Frame, Label, Button, messagebox
from tkinter import ttk
from app.models.finanzas import Finanzas

class CtasPorPagarView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="📄 Cuentas por Pagar (Proveedores)", font=("Arial", 14, "bold")).pack(pady=10)

        self.tabla = ttk.Treeview(self, columns=("ID", "Número", "Proveedor", "Monto", "Estado", "Fecha"), show="headings")
        for col in ("ID", "Número", "Proveedor", "Monto", "Estado", "Fecha"):
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center", width=100)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = Frame(self)
        btn_frame.pack(pady=5)
        Button(btn_frame, text="🔄 Actualizar", command=self.cargar_facturas).pack(side="left", padx=5)
        Button(btn_frame, text="💵 Marcar como Pagada", command=self.marcar_pagada).pack(side="left", padx=5)

        self.cargar_facturas()

    def cargar_facturas(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        try:
            facturas = Finanzas.listar_facturas()
            pendientes = [f for f in facturas if f[6] == "proveedor" and f[4] in ("pendiente", "vencida")]
            for f in pendientes:
                self.tabla.insert("", "end", values=(f[0], f[1], f[2], f[3], f[4], f[5]))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las facturas: {str(e)}")

    def marcar_pagada(self):
        seleccionado = self.tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona una factura para marcar como pagada.")
            return
        id_factura = self.tabla.item(seleccionado)['values'][0]
        try:
            Finanzas.cambiar_estado_factura(id_factura, "pagada")
            self.cargar_facturas()
            messagebox.showinfo("Éxito", "Factura marcada como pagada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la factura: {e}")
