# control_negocio/app/ui/inventario_view.py

import tkinter as tk
from tkinter import ttk, messagebox

from app.models.inventario import Inventario


class InventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self._build_ui()
        self.cargar_tabla()

    # ---------------- UI ----------------
    def _build_ui(self):
        # Título
        tk.Label(
            self, text="📦 Inventario",
            font=("Arial", 16, "bold"), bg="white"
        ).pack(pady=10)

        # Panel de filtros
        filtro = tk.Frame(self, bg="white")
        filtro.pack(pady=5, padx=10, fill="x")

        # Nombre
        tk.Label(filtro, text="Nombre:", bg="white")\
            .grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.entry_nombre = ttk.Entry(filtro, width=24)
        self.entry_nombre.grid(row=0, column=1, padx=5, pady=3)
        self.entry_nombre.bind("<Return>", lambda e: self.buscar_por_nombre())

        # Código Interno
        tk.Label(filtro, text="Código Interno:", bg="white")\
            .grid(row=0, column=2, sticky="e", padx=5, pady=3)
        self.entry_codigo = ttk.Entry(filtro, width=24)
        self.entry_codigo.grid(row=0, column=3, padx=5, pady=3)
        self.entry_codigo.bind("<Return>", lambda e: self.buscar_por_codigo())

        # Categoría
        tk.Label(filtro, text="Categoría:", bg="white")\
            .grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.entry_categoria = ttk.Entry(filtro, width=24)
        self.entry_categoria.grid(row=1, column=1, padx=5, pady=3)
        self.entry_categoria.bind("<Return>", lambda e: self.buscar_por_categoria())

        # Fecha Vencimiento
        tk.Label(filtro, text="Vence antes de (YYYY-MM-DD):", bg="white")\
            .grid(row=1, column=2, sticky="e", padx=5, pady=3)
        self.entry_vencimiento = ttk.Entry(filtro, width=24)
        self.entry_vencimiento.grid(row=1, column=3, padx=5, pady=3)
        self.entry_vencimiento.bind("<Return>", lambda e: self.buscar_por_vencimiento())

        # Botones de búsqueda
        btns = tk.Frame(self, bg="white")
        btns.pack(pady=8)
        ttk.Button(btns, text="Por Nombre",       command=self.buscar_por_nombre, width=14)\
            .pack(side="left", padx=5)
        ttk.Button(btns, text="Por Código",       command=self.buscar_por_codigo, width=14)\
            .pack(side="left", padx=5)
        ttk.Button(btns, text="Por Categoría",    command=self.buscar_por_categoria, width=14)\
            .pack(side="left", padx=5)
        ttk.Button(btns, text="Por Vencimiento",  command=self.buscar_por_vencimiento, width=14)\
            .pack(side="left", padx=5)
        ttk.Button(btns, text="Recargar Todo",    command=self.cargar_tabla, width=14)\
            .pack(side="left", padx=5)
        ttk.Button(btns, text="Limpiar filtros",  command=self._limpiar_filtros, width=14)\
            .pack(side="left", padx=5)

        # Tabla de inventario
        cols = (
            "id", "nombre", "categoria", "codigo_interno",
            "precio_compra", "precio_venta", "stock",
            "iva", "ubicacion", "fecha_vencimiento"
        )
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        self.tabla.pack(fill="both", expand=True, pady=10, padx=10)

        headers = {
            "id": "ID",
            "nombre": "Nombre",
            "categoria": "Categoría",
            "codigo_interno": "Código Interno",
            "precio_compra": "Precio Compra",
            "precio_venta": "Precio Venta",
            "stock": "Stock",
            "iva": "IVA (%)",
            "ubicacion": "Ubicación",
            "fecha_vencimiento": "Fecha Venc."
        }
        widths = {
            "id": 60, "nombre": 160, "categoria": 120, "codigo_interno": 130,
            "precio_compra": 110, "precio_venta": 110, "stock": 80,
            "iva": 80, "ubicacion": 120, "fecha_vencimiento": 110
        }
        for c in cols:
            self.tabla.heading(c, text=headers.get(c, c).strip())
            self.tabla.column(c, width=widths.get(c, 100), anchor="center")

        # Scrollbars
        ysb = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        ysb.place(in_=self.tabla, relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.tabla.configure(yscrollcommand=ysb.set)

    # ------------- Carga Tabla -------------
    def cargar_tabla(self, datos=None):
        self._limpiar_tabla()
        try:
            rows = datos if datos is not None else Inventario.listar_todo()
            for r in rows:
                # r = (id, nombre, categoria, codigo_interno, precio_compra, precio_venta,
                #      stock, iva, ubicacion, fecha_vencimiento)
                self.tabla.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el inventario.\n{e}")

    def _limpiar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

    def _limpiar_filtros(self):
        self.entry_nombre.delete(0, tk.END)
        self.entry_codigo.delete(0, tk.END)
        self.entry_categoria.delete(0, tk.END)
        self.entry_vencimiento.delete(0, tk.END)
        self.cargar_tabla()

    # ------------- Búsquedas -------------
    def buscar_por_nombre(self):
        texto = self.entry_nombre.get().strip()
        if not texto:
            return messagebox.showwarning("Atención", "Ingresa un nombre para buscar.")
        try:
            datos = Inventario.buscar_por_nombre(texto)
            self.cargar_tabla(datos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar por nombre.\n{e}")

    def buscar_por_codigo(self):
        texto = self.entry_codigo.get().strip()
        if not texto:
            return messagebox.showwarning("Atención", "Ingresa un código interno para buscar.")
        try:
            datos = Inventario.buscar_por_codigo_interno(texto)
            self.cargar_tabla(datos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar por código.\n{e}")

    def buscar_por_categoria(self):
        texto = self.entry_categoria.get().strip()
        if not texto:
            return messagebox.showwarning("Atención", "Ingresa una categoría para buscar.")
        try:
            datos = Inventario.buscar_por_categoria(texto)
            self.cargar_tabla(datos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar por categoría.\n{e}")

    def buscar_por_vencimiento(self):
        fecha = self.entry_vencimiento.get().strip()
        if not fecha:
            return messagebox.showwarning("Atención", "Ingresa una fecha (YYYY-MM-DD).")
        # No validamos formato aquí para permitir búsquedas flexibles; SQLite comparará textualmente YYYY-MM-DD.
        try:
            datos = Inventario.buscar_por_vencimiento(fecha)
            self.cargar_tabla(datos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar por vencimiento.\n{e}")
