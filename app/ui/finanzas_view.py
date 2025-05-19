from tkinter import Frame, Label, Entry, Button, Text, Scrollbar, END, Toplevel, StringVar
from tkinter import ttk, messagebox, filedialog
from datetime import date
from app.models.finanzas import Finanzas
import csv
import matplotlib.pyplot as plt

class FinanzasView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.estado_filtro = StringVar()
        self.estado_filtro.set("todos")
        self.tipo_filtro = StringVar()
        self.tipo_filtro.set("todos")
        self.crear_widgets()

    def crear_widgets(self):
        # Frame superior para ingresos y gastos
        frame_top = Frame(self)
        frame_top.pack(fill="x", padx=10, pady=10)

        frame_ingreso = Frame(frame_top)
        frame_ingreso.pack(side="left", padx=20, anchor="n")

        Label(frame_ingreso, text="📥 Registro de Ingreso", font=("Arial", 12, "bold")).pack(anchor="w")
        Label(frame_ingreso, text="Descripción:").pack(anchor="w")
        self.descripcion_ingreso = Entry(frame_ingreso, width=30)
        self.descripcion_ingreso.pack()
        Label(frame_ingreso, text="Monto:").pack(anchor="w")
        self.monto_ingreso = Entry(frame_ingreso, width=20)
        self.monto_ingreso.pack()
        Button(frame_ingreso, text="Registrar Ingreso", command=self.registrar_ingreso).pack(pady=5)

        frame_gasto = Frame(frame_top)
        frame_gasto.pack(side="left", padx=20, anchor="n")

        Label(frame_gasto, text="📤 Registro de Gasto", font=("Arial", 12, "bold")).pack(anchor="w")
        Label(frame_gasto, text="Descripción:").pack(anchor="w")
        self.descripcion_gasto = Entry(frame_gasto, width=30)
        self.descripcion_gasto.pack()
        Label(frame_gasto, text="Monto:").pack(anchor="w")
        self.monto_gasto = Entry(frame_gasto, width=20)
        self.monto_gasto.pack()
        Button(frame_gasto, text="Registrar Gasto", command=self.registrar_gasto).pack(pady=5)

        Button(self, text="📊 Mostrar Estado de Resultados", command=self.mostrar_estado).pack(pady=10)
        Button(self, text="📈 Ver Gráfico de Finanzas", command=self.mostrar_grafico).pack(pady=5)
        Button(self, text="📤 Exportar Estado a Excel", command=self.exportar_estado).pack(pady=5)

        self.resultado = Text(self, width=100, height=10)
        self.resultado.pack(padx=10, pady=5)

        # Tabla de facturas
        Label(self, text="📄 Gestión de Facturas", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)

        frame_facturas_btn = Frame(self)
        frame_facturas_btn.pack(anchor="w", padx=10, pady=(0, 5))
        Button(frame_facturas_btn, text="➕ Agregar Factura", command=self.abrir_formulario_factura).pack(side="left")
        Button(frame_facturas_btn, text="🔄 Actualizar Estado", command=self.actualizar_estado_factura).pack(side="left", padx=10)

        Label(frame_facturas_btn, text="Estado:").pack(side="left", padx=10)
        filtro_estado_cb = ttk.Combobox(frame_facturas_btn, textvariable=self.estado_filtro, values=["todos", "pendiente", "pagada", "vencida"], width=12)
        filtro_estado_cb.pack(side="left")
        filtro_estado_cb.bind("<<ComboboxSelected>>", lambda e: self.cargar_facturas())

        Label(frame_facturas_btn, text="Tipo:").pack(side="left", padx=10)
        filtro_tipo_cb = ttk.Combobox(frame_facturas_btn, textvariable=self.tipo_filtro, values=["todos", "proveedor", "cliente"], width=12)
        filtro_tipo_cb.pack(side="left")
        filtro_tipo_cb.bind("<<ComboboxSelected>>", lambda e: self.cargar_facturas())

        self.tabla_facturas = ttk.Treeview(self, columns=("ID", "Número", "Proveedor", "Monto", "Estado", "Fecha", "Tipo"), show="headings")
        for col in ("ID", "Número", "Proveedor", "Monto", "Estado", "Fecha", "Tipo"):
            self.tabla_facturas.heading(col, text=col)
            self.tabla_facturas.column(col, anchor="center", width=100)
        self.tabla_facturas.pack(fill="both", expand=True, padx=10, pady=5)

        self.cargar_facturas()

    def registrar_ingreso(self):
        descripcion = self.descripcion_ingreso.get()
        monto = self.monto_ingreso.get()
        if descripcion and monto:
            Finanzas.registrar_ingreso(descripcion, float(monto))
            self.descripcion_ingreso.delete(0, END)
            self.monto_ingreso.delete(0, END)
            self.resultado.insert(END, f"✅ Ingreso registrado: {descripcion} - ${monto}\n")

    def registrar_gasto(self):
        descripcion = self.descripcion_gasto.get()
        monto = self.monto_gasto.get()
        if descripcion and monto:
            Finanzas.registrar_gasto(descripcion, float(monto))
            self.descripcion_gasto.delete(0, END)
            self.monto_gasto.delete(0, END)
            self.resultado.insert(END, f"✅ Gasto registrado: {descripcion} - ${monto}\n")

    def mostrar_estado(self):
        ingresos = Finanzas.listar_ingresos()
        gastos = Finanzas.listar_gastos()
        total_ingresos, total_gastos, utilidad = Finanzas.estado_resultado()

        self.resultado.delete("1.0", END)
        self.resultado.insert(END, "📋 Ingresos:\n")
        for i in ingresos:
            self.resultado.insert(END, f"- {i[1]}: ${i[2]}\n")

        self.resultado.insert(END, "\n💸 Gastos:\n")
        for g in gastos:
            self.resultado.insert(END, f"- {g[1]}: ${g[2]}\n")

        self.resultado.insert(END, f"\n📊 Estado de Resultados:\n")
        self.resultado.insert(END, f"🟢 Total Ingresos: ${total_ingresos}\n")
        self.resultado.insert(END, f"🔴 Total Gastos (incl. facturas): ${total_gastos}\n")
        self.resultado.insert(END, f"💰 Utilidad Neta: ${utilidad}\n")

    def mostrar_grafico(self):
        ingresos, gastos, utilidad = Finanzas.estado_resultado()
        etiquetas = ["Ingresos", "Gastos", "Utilidad"]
        valores = [ingresos, gastos, utilidad]

        plt.figure(figsize=(6, 4))
        plt.bar(etiquetas, valores, color=["green", "red", "blue"])
        plt.title("Estado Financiero")
        plt.ylabel("Monto CLP")
        plt.grid(axis='y')
        plt.tight_layout()
        plt.show()

    def exportar_estado(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not ruta:
            return
        ingresos = Finanzas.listar_ingresos()
        gastos = Finanzas.listar_gastos()
        facturas = Finanzas.listar_facturas()
        with open(ruta, mode='w', newline='') as archivo:
            writer = csv.writer(archivo)
            writer.writerow(["Tipo", "Descripción", "Monto"])
            for i in ingresos:
                writer.writerow(["Ingreso", i[1], i[2]])
            for g in gastos:
                writer.writerow(["Gasto", g[1], g[2]])
            for f in facturas:
                tipo = "Factura Cliente" if f[6] == "cliente" else "Factura Proveedor"
                writer.writerow([tipo, f[2], f[3]])
        messagebox.showinfo("Exportación completa", "📁 Estado exportado exitosamente")

    def cargar_facturas(self):
        for row in self.tabla_facturas.get_children():
            self.tabla_facturas.delete(row)
        try:
            facturas = Finanzas.listar_facturas()
            estado = self.estado_filtro.get()
            tipo = self.tipo_filtro.get()
            if estado != "todos":
                facturas = [f for f in facturas if f[4] == estado]
            if tipo != "todos":
                facturas = [f for f in facturas if f[6] == tipo]
            for f in facturas:
                self.tabla_facturas.insert("", "end", values=f)
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar facturas: {str(e)}")

    def abrir_formulario_factura(self):
        ventana = Toplevel(self)
        ventana.title("Agregar Factura")

        Label(ventana, text="Número: ").grid(row=0, column=0)
        numero = Entry(ventana)
        numero.grid(row=0, column=1)

        Label(ventana, text="Proveedor/Cliente: ").grid(row=1, column=0)
        proveedor = Entry(ventana)
        proveedor.grid(row=1, column=1)

        Label(ventana, text="Monto: ").grid(row=2, column=0)
        monto = Entry(ventana)
        monto.grid(row=2, column=1)

        Label(ventana, text="Estado: ").grid(row=3, column=0)
        estado = ttk.Combobox(ventana, values=["pendiente", "pagada", "vencida"])
        estado.set("pendiente")
        estado.grid(row=3, column=1)

        Label(ventana, text="Fecha (YYYY-MM-DD):").grid(row=4, column=0)
        fecha = Entry(ventana)
        fecha.insert(0, str(date.today()))
        fecha.grid(row=4, column=1)

        Label(ventana, text="Tipo de factura:").grid(row=5, column=0)
        tipo = ttk.Combobox(ventana, values=["proveedor", "cliente"])
        tipo.set("proveedor")
        tipo.grid(row=5, column=1)

        def guardar():
            try:
                Finanzas.registrar_factura(
                    numero.get(), proveedor.get(), float(monto.get()), estado.get(), fecha.get(), tipo.get()
                )
                ventana.destroy()
                self.cargar_facturas()
                self.mostrar_estado()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la factura: {e}")

        Button(ventana, text="Guardar", command=guardar).grid(row=6, column=1, pady=10)

    def actualizar_estado_factura(self):
        seleccionado = self.tabla_facturas.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona una factura")
            return
        id_factura = self.tabla_facturas.item(seleccionado)['values'][0]

        ventana = Toplevel(self)
        ventana.title("Cambiar Estado")

        Label(ventana, text="Nuevo estado: ").grid(row=0, column=0)
        nuevo_estado = ttk.Combobox(ventana, values=["pendiente", "pagada", "vencida"])
        nuevo_estado.grid(row=0, column=1)

        def aplicar():
            Finanzas.cambiar_estado_factura(id_factura, nuevo_estado.get())
            ventana.destroy()
            self.cargar_facturas()
            self.mostrar_estado()

        Button(ventana, text="Aplicar", command=aplicar).grid(row=1, column=1, pady=10)
