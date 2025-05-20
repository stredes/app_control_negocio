# control_negocio/app/ui/proveedores_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.proveedor import Proveedor

class ProveedoresView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.proveedor_editando = None  # ID del proveedor en edición
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Gestión de Proveedores", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        campos = ["Nombre", "RUT", "Dirección", "Teléfono", "Razón Social", "Correo", "Comuna"]
        self.entradas = {}

        for i, campo in enumerate(campos):
            tk.Label(formulario, text=campo + ":", bg="white").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            entrada = ttk.Entry(formulario, width=30)
            entrada.grid(row=i, column=1, pady=5, padx=5)
            self.entradas[campo.lower().replace(" ", "_")] = entrada

        botones = tk.Frame(self, bg="white")
        botones.pack(pady=10)

        acciones = [
            ("Guardar", self.guardar_proveedor),
            ("Buscar", self.buscar_proveedor),
            ("Eliminar", self.eliminar_proveedor),
            ("Editar", self.editar_proveedor),
            ("Recargar", self.cargar_tabla)
        ]

        for texto, accion in acciones:
            ttk.Button(botones, text=texto, command=accion, width=12).pack(side="left", padx=5)

        columnas = ("id", "nombre", "rut", "direccion", "telefono", "razon_social", "correo", "comuna")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings")
        for col in columnas:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=120)
        self.tabla.pack(pady=10, fill="x")

    def limpiar_entradas(self):
        for entrada in self.entradas.values():
            entrada.delete(0, tk.END)
        self.proveedor_editando = None

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        proveedores = datos if datos else Proveedor.listar_todos()
        for prov in proveedores:
            self.tabla.insert("", tk.END, values=prov)

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
            messagebox.showinfo("Éxito", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")

    def buscar_proveedor(self):
        nombre = self.entradas["nombre"].get()
        resultados = Proveedor.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def eliminar_proveedor(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un proveedor para eliminar.")
            return
        item = self.tabla.item(seleccionado[0])
        proveedor_id = item["values"][0]
        Proveedor.eliminar(proveedor_id)
        self.cargar_tabla()
        messagebox.showinfo("Eliminado", "Proveedor eliminado correctamente.")

    def editar_proveedor(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un proveedor para editar.")
            return
        item = self.tabla.item(seleccionado[0])
        datos = item["values"]
        keys = list(self.entradas.keys())
        for i in range(1, len(keys)+1):
            self.entradas[keys[i-1]].delete(0, tk.END)
            self.entradas[keys[i-1]].insert(0, datos[i])
        self.proveedor_editando = datos[0]  # Guardamos ID
