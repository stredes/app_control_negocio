# control_negocio/app/ui/productos_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.producto import Producto

class ProductosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Gestión de Productos", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        # Campos
        etiquetas = ["Nombre", "Categoría", "Precio Compra", "Precio Venta", "Stock"]
        self.entradas = {}

        for i, texto in enumerate(etiquetas):
            tk.Label(formulario, text=texto + ":", bg="white").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            entrada = ttk.Entry(formulario, width=30)
            entrada.grid(row=i, column=1, pady=5, padx=5)
            self.entradas[texto.lower().replace(" ", "_")] = entrada

        # Botones
        botones = tk.Frame(self, bg="white")
        botones.pack(pady=15)

        acciones = [
            ("Guardar", self.guardar_producto),
            ("Buscar", self.buscar_producto),
            ("Eliminar", self.eliminar_producto),
            ("Recargar", self.cargar_tabla)
        ]

        for texto, comando in acciones:
            ttk.Button(botones, text=texto, command=comando, width=12).pack(side="left", padx=10)

        # Tabla
        self.tabla = ttk.Treeview(self, columns=("id", "nombre", "categoria", "compra", "venta", "stock"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col.capitalize())
            self.tabla.column(col, width=120)
        self.tabla.pack(pady=10, fill="x")

    def limpiar_entradas(self):
        for entrada in self.entradas.values():
            entrada.delete(0, tk.END)

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        productos = datos if datos else Producto.listar_todos()
        for prod in productos:
            self.tabla.insert("", tk.END, values=prod)

    def guardar_producto(self):
        try:
            datos = {k: v.get() for k, v in self.entradas.items()}
            Producto.crear(
                datos["nombre"],
                datos["categoría"],
                float(datos["precio_compra"]),
                float(datos["precio_venta"]),
                int(datos["stock"])
            )
            self.cargar_tabla()
            self.limpiar_entradas()
            messagebox.showinfo("Éxito", "Producto guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def buscar_producto(self):
        nombre = self.entradas["nombre"].get()
        resultados = Producto.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def eliminar_producto(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un producto para eliminar.")
            return
        item = self.tabla.item(seleccionado[0])
        producto_id = item["values"][0]
        Producto.eliminar(producto_id)
        self.cargar_tabla()
        messagebox.showinfo("Eliminado", "Producto eliminado.")
