from tkinter import Frame, Label, Entry, Button, Text, END, Toplevel, StringVar
from tkinter import ttk, messagebox, filedialog
from datetime import date
from app.models.finanzas import Finanzas
import csv
import matplotlib.pyplot as plt

class FinanzasView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.estado_filtro = StringVar(value="todos")
        self.tipo_filtro = StringVar(value="todos")
        self.crear_widgets()

    def crear_widgets(self):
        frame_top = Frame(self)
        frame_top.pack(fill="x", padx=10, pady=10)

        # Ingresos
        frame_ingreso = Frame(frame_top)
        frame_ingreso.pack(side="left", padx=20)
        Label(frame_ingreso, text="📥 Registro de Ingreso", font=("Arial", 12, "bold")).pack(anchor="w")
        self.nombre_ingreso = Entry(frame_ingreso, width=30)
        self.descripcion_ingreso = Entry(frame_ingreso, width=30)
        self.monto_ingreso = Entry(frame_ingreso, width=20)
        self.estado_ingreso = ttk.Combobox(frame_ingreso, values=["pendiente", "recibido", "rechazado"], width=18)
        self.estado_ingreso.set("pendiente")

        for label, widget in zip(["Nombre:", "Descripción:", "Monto:", "Estado:"],
                                 [self.nombre_ingreso, self.descripcion_ingreso, self.monto_ingreso, self.estado_ingreso]):
            Label(frame_ingreso, text=label).pack(anchor="w")
            widget.pack()

        Button(frame_ingreso, text="Registrar Ingreso", command=self.registrar_ingreso).pack(pady=5)

        # Gastos
        frame_gasto = Frame(frame_top)
        frame_gasto.pack(side="left", padx=20)
        Label(frame_gasto, text="📤 Registro de Gasto", font=("Arial", 12, "bold")).pack(anchor="w")
        self.nombre_gasto = Entry(frame_gasto, width=30)
        self.descripcion_gasto = Entry(frame_gasto, width=30)
        self.monto_gasto = Entry(frame_gasto, width=20)
        self.estado_gasto = ttk.Combobox(frame_gasto, values=["pendiente", "pagado", "rechazado"], width=18)
        self.estado_gasto.set("pendiente")

        for label, widget in zip(["Nombre:", "Descripción:", "Monto:", "Estado:"],
                                 [self.nombre_gasto, self.descripcion_gasto, self.monto_gasto, self.estado_gasto]):
            Label(frame_gasto, text=label).pack(anchor="w")
            widget.pack()

        Button(frame_gasto, text="Registrar Gasto", command=self.registrar_gasto).pack(pady=5)

        # Acciones
        for text, cmd in [
            ("📊 Mostrar Estado de Resultados", self.mostrar_estado),
            ("📈 Ver Gráfico de Finanzas", self.mostrar_grafico),
            ("📤 Exportar Estado a Excel", self.exportar_estado),
        ]:
            Button(self, text=text, command=cmd).pack(pady=4)

        self.resultado = Text(self, width=100, height=12)
        self.resultado.pack(padx=10, pady=5)

        # Facturas
        Label(self, text="📄 Gestión de Facturas", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        frame_facturas_btn = Frame(self)
        frame_facturas_btn.pack(anchor="w", padx=10, pady=(0, 5))

        Button(frame_facturas_btn, text="➕ Agregar Factura", command=self.abrir_formulario_factura).pack(side="left")
        Button(frame_facturas_btn, text="🔄 Actualizar Estado", command=self.actualizar_estado_factura).pack(side="left", padx=10)

        for label, var, values in [
            ("Estado:", self.estado_filtro, ["todos", "pendiente", "pagada", "vencida"]),
            ("Tipo:", self.tipo_filtro, ["todos", "proveedor", "cliente"]),
        ]:
            Label(frame_facturas_btn, text=label).pack(side="left", padx=5)
            cb = ttk.Combobox(frame_facturas_btn, textvariable=var, values=values, width=12)
            cb.pack(side="left")
            cb.bind("<<ComboboxSelected>>", lambda e: self.cargar_facturas())

        self.tabla_facturas = ttk.Treeview(self, columns=("ID", "Número", "Proveedor", "Monto", "Estado", "Fecha", "Tipo"), show="headings")
        for col in self.tabla_facturas["columns"]:
            self.tabla_facturas.heading(col, text=col)
            self.tabla_facturas.column(col, anchor="center", width=100)
        self.tabla_facturas.pack(fill="both", expand=True, padx=10, pady=5)
        self.cargar_facturas()

    def registrar_ingreso(self):
        try:
            Finanzas.registrar_ingreso(
                self.nombre_ingreso.get(),
                self.descripcion_ingreso.get(),
                float(self.monto_ingreso.get()),
                self.estado_ingreso.get()
            )
            self.resultado.insert(END, "✅ Ingreso registrado correctamente.\n")
            self.limpiar_ingreso()
        except Exception as e:
            messagebox.showerror("Error", f"Ingreso no válido: {e}")

    def registrar_gasto(self):
        try:
            Finanzas.registrar_gasto(
                self.nombre_gasto.get(),
                self.descripcion_gasto.get(),
                float(self.monto_gasto.get()),
                self.estado_gasto.get()
            )
            self.resultado.insert(END, "✅ Gasto registrado correctamente.\n")
            self.limpiar_gasto()
        except Exception as e:
            messagebox.showerror("Error", f"Gasto no válido: {e}")

    def limpiar_ingreso(self):
        for w in [self.nombre_ingreso, self.descripcion_ingreso, self.monto_ingreso]:
            w.delete(0, END)
        self.estado_ingreso.set("pendiente")

    def limpiar_gasto(self):
        for w in [self.nombre_gasto, self.descripcion_gasto, self.monto_gasto]:
            w.delete(0, END)
        self.estado_gasto.set("pendiente")

    def mostrar_estado(self):
        ingresos = Finanzas.listar_ingresos()
        gastos = Finanzas.listar_gastos()
        total_ingresos, total_gastos, utilidad = Finanzas.estado_resultado()

        self.resultado.delete("1.0", END)
        self.resultado.insert(END, "📋 Ingresos Recibidos:\n")
        for i in ingresos:
            if i[4] == "recibido":
                self.resultado.insert(END, f"- {i[1]}: ${i[3]}\n")

        self.resultado.insert(END, "\n💸 Gastos Pagados:\n")
        for g in gastos:
            if g[4] == "pagado":
                self.resultado.insert(END, f"- {g[1]}: ${g[3]}\n")

        self.resultado.insert(END, f"\n📊 Estado de Resultados:\n")
        self.resultado.insert(END, f"🟢 Total Ingresos: ${total_ingresos}\n")
        self.resultado.insert(END, f"🔴 Total Gastos (incluye facturas pagadas): ${total_gastos}\n")
        self.resultado.insert(END, f"💰 Utilidad Neta: ${utilidad}\n")

    def mostrar_grafico(self):
        ingresos, gastos, utilidad = Finanzas.estado_resultado()
        plt.figure(figsize=(6, 4))
        plt.bar(["Ingresos", "Gastos", "Utilidad"], [ingresos, gastos, utilidad], color=["green", "red", "blue"])
        plt.title("Estado Financiero")
        plt.ylabel("Monto CLP")
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()

    def exportar_estado(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not ruta: return

        ingresos = Finanzas.listar_ingresos()
        gastos = Finanzas.listar_gastos()
        facturas = Finanzas.listar_facturas()

        with open(ruta, mode='w', newline='') as archivo:
            writer = csv.writer(archivo)
            writer.writerow(["Tipo", "Nombre/Descripción", "Monto", "Estado", "Fecha"])
            for i in ingresos:
                writer.writerow(["Ingreso", i[1], i[3], i[4], i[5]])
            for g in gastos:
                writer.writerow(["Gasto", g[1], g[3], g[4], g[5]])
            for f in facturas:
                writer.writerow(["Factura " + f[6].capitalize(), f[2], f[3], f[4], f[5]])

        messagebox.showinfo("Exportación completa", "📁 Estado exportado exitosamente.")

    def cargar_facturas(self):
        for row in self.tabla_facturas.get_children():
            self.tabla_facturas.delete(row)

        facturas = Finanzas.listar_facturas()
        if self.estado_filtro.get() != "todos":
            facturas = [f for f in facturas if f[4] == self.estado_filtro.get()]
        if self.tipo_filtro.get() != "todos":
            facturas = [f for f in facturas if f[6] == self.tipo_filtro.get()]
        for f in facturas:
            self.tabla_facturas.insert("", "end", values=f)

    def abrir_formulario_factura(self):
        ventana = Toplevel(self)
        ventana.title("Agregar Factura")

        campos = ["Número", "Proveedor/Cliente", "Monto", "Estado", "Fecha (YYYY-MM-DD)", "Tipo de factura"]
        entradas = []
        for i, campo in enumerate(campos):
            Label(ventana, text=campo).grid(row=i, column=0)
            entry = ttk.Combobox(ventana, values=["pendiente", "pagada", "vencida"]) if campo == "Estado" else \
                    ttk.Combobox(ventana, values=["proveedor", "cliente"]) if campo == "Tipo de factura" else Entry(ventana)
            entry.grid(row=i, column=1)
            if campo == "Fecha (YYYY-MM-DD)":
                entry.insert(0, str(date.today()))
            entradas.append(entry)

        def guardar():
            try:
                Finanzas.registrar_factura(
                    entradas[0].get(), entradas[1].get(), float(entradas[2].get()),
                    entradas[3].get(), entradas[4].get(), entradas[5].get()
                )
                ventana.destroy()
                self.cargar_facturas()
                self.mostrar_estado()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

        Button(ventana, text="Guardar", command=guardar).grid(row=6, column=1, pady=10)

    def actualizar_estado_factura(self):
        seleccionado = self.tabla_facturas.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona una factura.")
            return
        id_factura = self.tabla_facturas.item(seleccionado)['values'][0]
        ventana = Toplevel(self)
        ventana.title("Cambiar Estado")
        Label(ventana, text="Nuevo estado: ").grid(row=0, column=0)
        nuevo_estado = ttk.Combobox(ventana, values=["pendiente", "pagada", "vencida"])
        nuevo_estado.grid(row=0, column=1)

        Button(ventana, text="Aplicar", command=lambda: self.aplicar_estado_factura(id_factura, nuevo_estado.get(), ventana)).grid(row=1, column=1, pady=10)

    def aplicar_estado_factura(self, id_factura, nuevo_estado, ventana):
        Finanzas.cambiar_estado_factura(id_factura, nuevo_estado)
        ventana.destroy()
        self.cargar_facturas()
        self.mostrar_estado()
