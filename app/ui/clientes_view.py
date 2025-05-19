# control_negocio/app/ui/clientes_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.cliente import Cliente

class ClientesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Gestión de Clientes", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        formulario = tk.Frame(self, bg="white")
        formulario.pack(pady=10)

        campos = ["Nombre", "RUT", "Dirección", "Teléfono"]
        self.entradas = {}

        for i, campo in enumerate(campos):
            tk.Label(formulario, text=campo + ":", bg="white").grid(row=i, column=0, sticky="e", pady=5, padx=5)
            entrada = ttk.Entry(formulario, width=30)
            entrada.grid(row=i, column=1, pady=5, padx=5)
            self.entradas[campo.lower()] = entrada

        botones = tk.Frame(self, bg="white")
        botones.pack(pady=10)

        acciones = [
            ("Guardar", self.guardar_cliente),
            ("Buscar", self.buscar_cliente),
            ("Eliminar", self.eliminar_cliente),
            ("Recargar", self.cargar_tabla)
        ]

        for texto, accion in acciones:
            ttk.Button(botones, text=texto, command=accion, width=12).pack(side="left", padx=10)

        self.tabla = ttk.Treeview(self, columns=("id", "nombre", "rut", "direccion", "telefono"), show="headings")
        for col in self.tabla["columns"]:
            self.tabla.heading(col, text=col.capitalize())
            self.tabla.column(col, width=130)
        self.tabla.pack(pady=10, fill="x")

    def limpiar_entradas(self):
        for entrada in self.entradas.values():
            entrada.delete(0, tk.END)

    def cargar_tabla(self, datos=None):
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        clientes = datos if datos else Cliente.listar_todos()
        for cli in clientes:
            self.tabla.insert("", tk.END, values=cli)

    def guardar_cliente(self):
        try:
            datos = {k: v.get() for k, v in self.entradas.items()}
            Cliente.crear(
                datos["nombre"],
                datos["rut"],
                datos["dirección"],
                datos["teléfono"]
            )
            self.cargar_tabla()
            self.limpiar_entradas()
            messagebox.showinfo("Éxito", "Cliente guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def buscar_cliente(self):
        nombre = self.entradas["nombre"].get()
        resultados = Cliente.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def eliminar_cliente(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un cliente para eliminar.")
            return
        item = self.tabla.item(seleccionado[0])
        cliente_id = item["values"][0]
        Cliente.eliminar(cliente_id)
        self.cargar_tabla()
        messagebox.showinfo("Eliminado", "Cliente eliminado.")

    