# control_negocio/app/ui/ingreso_inventario_view.py

import tkinter as tk
from tkinter import ttk, messagebox

from app.models.producto import Producto
from app.models.ingreso_inventario import IngresoInventario


class IngresoInventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self._map_codigo_to_codigo = {}  # texto mostrado -> codigo_interno real
        self.crear_widgets()
        self.cargar_combobox_producto()
        self.cargar_tabla()

    # ---------------- UI ----------------
    def crear_widgets(self):
        tk.Label(
            self,
            text="📥 Ingreso de Productos al Inventario",
            font=("Arial", 16, "bold"),
            bg="white",
        ).pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10, padx=10, fill="x")

        # Código Interno (combobox)
        tk.Label(form, text="Código Interno:", bg="white")\
            .grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cmb_codigo = ttk.Combobox(form, width=40, state="readonly")
        self.cmb_codigo.grid(row=0, column=1, padx=5, pady=5)

        # Cantidad
        tk.Label(form, text="Cantidad:", bg="white")\
            .grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(form, width=20)
        self.entry_cantidad.insert(0, "1")
        self.entry_cantidad.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Ubicación
        tk.Label(form, text="Ubicación:", bg="white")\
            .grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_ubicacion = ttk.Entry(form, width=30)
        self.entry_ubicacion.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Método
        tk.Label(form, text="Método:", bg="white")\
            .grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_metodo = ttk.Entry(form, width=20)
        self.entry_metodo.insert(0, "manual")
        self.entry_metodo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Registrar Ingreso", command=self.registrar, width=16)\
            .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recargar", command=self._refrescar, width=10)\
            .pack(side="left", padx=5)

        # Tabla de movimientos (solo entradas)
        cols = ("id", "codigo_producto", "tipo", "cantidad", "ubicacion", "metodo", "fecha")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c.replace("_", " ").capitalize())
            self.tabla.column(c, width=120 if c in ("codigo_producto", "ubicacion") else 100, anchor="center")
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    # ------------- Datos -------------
    def cargar_combobox_producto(self):
        """
        Carga en el Combobox todos los códigos internos con su nombre:
        'COD123 — Nombre del producto'
        """
        try:
            productos = Producto.listar_todos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar productos.\n{e}")
            return

        # Estructura de productos según tu tabla:
        # (id, nombre, categoria, precio_compra, precio_venta, stock, codigo_interno, codigo_externo, iva, ubicacion, fecha_vencimiento)
        # índice 6 -> codigo_interno, índice 1 -> nombre
        opciones = []
        self._map_codigo_to_codigo.clear()
        for p in productos:
            codigo = p[6]
            nombre = p[1]
            if not codigo:
                continue
            etiqueta = f"{codigo} — {nombre}"
            self._map_codigo_to_codigo[etiqueta] = codigo
            opciones.append(etiqueta)

        self.cmb_codigo["values"] = opciones
        if opciones:
            self.cmb_codigo.current(0)

    def cargar_tabla(self):
        """Refresca la tabla con todas las entradas de inventario."""
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        try:
            for mov in IngresoInventario.listar_entradas():
                self.tabla.insert("", tk.END, values=mov)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar movimientos.\n{e}")

    # ------------- Acciones -------------
    def registrar(self):
        """
        Valida y registra el ingreso, actualizando stock y dejando traza.
        """
        try:
            etiqueta = self.cmb_codigo.get().strip()
            if not etiqueta:
                raise ValueError("Debes seleccionar un código interno de producto.")
            codigo = self._map_codigo_to_codigo.get(etiqueta, etiqueta)

            try:
                cantidad = int((self.entry_cantidad.get() or "0").strip())
            except ValueError:
                raise ValueError("La cantidad debe ser un número entero.")

            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a 0.")

            ubic = (self.entry_ubicacion.get() or "").strip()
            if not ubic:
                raise ValueError("Debes especificar la ubicación.")

            metodo = (self.entry_metodo.get() or "manual").strip()

            # Registrar (actualiza stock y crea movimiento)
            IngresoInventario.registrar(codigo, cantidad, ubic, metodo)

            messagebox.showinfo("✅ Éxito", "Ingreso registrado; stock actualizado.")
            self._limpiar_form()
            self._refrescar()

        except Exception as e:
            messagebox.showerror("❌ Error", f"{e}")

    # ------------- Util -------------
    def _limpiar_form(self):
        self.cmb_codigo.set("")
        self.entry_cantidad.delete(0, tk.END)
        self.entry_cantidad.insert(0, "1")
        self.entry_ubicacion.delete(0, tk.END)
        self.entry_metodo.delete(0, tk.END)
        self.entry_metodo.insert(0, "manual")

    def _refrescar(self):
        self.cargar_combobox_producto()
        self.cargar_tabla()
