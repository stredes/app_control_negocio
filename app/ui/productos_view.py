import tkinter as tk
from tkinter import ttk, messagebox
import unicodedata
from app.models.producto import Producto
from app.models.categoria import Categoria

class ProductosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.producto_seleccionado_id = None
        self.crear_widgets()
        self.cargar_categorias()   # Carga categorías en el Combobox
        self.cargar_tabla()

    def limpiar_clave(self, texto):
        txt = unicodedata.normalize('NFD', texto).lower().replace(" ", "_")
        return ''.join(c for c in txt if c.isalnum() or c == "_")

    def crear_widgets(self):
        tk.Label(self, text="🛠 Creación de Productos",
                 font=("Arial", 16, "bold"), bg="white")\
          .pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        campos = [
            "Nombre", "Categoría", "Precio Compra", "Precio Venta", "Stock",
            "Código Interno", "Código Externo", "IVA", "Ubicación", "Fecha Vencimiento"
        ]
        self.entradas = {}

        for i, campo in enumerate(campos):
            clave = self.limpiar_clave(campo)
            tk.Label(formulario, text=campo + ":", bg="white")\
              .grid(row=i, column=0, sticky="e", padx=5, pady=3)

            if campo == "Categoría":
                # Combobox para categorías
                self.cmb_categoria = ttk.Combobox(
                    formulario, width=30, state="readonly")
                self.cmb_categoria.grid(row=i, column=1, padx=5, pady=3)
                self.entradas["categoria"] = self.cmb_categoria
            else:
                entrada = ttk.Entry(formulario, width=30)
                entrada.grid(row=i, column=1, padx=5, pady=3)
                self.entradas[clave] = entrada

        btns = tk.Frame(self, bg="white")
        btns.pack(pady=10)
        acciones = [
            ("Guardar", self.guardar_producto),
            ("Editar", self.editar_producto),
            ("Buscar", self.buscar_producto),
            ("Eliminar", self.eliminar_producto),
            ("Recargar", self.cargar_tabla)
        ]
        for text, cmd in acciones:
            ttk.Button(btns, text=text, command=cmd, width=12)\
              .pack(side="left", padx=5)

        cols = (
            "id", "nombre", "categoria", "precio_compra", "precio_venta",
            "stock", "codigo_interno", "codigo_externo", "iva", "ubicacion", "fecha_vencimiento"
        )
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c.replace("_", " ").capitalize())
            self.tabla.column(c, width=100, anchor="center")
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_producto)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def cargar_categorias(self):
        """
        Pobla el Combobox de categorías con los nombres existentes.
        """
        datos = Categoria.listar()  # devuelve lista de (id, nombre)
        nombres = [nombre for (_id, nombre) in datos]
        self.cmb_categoria["values"] = nombres

    def limpiar_entradas(self):
        for w in self.entradas.values():
            w.delete(0, tk.END)
        self.producto_seleccionado_id = None

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        filas = datos if datos is not None else Producto.listar_todos()
        for f in filas:
            self.tabla.insert("", tk.END, values=f)

    def guardar_producto(self):
        try:
            d = {k: v.get() for k, v in self.entradas.items()}
            Producto.crear(
                d["nombre"],
                d["categoria"],
                float(d["precio_compra"]),
                float(d["precio_venta"]),
                int(d["stock"]),
                d["codigo_interno"],
                d["codigo_externo"],
                float(d["iva"]),
                d["ubicacion"],
                d["fecha_vencimiento"]
            )
            messagebox.showinfo("✅ Éxito", "Producto guardado correctamente.")
            self.limpiar_entradas()
            self.cargar_categorias()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo guardar: {e}")

    def buscar_producto(self):
        nombre = self.entradas["nombre"].get()
        resultados = Producto.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def eliminar_producto(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Atención", "Selecciona un producto para eliminar.")
            return
        pid = self.tabla.item(sel[0])["values"][0]
        Producto.eliminar(pid)
        messagebox.showinfo("🗑️ Eliminado", "Producto eliminado.")
        self.limpiar_entradas()
        self.cargar_tabla()

    def seleccionar_producto(self, event):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        self.producto_seleccionado_id = vals[0]
        # Cargar valores en formulario
        keys = list(self.entradas.keys())
        for i, clave in enumerate(keys):
            self.entradas[clave].delete(0, tk.END)
            self.entradas[clave].insert(0, vals[i+1])

    def editar_producto(self):
        if not self.producto_seleccionado_id:
            messagebox.showwarning("⚠️ Atención", "Selecciona un producto para editar.")
            return
        try:
            d = {k: v.get() for k, v in self.entradas.items()}
            Producto.editar(
                self.producto_seleccionado_id,
                d["nombre"],
                d["categoria"],
                float(d["precio_compra"]),
                float(d["precio_venta"]),
                int(d["stock"]),
                d["codigo_interno"],
                d["codigo_externo"],
                float(d["iva"]),
                d["ubicacion"],
                d["fecha_vencimiento"]
            )
            messagebox.showinfo("✏️ Editado", "Producto actualizado exitosamente.")
            self.limpiar_entradas()
            self.cargar_categorias()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo editar: {e}")
