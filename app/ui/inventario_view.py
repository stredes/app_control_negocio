import tkinter as tk
from tkinter import ttk, messagebox
from app.models.inventario import Inventario

class InventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        # Título
        tk.Label(self, text="Inventario", font=("Arial", 16, "bold"), bg="white")\
            .pack(pady=10)

        # Panel de filtros
        filtro_frame = tk.Frame(self, bg="white")
        filtro_frame.pack(pady=5, padx=10, fill="x")

        # Nombre
        tk.Label(filtro_frame, text="Nombre:", bg="white")\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_nombre = ttk.Entry(filtro_frame, width=20)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=3)

        # Código Interno
        tk.Label(filtro_frame, text="Código Interno:", bg="white")\
            .grid(row=0, column=2, sticky="e", padx=5, pady=3)
        self.entry_codigo = ttk.Entry(filtro_frame, width=20)
        self.entry_codigo.grid(row=0, column=3, padx=5, pady=3)

        # Categoría
        tk.Label(filtro_frame, text="Categoría:", bg="white")\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_categoria = ttk.Entry(filtro_frame, width=20)
        self.entry_categoria.grid(row=1, column=1, padx=5, pady=3)

        # Fecha Vencimiento
        tk.Label(filtro_frame, text="Vence antes de:", bg="white")\
            .grid(row=1, column=2, sticky="e", padx=5, pady=3)
        self.entry_vencimiento = ttk.Entry(filtro_frame, width=20)
        self.entry_vencimiento.grid(row=1, column=3, padx=5, pady=3)

        # Botones de búsqueda
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Por Nombre", command=self.buscar_por_nombre, width=12)\
            .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Por Código", command=self.buscar_por_codigo, width=12)\
            .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Por Categoría", command=self.buscar_por_categoria, width=12)\
            .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Por Vencimiento", command=self.buscar_por_vencimiento, width=12)\
            .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recargar Todo", command=self.cargar_tabla, width=12)\
            .pack(side="left", padx=5)

        # Tabla de inventario
        cols = (
            "id", "nombre", "categoria", "codigo_interno",
            "precio_compra", "precio_venta", "stock",
            "iva", "ubicacion", "fecha_vencimiento"
        )
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=100, anchor="center")

        self.tabla.pack(fill="both", expand=True, pady=10, padx=10)

    def cargar_tabla(self, datos=None):
        # Limpia y carga datos en la tabla
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        rows = datos if datos is not None else Inventario.listar_todo()
        for r in rows:
            self.tabla.insert("", tk.END, values=r)

    def buscar_por_nombre(self):
        texto = self.entry_nombre.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Ingresa un nombre para buscar.")
            return
        datos = Inventario.buscar_por_nombre(texto)
        self.cargar_tabla(datos)

    def buscar_por_codigo(self):
        texto = self.entry_codigo.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Ingresa un código interno para buscar.")
            return
        datos = Inventario.buscar_por_codigo_interno(texto)
        self.cargar_tabla(datos)

    def buscar_por_categoria(self):
        texto = self.entry_categoria.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Ingresa una categoría para buscar.")
            return
        datos = Inventario.buscar_por_categoria(texto)
        self.cargar_tabla(datos)

    def buscar_por_vencimiento(self):
        fecha = self.entry_vencimiento.get().strip()
        if not fecha:
            messagebox.showwarning("Atención", "Ingresa una fecha (YYYY-MM-DD).")
            return
        datos = Inventario.buscar_por_vencimiento(fecha)
        self.cargar_tabla(datos)
