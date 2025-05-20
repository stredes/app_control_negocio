# control_negocio/app/ui/compras_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.compra import Compra
from app.models.producto import Producto
from app.models.proveedor import Proveedor

class ComprasView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Órdenes de Compra", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        self.cmb_proveedor = ttk.Combobox(formulario, width=32, state="readonly")
        self.cmb_producto = ttk.Combobox(formulario, width=32, state="readonly")

        campos = {
            "Proveedor:": self.cmb_proveedor,
            "Producto:": self.cmb_producto,
            "Cantidad:": ttk.Entry(formulario, width=30),
            "Precio Unitario:": ttk.Entry(formulario, width=30),
            "IVA (%):": ttk.Entry(formulario, width=30)
        }

        self.campos = {}
        for i, (lbl, widget) in enumerate(campos.items()):
            tk.Label(formulario, text=lbl, bg="white").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            widget.grid(row=i, column=1, pady=5, padx=5)
            self.campos[lbl.strip(":").lower().replace(" ", "_")] = widget

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Registrar Compra", command=self.registrar_compra).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Última Compra", command=self.mostrar_ultima_compra).pack(side="left", padx=5)

        # Tabla
        cols = ("id", "proveedor", "producto", "cantidad", "precio_unitario", "iva", "total")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=120)
        self.tabla.pack(pady=10, fill="x")

        self.cargar_combobox()

    def cargar_combobox(self):
        self.cmb_proveedor["values"] = [p[1] for p in Proveedor.listar_todos()]
        self.cmb_producto["values"] = [p[1] for p in Producto.listar_todos()]

    def registrar_compra(self):
        try:
            proveedor = self.campos["proveedor"].get()
            producto = self.campos["producto"].get()
            cantidad = int(self.campos["cantidad"].get())
            precio_unitario = float(self.campos["precio_unitario"].get())
            iva = float(self.campos["iva"].get())

            Compra.registrar(proveedor, producto, cantidad, precio_unitario, iva)
            messagebox.showinfo("Éxito", "Compra registrada y stock actualizado.")
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar: {e}")

    def mostrar_ultima_compra(self):
        producto = self.campos["producto"].get()
        if not producto:
            messagebox.showwarning("Atención", "Selecciona un producto.")
            return
        compra = Compra.ultima_compra_producto(producto)
        if compra:
            info = f"📦 Última compra:\nProveedor: {compra[1]}\nCantidad: {compra[3]}\nPrecio: {compra[4]}\nIVA: {compra[5]}%\nTotal: {compra[6]}"
            messagebox.showinfo("Última compra", info)
        else:
            messagebox.showinfo("Sin datos", "No hay compras previas para este producto.")

    def cargar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for c in Compra.listar_todas():
            self.tabla.insert("", tk.END, values=c)
