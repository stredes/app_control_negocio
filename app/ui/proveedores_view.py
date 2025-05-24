import tkinter as tk
from tkinter import ttk, messagebox
from app.models.proveedor import Proveedor
import unicodedata

class ProveedoresView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.proveedor_editando = None
        self.crear_widgets()
        self.cargar_tabla()

    def limpiar_clave(self, texto):
        # Normaliza (quita tildes), pasa a minúsculas, convierte espacios en "_" y filtra solo alfanuméricos/_
        txt = unicodedata.normalize('NFD', texto).lower().replace(" ", "_")
        return ''.join(c for c in txt if c.isalnum() or c == "_")

    def crear_widgets(self):
        tk.Label(self, text="🏭 Gestión de Proveedores",
                 font=("Arial", 16, "bold"), bg="white")\
          .pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        campos = ["Nombre", "RUT", "Dirección", "Teléfono",
                  "Razón Social", "Correo Electrónico", "Comuna"]
        self.entradas = {}

        for i, campo in enumerate(campos):
            clave = self.limpiar_clave(campo)
            tk.Label(formulario, text=campo + ":", bg="white")\
              .grid(row=i, column=0, sticky="e", padx=5, pady=3)
            entrada = ttk.Entry(formulario, width=30)
            entrada.grid(row=i, column=1, padx=5, pady=3)
            self.entradas[clave] = entrada

        botones = tk.Frame(self, bg="white")
        botones.pack(pady=10)

        acciones = [
            ("Guardar", self.guardar_proveedor),
            ("Buscar", self.buscar_proveedor),
            ("Editar", self.preparar_edicion),
            ("Eliminar", self.eliminar_proveedor),
            ("Recargar", self.cargar_tabla)
        ]
        for texto, cmd in acciones:
            ttk.Button(botones, text=texto, command=cmd, width=12)\
               .pack(side="left", padx=5)

        cols = ("id", "nombre", "rut", "direccion", "telefono",
                "razon_social", "correo_electronico", "comuna")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            # capitaliza y reemplaza "_" por espacio
            self.tabla.heading(c, text=c.replace("_", " ").capitalize())
            self.tabla.column(c, width=120)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_proveedor)
        self.tabla.pack(fill="both", expand=True, pady=10)

    def limpiar_entradas(self):
        for e in self.entradas.values():
            e.delete(0, tk.END)
        self.proveedor_editando = None

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        rows = datos if datos is not None else Proveedor.listar_todos()
        for r in rows:
            self.tabla.insert("", tk.END, values=r)

    def guardar_proveedor(self):
        try:
            datos = {k: v.get().strip() for k, v in self.entradas.items()}
            if not all(datos.values()):
                raise ValueError("Todos los campos son obligatorios.")

            if self.proveedor_editando:
                Proveedor.editar(self.proveedor_editando, *datos.values())
                mensaje = "Proveedor actualizado correctamente."
            else:
                Proveedor.crear(*datos.values())
                mensaje = "Proveedor creado correctamente."

            self.limpiar_entradas()
            self.cargar_tabla()
            messagebox.showinfo("✅ Éxito", mensaje)

        except Exception as e:
            messagebox.showerror("❌ Error", f"Ocurrió un error: {e}")

    def buscar_proveedor(self):
        nombre = self.entradas["nombre"].get().strip()
        resultados = Proveedor.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def preparar_edicion(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Atención", "Selecciona un proveedor para editar.")
            return
        vals = self.tabla.item(sel[0])["values"]
        self.proveedor_editando = vals[0]
        # Carga en formulario todos los campos
        keys = list(self.entradas.keys())
        for i, clave in enumerate(keys):
            self.entradas[clave].delete(0, tk.END)
            self.entradas[clave].insert(0, vals[i+1])

    def eliminar_proveedor(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Atención", "Selecciona un proveedor para eliminar.")
            return
        pid = self.tabla.item(sel[0])["values"][0]
        Proveedor.eliminar(pid)
        self.limpiar_entradas()
        self.cargar_tabla()
        messagebox.showinfo("🗑️ Eliminado", "Proveedor eliminado correctamente.")

    def seleccionar_proveedor(self, event):
        # Opcional: al hacer clic carga en el formulario (sin activar edición)
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        keys = list(self.entradas.keys())
        for i, clave in enumerate(keys):
            self.entradas[clave].delete(0, tk.END)
            self.entradas[clave].insert(0, vals[i+1])
def limpiar_entradas(self):
        for clave in self.entradas.keys():
            self.entradas[clave].delete(0, tk.END)