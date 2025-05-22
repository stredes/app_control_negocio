import tkinter as tk
from tkinter import ttk, messagebox
from app.models.producto import Producto
import unicodedata

class ProductosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.producto_seleccionado_id = None
        self.crear_widgets()
        self.cargar_tabla()

    def limpiar_clave(self, texto):
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto.lower())
            if c.isalnum() or c == '_'
        ).replace(" ", "_")

    def crear_widgets(self):
        tk.Label(self, text="🛠 Creación de Productos", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        campos = [
            "Nombre", "Categoría", "Precio Compra", "Precio Venta", "Stock",
            "Código Interno", "Código Externo", "IVA", "Ubicación", "Fecha Vencimiento"
        ]
        self.entradas = {}

        for i, campo in enumerate(campos):
            tk.Label(formulario, text=campo + ":", bg="white").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            entrada = ttk.Entry(formulario, width=30)
            entrada.grid(row=i, column=1, pady=5, padx=5)
            clave = self.limpiar_clave(campo)
            self.entradas[clave] = entrada

        botones = tk.Frame(self, bg="white")
        botones.pack(pady=15)

        acciones = [
            ("Guardar", self.guardar_producto),
            ("Editar", self.editar_producto),
            ("Buscar", self.buscar_producto),
            ("Eliminar", self.eliminar_producto),
            ("Recargar", self.cargar_tabla)
        ]

        for texto, comando in acciones:
            ttk.Button(botones, text=texto, command=comando, width=12).pack(side="left", padx=5)

        self.tabla = ttk.Treeview(
            self,
            columns=(
                "id", "nombre", "categoria", "precio_compra", "precio_venta",
                "stock", "codigo_interno", "codigo_externo", "iva", "ubicacion", "fecha_vencimiento"
            ),
            show="headings"
        )
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=110)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_producto)
        self.tabla.pack(pady=10, fill="x")

    def limpiar_entradas(self):
        for entrada in self.entradas.values():
            entrada.delete(0, tk.END)
        self.producto_seleccionado_id = None

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
                datos["categoria"],
                float(datos["precio_compra"]),
                float(datos["precio_venta"]),
                int(datos["stock"]),
                datos["codigo_interno"],
                datos["codigo_externo"],
                float(datos["iva"]),
                datos["ubicacion"],
                datos["fecha_vencimiento"]
            )
            self.cargar_tabla()
            self.limpiar_entradas()
            messagebox.showinfo("✅ Éxito", "Producto guardado correctamente.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo guardar: {e}")

    def buscar_producto(self):
        nombre = self.entradas["nombre"].get()
        resultados = Producto.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def eliminar_producto(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("⚠️ Atención", "Selecciona un producto para eliminar.")
            return
        item = self.tabla.item(seleccionado[0])
        producto_id = item["values"][0]
        Producto.eliminar(producto_id)
        self.cargar_tabla()
        self.limpiar_entradas()
        messagebox.showinfo("🗑️ Eliminado", "Producto eliminado.")

    def seleccionar_producto(self, event):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            return
        item = self.tabla.item(seleccionado[0])
        valores = item["values"]
        self.producto_seleccionado_id = valores[0]
        keys = list(self.entradas.keys())
        for i, k in enumerate(keys):
            self.entradas[k].delete(0, tk.END)
            self.entradas[k].insert(0, valores[i + 1])  # +1 porque el primer valor es ID

    def editar_producto(self):
        if not self.producto_seleccionado_id:
            messagebox.showwarning("⚠️ Atención", "Debes seleccionar un producto para editar.")
            return

        try:
            datos = {k: v.get() for k, v in self.entradas.items()}
            conn = Producto.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE productos SET
                    nombre = ?, categoria = ?, precio_compra = ?, precio_venta = ?, stock = ?,
                    codigo_interno = ?, codigo_externo = ?, iva = ?, ubicacion = ?, fecha_vencimiento = ?
                WHERE id = ?
            """, (
                datos["nombre"], datos["categoria"], float(datos["precio_compra"]),
                float(datos["precio_venta"]), int(datos["stock"]),
                datos["codigo_interno"], datos["codigo_externo"], float(datos["iva"]),
                datos["ubicacion"], datos["fecha_vencimiento"], self.producto_seleccionado_id
            ))
            conn.commit()
            conn.close()
            self.cargar_tabla()
            self.limpiar_entradas()
            messagebox.showinfo("✏️ Editado", "Producto actualizado exitosamente.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo editar: {e}")
