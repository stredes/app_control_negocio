# control_negocio/app/ui/ingreso_inventario_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.producto import Producto
from app.models.ingreso_inventario import IngresoInventario

class IngresoInventarioView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.crear_widgets()
        self.cargar_combobox_producto()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(
            self, text="📥 Ingreso de Productos al Inventario",
            font=("Arial", 16, "bold"), bg="white"
        ).pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10, padx=10)

        # Código Interno
        tk.Label(form, text="Código Interno:", bg="white")\
            .grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cmb_codigo = ttk.Combobox(form, width=30, state="readonly")
        self.cmb_codigo.grid(row=0, column=1, padx=5, pady=5)

        # Cantidad
        tk.Label(form, text="Cantidad:", bg="white")\
            .grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(form, width=30)
        self.entry_cantidad.grid(row=1, column=1, padx=5, pady=5)

        # Ubicación
        tk.Label(form, text="Ubicación:", bg="white")\
            .grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_ubicacion = ttk.Entry(form, width=30)
        self.entry_ubicacion.grid(row=2, column=1, padx=5, pady=5)

        # Método
        tk.Label(form, text="Método:", bg="white")\
            .grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_metodo = ttk.Entry(form, width=30)
        self.entry_metodo.insert(0, "manual")
        self.entry_metodo.grid(row=3, column=1, padx=5, pady=5)

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)
        ttk.Button(
            btn_frame, text="Registrar Ingreso",
            command=self.registrar, width=16
        ).pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Recargar",
            command=self.cargar_tabla, width=10
        ).pack(side="left", padx=5)

        # Tabla de movimientos
        cols = ("id", "codigo_producto", "tipo", "cantidad",
                "ubicacion", "metodo", "fecha")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c.replace("_", " ").capitalize())
            self.tabla.column(c, width=100, anchor="center")
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def cargar_combobox_producto(self):
        """
        Carga en el Combobox todos los códigos internos de productos.
        """
        productos = Producto.listar_todos()  # [(id, nombre, categoria, ..., codigo_interno, ...), ...]
        codigos = [p[6] for p in productos]   # índice 6 → codigo_interno
        self.cmb_codigo["values"] = codigos

    def registrar(self):
        """
        Llama al modelo para registrar y actualizar stock.
        """
        try:
            codigo   = self.cmb_codigo.get().strip()
            cantidad = int(self.entry_cantidad.get().strip())
            ubic     = self.entry_ubicacion.get().strip()
            metodo   = self.entry_metodo.get().strip()

            if not codigo or not ubic:
                raise ValueError("Selecciona un código y especifica ubicación.")

            # Ahora llamamos al método que sí existe en tu modelo
            IngresoInventario.registrar(codigo, cantidad, ubic, metodo)

            messagebox.showinfo("✅ Éxito", "Ingreso registrado; stock actualizado.")
            # Limpiar formulario
            self.cmb_codigo.set("")
            self.entry_cantidad.delete(0, tk.END)
            self.entry_ubicacion.delete(0, tk.END)
            self.entry_metodo.delete(0, tk.END)
            self.entry_metodo.insert(0, "manual")
            # Refrescar
            self.cargar_combobox_producto()
            self.cargar_tabla()

        except Exception as e:
            messagebox.showerror("❌ Error", f"{e}")

    def cargar_tabla(self):
        """
        Refresca la tabla con todas las entradas manuales.
        """
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        # Usa listar_entradas() para filtrar sólo las de tipo entrada
        for mov in IngresoInventario.listar_entradas():
            self.tabla.insert("", tk.END, values=mov)
