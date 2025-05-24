import tkinter as tk
from tkinter import ttk, messagebox
from app.models.venta import Venta
from app.models.cliente import Cliente
from app.models.producto import Producto

class VentasView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_comboboxes()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Órdenes de Venta", font=("Arial", 16, "bold"), bg="white")
        tk.Label(self, text="Órdenes de Venta", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # Cliente
        tk.Label(form, text="Cliente:", bg="white").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cliente_cb = ttk.Combobox(form, width=30, state="readonly")
        self.cliente_cb.grid(row=0, column=1, padx=5, pady=5)

        # Producto
        tk.Label(form, text="Producto:", bg="white").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.producto_cb = ttk.Combobox(form, width=30, state="readonly")
        self.producto_cb.grid(row=1, column=1, padx=5, pady=5)
        self.producto_cb.bind("<<ComboboxSelected>>", self.mostrar_ultima_venta)

        # Cantidad
        tk.Label(form, text="Cantidad:", bg="white").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(form, width=30)
        self.entry_cantidad.grid(row=2, column=1, padx=5, pady=5)

        # Precio Unitario
        tk.Label(form, text="Precio Unitario:", bg="white").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_precio_unitario = ttk.Entry(form, width=30)
        self.entry_precio_unitario.grid(row=3, column=1, padx=5, pady=5)

        # IVA (%)
        tk.Label(form, text="IVA (%):", bg="white").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_iva = ttk.Entry(form, width=30)
        self.entry_iva.insert(0, "19")
        self.entry_iva.grid(row=4, column=1, padx=5, pady=5)

        # Información de última venta
        self.info_venta = tk.Label(self, text="", bg="white", fg="gray")
        self.info_venta.pack()

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Registrar Venta", command=self.registrar_venta, width=16).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recargar", command=self.cargar_tabla, width=10).pack(side="left", padx=5)

        # Tabla de ventas
        cols = ("id", "cliente", "producto", "cantidad",
                "precio_unitario", "iva", "total", "fecha")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=100, anchor="center")
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def cargar_comboboxes(self):
        # Poblar comboboxes con datos actuales
        clientes = [c[1] for c in Cliente.listar_todos()]
        productos = [p[1] for p in Producto.listar_todos()]
        self.cliente_cb['values'] = clientes
        self.producto_cb['values'] = productos

    def mostrar_ultima_venta(self, event=None):
        producto = self.producto_cb.get()
        if not producto:
            self.info_venta.config(text="")
            return
        venta = Venta.ultima_venta_producto(producto)
        if venta:
            # venta = (id, cliente, producto, cantidad, precio_unitario, iva, total, fecha)
            fecha = venta[7]
            total = venta[6]
            self.info_venta.config(
                text=f"🕒 Última venta de {producto}: {fecha} (Total: ${total})"
            )
        else:
            self.info_venta.config(text="Sin ventas anteriores registradas.")

    def registrar_venta(self):
        try:
            cliente = self.cliente_cb.get()
            producto = self.producto_cb.get()
            cantidad = int(self.entry_cantidad.get())
            precio = float(self.entry_precio_unitario.get())
            iva = float(self.entry_iva.get())
            if not cliente or not producto:
                raise ValueError("Debe seleccionar cliente y producto.")

            Venta.registrar(cliente, producto, cantidad, precio, iva)
            messagebox.showinfo("✅ Éxito", "Venta registrada correctamente.")

            # Limpiar campos
            self.cliente_cb.set("")
            self.producto_cb.set("")
            self.entry_cantidad.delete(0, tk.END)
            self.entry_precio_unitario.delete(0, tk.END)
            self.entry_iva.delete(0, tk.END)
            self.entry_iva.insert(0, "19")
            self.info_venta.config(text="")

            # Refrescar datos
            self.cargar_comboboxes()
            self.cargar_tabla()

        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo registrar la venta:\n{e}")

    def cargar_tabla(self):
        # Refrescar tabla con todas las ventas
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for v in Venta.listar_todas():
            self.tabla.insert("", tk.END, values=v)
