# app/ui/productos_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import unicodedata

from app.models.producto import Producto
from app.models.categoria import Categoria
from app.config.constantes import IVA_RATE  # tasa por defecto (19% -> 0.19)

class ProductosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.producto_seleccionado_id = None
        self.crear_widgets()
        self.cargar_categorias()   # Combobox de categorías
        self.cargar_tabla()

    # ---------- Utils ----------
    @staticmethod
    def limpiar_clave(texto: str) -> str:
        txt = unicodedata.normalize("NFD", texto).lower().replace(" ", "_")
        return "".join(c for c in txt if c.isalnum() or c == "_")

    @staticmethod
    def _to_float(valor: str, nombre: str) -> float:
        try:
            return float(valor.strip().replace(",", "."))
        except Exception:
            raise ValueError(f"'{nombre}' debe ser un número válido.")

    @staticmethod
    def _to_int(valor: str, nombre: str) -> int:
        try:
            return int(valor.strip())
        except Exception:
            raise ValueError(f"'{nombre}' debe ser un entero válido.")

    # ---------- UI ----------
    def crear_widgets(self):
        tk.Label(
            self, text="🛠 Creación de Productos",
            font=("Arial", 16, "bold"), bg="white"
        ).pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        campos = [
            "Nombre", "Categoría", "Precio Compra", "Precio Venta", "Stock",
            "Código Interno", "Código Externo", "IVA", "Ubicación", "Fecha Vencimiento"
        ]
        self.entradas: dict[str, tk.Entry | ttk.Combobox] = {}

        for i, campo in enumerate(campos):
            clave = self.limpiar_clave(campo)
            tk.Label(form, text=campo + ":", bg="white")\
              .grid(row=i, column=0, sticky="e", padx=5, pady=3)

            if campo == "Categoría":
                self.cmb_categoria = ttk.Combobox(form, width=30, state="readonly")
                self.cmb_categoria.grid(row=i, column=1, padx=5, pady=3)
                self.entradas["categoria"] = self.cmb_categoria
            else:
                e = ttk.Entry(form, width=30)
                e.grid(row=i, column=1, padx=5, pady=3)
                # Sugerencias útiles
                if campo == "IVA":
                    e.insert(0, str(IVA_RATE))  # 0.19 por defecto
                if campo == "Stock":
                    e.insert(0, "0")
                self.entradas[clave] = e

        # Botones
        btns = tk.Frame(self, bg="white")
        btns.pack(pady=10)
        acciones = [
            ("Guardar", self.guardar_producto),
            ("Editar", self.editar_producto),
            ("Buscar", self.buscar_producto),
            ("Eliminar", self.eliminar_producto),
            ("Recargar", self.cargar_tabla),
        ]
        for text, cmd in acciones:
            ttk.Button(btns, text=text, command=cmd, width=12)\
              .pack(side="left", padx=5)

        # Tabla
        cols = (
            "id", "nombre", "categoria", "precio_compra", "precio_venta",
            "stock", "codigo_interno", "codigo_externo", "iva", "ubicacion", "fecha_vencimiento"
        )
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c.replace("_", " ").capitalize())
            self.tabla.column(c, width=110 if c != "nombre" else 160, anchor="center")
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_producto)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Datos ----------
    def cargar_categorias(self):
        """
        Pobla el Combobox de categorías con los nombres existentes.
        Si no hay categorías, deja el campo vacío y editable vía entrada directa.
        """
        datos = Categoria.listar()  # [(id, nombre), ...]
        nombres = [nombre for (_id, nombre) in datos]
        if nombres:
            self.cmb_categoria.configure(state="readonly")
            self.cmb_categoria["values"] = nombres
            self.cmb_categoria.set(nombres[0])
        else:
            # Si no hay categorías, lo dejamos sin valores (el usuario puede crear en la vista de Categorías)
            self.cmb_categoria.configure(state="disabled")
            self.cmb_categoria.set("")

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        filas = datos if datos is not None else Producto.listar_todos()
        for f in filas:
            self.tabla.insert("", tk.END, values=f)

    def limpiar_entradas(self):
        for k, w in self.entradas.items():
            if isinstance(w, ttk.Combobox):
                # No tocamos si no hay categorías
                if w.cget("state") == "readonly" and w["values"]:
                    w.set(w["values"][0])
                else:
                    w.set("")
            else:
                w.delete(0, tk.END)
        # Defaults útiles
        if "iva" in self.entradas:
            self.entradas["iva"].insert(0, str(IVA_RATE))
        if "stock" in self.entradas:
            self.entradas["stock"].insert(0, "0")
        self.producto_seleccionado_id = None

    # ---------- Acciones ----------
    def guardar_producto(self):
        try:
            d = {k: (v.get().strip() if isinstance(v, (tk.Entry, ttk.Combobox)) else "") for k, v in self.entradas.items()}
            if not d["nombre"]:
                raise ValueError("El nombre es obligatorio.")

            # Parseos y validaciones
            precio_compra = self._to_float(d["precio_compra"], "Precio Compra")
            precio_venta  = self._to_float(d["precio_venta"], "Precio Venta")
            stock         = self._to_int(d["stock"], "Stock")
            iva_input     = d.get("iva", str(IVA_RATE)) or str(IVA_RATE)
            iva_val       = self._to_float(iva_input, "IVA")

            # Crear
            Producto.crear(
                d["nombre"],
                d.get("categoria", ""),
                float(precio_compra),
                float(precio_venta),
                int(stock),
                d.get("codigo_interno", ""),
                d.get("codigo_externo", ""),
                float(iva_val),
                d.get("ubicacion", ""),
                d.get("fecha_vencimiento", ""),
            )
            messagebox.showinfo("✅ Éxito", "Producto guardado correctamente.")
            self.limpiar_entradas()
            self.cargar_categorias()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo guardar: {e}")

    def seleccionar_producto(self, _event):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        # vals ordena como columnas de la tabla
        self.producto_seleccionado_id = vals[0]

        # Mapear al formulario (saltamos el id)
        mapping = [
            ("nombre", 1),
            ("categoria", 2),
            ("precio_compra", 3),
            ("precio_venta", 4),
            ("stock", 5),
            ("codigo_interno", 6),
            ("codigo_externo", 7),
            ("iva", 8),
            ("ubicacion", 9),
            ("fecha_vencimiento", 10),
        ]
        for key, idx in mapping:
            w = self.entradas.get(key)
            if not w:
                continue
            valor = vals[idx] if idx < len(vals) else ""
            if isinstance(w, ttk.Combobox):
                # Si la categoría no existe en la lista actual, deshabilitamos readonly para mostrarla
                if w.cget("state") == "readonly" and w["values"] and valor in w["values"]:
                    w.set(valor)
                else:
                    w.configure(state="normal")
                    w.delete(0, tk.END)
                    w.insert(0, valor)
                    w.configure(state="readonly" if w["values"] else "disabled")
            else:
                w.delete(0, tk.END)
                w.insert(0, valor)

    def editar_producto(self):
        if not self.producto_seleccionado_id:
            return messagebox.showwarning("⚠️ Atención", "Selecciona un producto para editar.")
        try:
            d = {k: (v.get().strip() if isinstance(v, (tk.Entry, ttk.Combobox)) else "") for k, v in self.entradas.items()}
            if not d["nombre"]:
                raise ValueError("El nombre es obligatorio.")

            precio_compra = self._to_float(d["precio_compra"], "Precio Compra")
            precio_venta  = self._to_float(d["precio_venta"], "Precio Venta")
            stock         = self._to_int(d["stock"], "Stock")
            iva_input     = d.get("iva", str(IVA_RATE)) or str(IVA_RATE)
            iva_val       = self._to_float(iva_input, "IVA")

            Producto.editar(
                self.producto_seleccionado_id,
                d["nombre"],
                d.get("categoria", ""),
                float(precio_compra),
                float(precio_venta),
                int(stock),
                d.get("codigo_interno", ""),
                d.get("codigo_externo", ""),
                float(iva_val),
                d.get("ubicacion", ""),
                d.get("fecha_vencimiento", ""),
            )
            messagebox.showinfo("✏️ Editado", "Producto actualizado exitosamente.")
            self.limpiar_entradas()
            self.cargar_categorias()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo editar: {e}")

    def eliminar_producto(self):
        sel = self.tabla.selection()
        if not sel:
            return messagebox.showwarning("⚠️ Atención", "Selecciona un producto para eliminar.")
        pid = self.tabla.item(sel[0])["values"][0]
        try:
            if not messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
                return
            Producto.eliminar(pid)
            messagebox.showinfo("🗑️ Eliminado", "Producto eliminado.")
            self.limpiar_entradas()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo eliminar: {e}")

    def buscar_producto(self):
        nombre = (self.entradas.get("nombre").get() if self.entradas.get("nombre") else "").strip()
        if not nombre:
            messagebox.showwarning("⚠️ Atención", "Ingresa un nombre para buscar.")
            return
        resultados = Producto.buscar_por_nombre(nombre)
        if not resultados:
            messagebox.showinfo("🔎 Sin resultados", "No se encontraron productos para ese nombre.")
        self.cargar_tabla(resultados)
