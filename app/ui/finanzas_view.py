# control_negocio/app/ui/finanzas_view.py

from tkinter import Frame, Label, Entry, Button, Text, END, Toplevel, StringVar
from tkinter import filedialog, messagebox
from tkinter import ttk
from datetime import date
import csv
import matplotlib.pyplot as plt

from app.models.finanzas import Finanzas

class FinanzasView(Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.pack(fill="both", expand=True)
        # IDs seleccionados para cada tabla
        self.ingreso_sel_id = None
        self.gasto_sel_id   = None
        self.fact_sel_id    = None

        # Variables de filtro para facturas
        self.estado_filtro = StringVar(value="todos")
        self.tipo_filtro   = StringVar(value="todos")

        self.crear_widgets()
        self.cargar_ingresos()
        self.cargar_gastos()
        self.cargar_facturas()

    def crear_widgets(self):
        # — Panel superior: Ingresos y Gastos CRUD —
        top = Frame(self, bg="white")
        top.pack(fill="x", padx=10, pady=10)

        # Ingresos CRUD
        ing_frame = Frame(top, bg="white", bd=1, relief="solid")
        ing_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        Label(ing_frame, text="📥 Ingresos", font=("Arial", 14, "bold"), bg="white").pack(pady=5)
        form_ing = Frame(ing_frame, bg="white")
        form_ing.pack(padx=10, pady=5)
        self.ing_fields = {}
        for i, field in enumerate(["Nombre","Descripción","Monto","Estado","Fecha"]):
            Label(form_ing, text=field+":", bg="white").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if field == "Estado":
                w = ttk.Combobox(form_ing, values=["pendiente","recibido","rechazado"], state="readonly", width=22)
                w.set("pendiente")
            else:
                w = Entry(form_ing, width=24)
                if field == "Fecha":
                    w.insert(0, date.today().isoformat())
            w.grid(row=i, column=1, padx=5, pady=2)
            self.ing_fields[field.lower()] = w
        btn_ing = Frame(ing_frame, bg="white")
        btn_ing.pack(pady=5)
        Button(btn_ing, text="Agregar", command=self.registrar_ingreso).pack(side="left", padx=5)
        Button(btn_ing, text="Editar",   command=self.editar_ingreso).pack(side="left", padx=5)
        Button(btn_ing, text="Eliminar", command=self.eliminar_ingreso).pack(side="left", padx=5)
        cols_ing = ("ID","Nombre","Descripción","Monto","Estado","Fecha")
        self.ing_tree = ttk.Treeview(ing_frame, columns=cols_ing, show="headings", height=5)
        for c in cols_ing:
            self.ing_tree.heading(c, text=c)
            self.ing_tree.column(c, width=100, anchor="center")
        self.ing_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.ing_tree.bind("<<TreeviewSelect>>", self._on_ingreso_select)

        # Gastos CRUD
        gas_frame = Frame(top, bg="white", bd=1, relief="solid")
        gas_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        Label(gas_frame, text="📤 Gastos", font=("Arial", 14, "bold"), bg="white").pack(pady=5)
        form_gas = Frame(gas_frame, bg="white")
        form_gas.pack(padx=10, pady=5)
        self.gas_fields = {}
        for i, field in enumerate(["Nombre","Descripción","Monto","Estado","Fecha"]):
            Label(form_gas, text=field+":", bg="white").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if field == "Estado":
                w = ttk.Combobox(form_gas, values=["pendiente","pagado","rechazado"], state="readonly", width=22)
                w.set("pendiente")
            else:
                w = Entry(form_gas, width=24)
                if field == "Fecha":
                    w.insert(0, date.today().isoformat())
            w.grid(row=i, column=1, padx=5, pady=2)
            self.gas_fields[field.lower()] = w
        btn_gas = Frame(gas_frame, bg="white")
        btn_gas.pack(pady=5)
        Button(btn_gas, text="Agregar", command=self.registrar_gasto).pack(side="left", padx=5)
        Button(btn_gas, text="Editar",   command=self.editar_gasto).pack(side="left", padx=5)
        Button(btn_gas, text="Eliminar", command=self.eliminar_gasto).pack(side="left", padx=5)
        cols_gas = ("ID","Nombre","Descripción","Monto","Estado","Fecha")
        self.gas_tree = ttk.Treeview(gas_frame, columns=cols_gas, show="headings", height=5)
        for c in cols_gas:
            self.gas_tree.heading(c, text=c)
            self.gas_tree.column(c, width=100, anchor="center")
        self.gas_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.gas_tree.bind("<<TreeviewSelect>>", self._on_gasto_select)

        # — Panel medio: resumen, gráfico, exportar —
        mid = Frame(self, bg="white")
        mid.pack(fill="x", padx=10, pady=10)
        Button(mid, text="📊 Mostrar Estado de Resultados", command=self.mostrar_estado).pack(side="left", padx=5)
        Button(mid, text="📈 Ver Gráfico",                 command=self.mostrar_grafico).pack(side="left", padx=5)
        Button(mid, text="📤 Exportar a CSV",               command=self.exportar_estado).pack(side="left", padx=5)
        self.resultado = Text(self, width=120, height=10)
        self.resultado.pack(padx=10, pady=5)

        # — Panel inferior: Facturas CRUD —
        bot = Frame(self, bg="white")
        bot.pack(fill="both", expand=True, padx=10, pady=10)
        Label(bot, text="📄 Facturas", font=("Arial", 14, "bold"), bg="white").pack(anchor="w")
        fact_btn = Frame(bot, bg="white")
        fact_btn.pack(anchor="w", pady=5)
        Button(fact_btn, text="➕ Agregar Factura",   command=lambda: self.abrir_formulario_factura(edit=False)).pack(side="left", padx=5)
        Button(fact_btn, text="✏️ Editar Factura",    command=lambda: self.abrir_formulario_factura(edit=True)).pack(side="left", padx=5)
        Button(fact_btn, text="🗑️ Eliminar Factura",  command=self.eliminar_factura).pack(side="left", padx=5)
        Button(fact_btn, text="🔄 Refrescar",         command=self.cargar_facturas).pack(side="left", padx=5)
        Label(fact_btn, text="Estado:", bg="white").pack(side="left", padx=5)
        cb1 = ttk.Combobox(fact_btn, textvariable=self.estado_filtro, values=["todos","pendiente","pagada","vencida"], width=12)
        cb1.pack(side="left"); cb1.bind("<<ComboboxSelected>>", lambda e: self.cargar_facturas())
        Label(fact_btn, text="Tipo:", bg="white").pack(side="left", padx=5)
        cb2 = ttk.Combobox(fact_btn, textvariable=self.tipo_filtro, values=["todos","proveedor","cliente"], width=12)
        cb2.pack(side="left"); cb2.bind("<<ComboboxSelected>>", lambda e: self.cargar_facturas())

        cols_f = ("ID","Número","Proveedor/Cliente","Monto","Estado","Fecha","Tipo")
        self.fact_tree = ttk.Treeview(bot, columns=cols_f, show="headings")
        for c in cols_f:
            self.fact_tree.heading(c, text=c)
            self.fact_tree.column(c, width=100, anchor="center")
        self.fact_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.fact_tree.bind("<<TreeviewSelect>>", self._on_factura_select)

    # — Ingresos CRUD —  
    def cargar_ingresos(self):
        for r in self.ing_tree.get_children():
            self.ing_tree.delete(r)
        for i in Finanzas.listar_ingresos():
            self.ing_tree.insert("", END, values=i)

    def _on_ingreso_select(self, event):
        sel = self.ing_tree.selection()
        if not sel:
            self.ingreso_sel_id = None
            return
        vals = self.ing_tree.item(sel[0])["values"]
        self.ingreso_sel_id = vals[0]
        for idx, key in enumerate(["nombre","descripción","monto","estado","fecha"], start=1):
            self.ing_fields[key].delete(0, END)
            self.ing_fields[key].insert(0, vals[idx])

    def registrar_ingreso(self):
        try:
            f = self.ing_fields
            Finanzas.registrar_ingreso(
                f["nombre"].get(), f["descripción"].get(),
                float(f["monto"].get()), f["estado"].get(),
                f["fecha"].get()
            )
            self.cargar_ingresos()
        except Exception as e:
            messagebox.showerror("Error", e)

    def editar_ingreso(self):
        if not self.ingreso_sel_id:
            return messagebox.showwarning("Atención", "Selecciona un ingreso.")
        try:
            f = self.ing_fields
            Finanzas.editar_ingreso(
                self.ingreso_sel_id,
                f["nombre"].get(), f["descripción"].get(),
                float(f["monto"].get()), f["estado"].get(),
                f["fecha"].get()
            )
            self.cargar_ingresos()
        except Exception as e:
            messagebox.showerror("Error al editar ingreso", e)

    def eliminar_ingreso(self):
        if not self.ingreso_sel_id:
            return messagebox.showwarning("Atención", "Selecciona un ingreso.")
        if messagebox.askyesno("Confirmar", "¿Eliminar ingreso?"):
            Finanzas.eliminar_ingreso(self.ingreso_sel_id)
            self.cargar_ingresos()

    # — Gastos CRUD —  
    def cargar_gastos(self):
        for r in self.gas_tree.get_children():
            self.gas_tree.delete(r)
        for g in Finanzas.listar_gastos():
            self.gas_tree.insert("", END, values=g)

    def _on_gasto_select(self, event):
        sel = self.gas_tree.selection()
        if not sel:
            self.gasto_sel_id = None
            return
        vals = self.gas_tree.item(sel[0])["values"]
        self.gasto_sel_id = vals[0]
        for idx, key in enumerate(["nombre","descripción","monto","estado","fecha"], start=1):
            self.gas_fields[key].delete(0, END)
            self.gas_fields[key].insert(0, vals[idx])

    def registrar_gasto(self):
        try:
            f = self.gas_fields
            Finanzas.registrar_gasto(
                f["nombre"].get(), f["descripción"].get(),
                float(f["monto"].get()), f["estado"].get(),
                f["fecha"].get()
            )
            self.cargar_gastos()
        except Exception as e:
            messagebox.showerror("Error", e)

    def editar_gasto(self):
        if not self.gasto_sel_id:
            return messagebox.showwarning("Atención", "Selecciona un gasto.")
        try:
            f = self.gas_fields
            Finanzas.editar_gasto(
                self.gasto_sel_id,
                f["nombre"].get(), f["descripción"].get(),
                float(f["monto"].get()), f["estado"].get(),
                f["fecha"].get()
            )
            self.cargar_gastos()
        except Exception as e:
            messagebox.showerror("Error al editar gasto", e)

    def eliminar_gasto(self):
        if not self.gasto_sel_id:
            return messagebox.showwarning("Atención", "Selecciona un gasto.")
        if messagebox.askyesno("Confirmar", "¿Eliminar gasto?"):
            Finanzas.eliminar_gasto(self.gasto_sel_id)
            self.cargar_gastos()

    # — Resumen / Gráfico / Exportación —  
    def mostrar_estado(self):
        ingresos_nf = [i for i in Finanzas.listar_ingresos() if i[4]=="recibido"]
        fact_list   = Finanzas.listar_facturas()
        fact_cob    = [f for f in fact_list if f[6]=="cliente"  and f[4]=="pagada"]
        gastos_nf   = [g for g in Finanzas.listar_gastos()  if g[4]=="pagado"]
        fact_prov   = [f for f in fact_list if f[6]=="proveedor" and f[4]=="pagada"]

        tot_ing = sum(i[3] for i in ingresos_nf) + sum(f[3] for f in fact_cob)
        tot_gas = sum(g[3] for g in gastos_nf)   + sum(f[3] for f in fact_prov)
        util    = tot_ing - tot_gas

        self.resultado.delete("1.0", END)
        self.resultado.insert(END, "📋 Ingresos pequeños:\n")
        for i in ingresos_nf: self.resultado.insert(END, f"- {i[1]}: ${i[3]:,.2f}\n")
        self.resultado.insert(END, "\n📜 Facturas cliente pagadas:\n")
        for f in fact_cob:    self.resultado.insert(END, f"- {f[1]}: ${f[3]:,.2f}\n")
        self.resultado.insert(END, "\n💸 Gastos pequeños:\n")
        for g in gastos_nf:   self.resultado.insert(END, f"- {g[1]}: ${g[3]:,.2f}\n")
        self.resultado.insert(END, "\n🧾 Facturas prov. pagadas:\n")
        for f in fact_prov:   self.resultado.insert(END, f"- {f[1]}: ${f[3]:,.2f}\n")
        self.resultado.insert(END, "\n📊 Resumen:\n")
        self.resultado.insert(END, f"🟢 Ingresos totales: ${tot_ing:,.2f}\n")
        self.resultado.insert(END, f"🔴 Gastos totales:   ${tot_gas:,.2f}\n")
        self.resultado.insert(END, f"💰 Utilidad neta:    ${util:,.2f}\n")

    def mostrar_grafico(self):
        ingresos_nf   = sum(i[3] for i in Finanzas.listar_ingresos() if i[4]=="recibido")
        total_ing_fc  = sum(f[3] for f in Finanzas.listar_facturas() if f[6]=="cliente"  and f[4]=="pagada")
        gastos_nf     = sum(g[3] for g in Finanzas.listar_gastos()  if g[4]=="pagado")
        total_gas_fp  = sum(f[3] for f in Finanzas.listar_facturas() if f[6]=="proveedor" and f[4]=="pagada")
        util          = (ingresos_nf + total_ing_fc) - (gastos_nf + total_gas_fp)

        etiquetas = ["Ing Peq","Fact Cli","Gas Peq","Fact Prov","Utilidad"]
        valores   = [ingresos_nf, total_ing_fc, gastos_nf, total_gas_fp, util]

        plt.figure(figsize=(6,4))
        plt.bar(etiquetas, valores)
        plt.title("Estado Financiero")
        plt.ylabel("Monto CLP")
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()

    def exportar_estado(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not ruta: return
        ingresos_nf = [i for i in Finanzas.listar_ingresos() if i[4]=="recibido"]
        fact_cob    = [f for f in Finanzas.listar_facturas()    if f[6]=="cliente"  and f[4]=="pagada"]
        gastos_nf   = [g for g in Finanzas.listar_gastos()      if g[4]=="pagado"]
        fact_prov   = [f for f in Finanzas.listar_facturas()    if f[6]=="proveedor" and f[4]=="pagada"]

        with open(ruta,"w",newline="") as f:
            w = csv.writer(f)
            w.writerow(["Tipo","Desc","Monto","Estado","Fecha"])
            for i in ingresos_nf: w.writerow(["Ingreso Peq", i[1], i[3], i[4], i[5]])
            for fc in fact_cob:   w.writerow(["Fact Cli", fc[1], fc[3], fc[4], fc[5]])
            for g in gastos_nf:   w.writerow(["Gas Peq", g[1], g[3], g[4], g[5]])
            for fp in fact_prov:  w.writerow(["Fact Prov", fp[1], fp[3], fp[4], fp[5]])
        messagebox.showinfo("Exportación","Estado exportado exitosamente.")

    # — Facturas CRUD —  
    def cargar_facturas(self):
        for r in self.fact_tree.get_children():
            self.fact_tree.delete(r)
        facturas = Finanzas.listar_facturas()
        if self.estado_filtro.get()!="todos":
            facturas = [f for f in facturas if f[4]==self.estado_filtro.get()]
        if self.tipo_filtro.get()!="todos":
            facturas = [f for f in facturas if f[6]==self.tipo_filtro.get()]
        for f in facturas:
            self.fact_tree.insert("", END, values=f)

    def _on_factura_select(self, event):
        sel = self.fact_tree.selection()
        self.fact_sel_id = self.fact_tree.item(sel[0])["values"][0] if sel else None

    def abrir_formulario_factura(self, edit=False):
        """Abre un Toplevel para agregar o editar una factura."""
        ventana = Toplevel(self)
        ventana.title("Editar Factura" if edit else "Agregar Factura")
        campos = ["Número","Proveedor/Cliente","Monto","Estado","Fecha (YYYY-MM-DD)","Tipo de factura"]
        entradas = {}
        for i, campo in enumerate(campos):
            Label(ventana, text=campo).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if campo == "Estado":
                w = ttk.Combobox(ventana, values=["pendiente","pagada","vencida"], state="readonly", width=22)
                w.set("pendiente")
            elif campo == "Tipo de factura":
                w = ttk.Combobox(ventana, values=["proveedor","cliente"], state="readonly", width=22)
                w.set("cliente")
            else:
                w = Entry(ventana, width=24)
                if campo.startswith("Fecha"):
                    w.insert(0, date.today().isoformat())
            w.grid(row=i, column=1, padx=5, pady=2)
            entradas[campo] = w

        if edit:
            if not self.fact_sel_id:
                messagebox.showwarning("Atención", "Selecciona una factura para editar.")
                ventana.destroy()
                return
            # precargar valores
            rec = next(r for r in Finanzas.listar_facturas() if r[0]==self.fact_sel_id)
            # rec = (id, número, proveedor, monto, estado, fecha, tipo)
            entradas["Número"].delete(0, END);           entradas["Número"].insert(0, rec[1])
            entradas["Proveedor/Cliente"].delete(0, END); entradas["Proveedor/Cliente"].insert(0, rec[2])
            entradas["Monto"].delete(0, END);            entradas["Monto"].insert(0, rec[3])
            entradas["Estado"].set(rec[4])
            entradas["Fecha (YYYY-MM-DD)"].delete(0, END); entradas["Fecha (YYYY-MM-DD)"].insert(0, rec[5])
            entradas["Tipo de factura"].set(rec[6])

        def guardar():
            numero  = entradas["Número"].get().strip()
            tercero = entradas["Proveedor/Cliente"].get().strip()
            monto   = float(entradas["Monto"].get())
            estado  = entradas["Estado"].get()
            fecha   = entradas["Fecha (YYYY-MM-DD)"].get()
            tipo    = entradas["Tipo de factura"].get()
            try:
                if edit:
                    Finanzas.editar_factura(
                        self.fact_sel_id, numero, tercero, monto, estado, fecha, tipo
                    )
                else:
                    Finanzas.registrar_factura(numero, tercero, monto, estado, fecha, tipo)
                ventana.destroy()
                self.cargar_facturas()
                self.mostrar_estado()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar factura: {e}")

        Button(ventana, text="Guardar", command=guardar).grid(row=len(campos), column=1, pady=10)

    def eliminar_factura(self):
        if not self.fact_sel_id:
            return messagebox.showwarning("Atención", "Selecciona una factura para eliminar.")
        if messagebox.askyesno("Confirmar", "¿Eliminar factura?"):
            Finanzas.eliminar_factura(self.fact_sel_id)
            self.cargar_facturas()
