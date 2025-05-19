# control_negocio/app/ui/inventario_view.py

import tkinter as tk
from tkinter import ttk
from app.models.producto import Producto

class InventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Consulta de Inventario (Kardex)", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        filtro_frame = tk.Frame(self, bg="white")
        filtro_frame.pack(pady=10)

        tk.Label(filtro_frame, text="Buscar producto:", bg="white").pack(side="left", padx=5)
        self.entrada_busqueda = ttk.Entry(filtro_frame, width=30)
        self.entrada_busqueda.pack(side="left", padx=5)

        ttk.Button(filtro_frame, text="Buscar", command=self.buscar_producto).pack(side="left", padx=5)
        ttk.Button(filtro_frame, text="Mostrar todo", command=self.cargar_tabla).pack(side="left", padx=5)

        self.tabla = ttk.Treeview(self, columns=("id", "nombre", "categoria", "precio_compra", "precio_venta", "stock"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=120)
        self.tabla.pack(pady=10, fill="both", expand=True)

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        productos = datos if datos else Producto.listar_todos()
        for prod in productos:
            self.tabla.insert("", tk.END, values=prod)

    def buscar_producto(self):
        nombre = self.entrada_busqueda.get()
        if nombre:
            resultados = Producto.buscar_por_nombre(nombre)
            self.cargar_tabla(resultados)
        else:
            self.cargar_tabla()
