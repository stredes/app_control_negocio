import tkinter as tk
from tkinter import Frame, Label, Entry, Button, messagebox, StringVar
from tkinter import ttk
from datetime import date
from app.models.finanzas import Finanzas

class CtasPorCobrarView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill="both", expand=True)

        self.cta_sel_id    = None
        self.estado_filtro = StringVar(self, value="todos")

        self.crear_widgets()
        self.cargar_ctas()

    def crear_widgets(self):
        Label(self, text="📋 Cuentas por Cobrar", font=("Arial", 16, "bold"), bg="white")\
            .pack(pady=10)

        form = Frame(self, bg="white")
        form.pack(padx=10, pady=5, anchor="w")

        # Campos
        Label(form, text="Número:", bg="white").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.ent_numero  = Entry(form, width=20)
        self.ent_numero.grid(row=0, column=1, padx=5, pady=2)

        Label(form, text="Cliente:", bg="white").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.ent_cliente = Entry(form, width=20)
        self.ent_cliente.grid(row=1, column=1, padx=5, pady=2)

        Label(form, text="Monto:", bg="white").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.ent_monto   = Entry(form, width=20)
        self.ent_monto.grid(row=2, column=1, padx=5, pady=2)

        Label(form, text="Estado:", bg="white").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.cmb_estado  = ttk.Combobox(
            form,
            values=["pendiente","pagada","vencida"],
            state="readonly",
            width=18
        )
        self.cmb_estado.grid(row=3, column=1, padx=5, pady=2)
        self.cmb_estado.set("pendiente")

        Label(form, text="Fecha:", bg="white").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.ent_fecha   = Entry(form, width=20)
        self.ent_fecha.grid(row=4, column=1, padx=5, pady=2)
        self.ent_fecha.insert(0, date.today().isoformat())

        # Botones CRUD
        btns = Frame(self, bg="white")
        btns.pack(pady=5)
        Button(btns, text="➕ Agregar",  command=self.agregar_cta).pack(side="left", padx=5)
        Button(btns, text="✏️ Editar",  command=self.editar_cta).pack(side="left", padx=5)
        Button(btns, text="🗑️ Eliminar",command=self.eliminar_cta).pack(side="left", padx=5)
        Button(btns, text="🔄 Refrescar",command=self.cargar_ctas).pack(side="left", padx=5)

        # Filtro por estado
        Label(btns, text="Estado:", bg="white").pack(side="left", padx=5)
        cb = ttk.Combobox(
            btns,
            textvariable=self.estado_filtro,
            values=["todos","pendiente","pagada","vencida"],
            width=12
        )
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.cargar_ctas())

        # Tabla
        cols = ("ID","Número","Cliente","Monto","Estado","Fecha")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            self.cta_sel_id = None
            return
        id_, num, cli, mon, est, fech = self.tree.item(sel[0])["values"]
        self.cta_sel_id = id_
        self.ent_numero.delete(0, tk.END);  self.ent_numero.insert(0, num)
        self.ent_cliente.delete(0, tk.END); self.ent_cliente.insert(0, cli)
        self.ent_monto.delete(0, tk.END);   self.ent_monto.insert(0, mon)
        self.cmb_estado.set(est)
        self.ent_fecha.delete(0, tk.END);   self.ent_fecha.insert(0, fech)

    def agregar_cta(self):
        try:
            Finanzas.registrar_factura(
                self.ent_numero.get(),
                self.ent_cliente.get(),
                float(self.ent_monto.get()),
                self.cmb_estado.get(),
                self.ent_fecha.get(),
                "cliente"
            )
            self.cargar_ctas()
        except Exception as e:
            messagebox.showerror("Error", e)

    def editar_cta(self):
        if not self.cta_sel_id:
            return messagebox.showwarning("Atención","Selecciona una cuenta.")
        try:
            Finanzas.editar_factura(
                self.cta_sel_id,
                self.ent_numero.get(),
                self.ent_cliente.get(),
                float(self.ent_monto.get()),
                self.cmb_estado.get(),
                self.ent_fecha.get(),
                "cliente"
            )
            self.cargar_ctas()
        except Exception as e:
            messagebox.showerror("Error", e)

    def eliminar_cta(self):
        if not self.cta_sel_id:
            return messagebox.showwarning("Atención","Selecciona una cuenta.")
        if messagebox.askyesno("Confirmar","¿Eliminar?"):
            Finanzas.eliminar_factura(self.cta_sel_id)
            self.cargar_ctas()

    def cargar_ctas(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        facturas = [f for f in Finanzas.listar_facturas() if f[6] == "cliente"]
        if self.estado_filtro.get() != "todos":
            facturas = [f for f in facturas if f[4] == self.estado_filtro.get()]
        for f in facturas:
            self.tree.insert("", tk.END, values=(f[0], f[1], f[2], f[3], f[4], f[5]))
