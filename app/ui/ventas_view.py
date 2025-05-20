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
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Órdenes de Venta", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # Campos y entradas
        tk.Label(form, text="Cliente:", bg="white").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cliente_cb = ttk.Combobox(form, values=self.obtener_clientes(), width=30)
        self.cliente_cb.grid(row=0, column=1, padx=5)

        tk.Label(form, text="Producto:", bg="white").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.producto_cb = ttk.Combobox(form, values=self.obtener_productos(), width=30)
        self.producto_cb.grid(row=1, column=1, padx=5)
        self.producto_cb.bind("<<ComboboxSelected>>", self.mostrar_ultima_venta)

        tk.Label(form, text="Cantidad:", bg="white").grid(row=2, column=0, sticky="e", padx=5)
        self.cantidad = ttk.Entry(form, width=20)
        self.cantidad.grid(row=2, column=1, padx=5)

        tk.Label(form, text="Precio Unitario:", bg="white").grid(row=3, column=0, sticky="e", padx=5)
        self.precio_unitario = ttk.Entry(form, width=20)
        self.precio_unitario.grid(row=3, column=1, padx=5)

        tk.Label(form, text="IVA (%):", bg="white").grid(row=4, column=0, sticky="e", padx=5)
        self.iva = ttk.Entry(form, width=20)
        self.iva.insert(0, "19")
        self.iva.grid(row=4, column=1, padx=5)

        # Última venta
        self.info_venta = tk.Label(self, text="", bg="white", fg="gray")
        self.info_venta.pack()

        # Botón de registro
        ttk.Button(self, text="Registrar Venta", command=self.registrar_venta, width=20).pack(pady=10)

        # Tabla
        self.tabla = ttk.Treeview(self, columns=("id", "cliente", "producto", "cantidad", "precio_unitario", "iva", "total", "fecha"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col.capitalize())
            self.tabla.column(col, width=120)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def obtener_clientes(self):
        return [c[1] for c in Cliente.listar_todos()]

    def obtener_productos(self):
        return [p[1] for p in Producto.listar_todos()]

    def mostrar_ultima_venta(self, event=None):
        producto = self.producto_cb.get()
        venta = Venta.ultima_venta(producto)
        if venta:
            self.info_venta.config(text=f"🕒 Última venta de {producto}: {venta[6]} (Total: ${venta[5]})")
        else:
            self.info_venta.config(text="Sin ventas anteriores registradas.")

    def registrar_venta(self):
        try:
            cliente = self.cliente_cb.get()
            producto = self.producto_cb.get()
            cantidad = int(self.cantidad.get())
            precio_unitario = float(self.precio_unitario.get())
            iva = float(self.iva.get())

            if not cliente or not producto:
                raise ValueError("Debe seleccionar cliente y producto.")

            Venta.registrar(cliente, producto, cantidad, precio_unitario, iva)
            self.cargar_tabla()
            self.limpiar_campos()
            messagebox.showinfo("Éxito", "Venta registrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la venta:\n{e}")

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        ventas = Venta.listar_todas()
        for v in ventas:
            self.tabla.insert("", tk.END, values=v)

    def limpiar_campos(self):
        self.cliente_cb.set("")
        self.producto_cb.set("")
        self.cantidad.delete(0, tk.END)
        self.precio_unitario.delete(0, tk.END)
        self.iva.delete(0, tk.END)
        self.iva.insert(0, "19")
        self.info_venta.config(text="")
