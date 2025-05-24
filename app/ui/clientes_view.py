# control_negocio/app/ui/clientes_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from app.models.cliente import Cliente

class ClientesView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.cliente_seleccionado_id = None
        self.crear_widgets()
        self.cargar_tabla()

    def crear_widgets(self):
        # Título
        tk.Label(self, text="👥 Gestión de Clientes",
                 font=("Arial", 16, "bold"), bg="white")\
          .pack(pady=10)

        # Formulario
        form = tk.Frame(self, bg="white")
        form.pack(pady=10, padx=10)

        campos = ["Nombre", "RUT", "Dirección", "Teléfono"]
        self.entradas = {}

        for i, campo in enumerate(campos):
            tk.Label(form, text=campo + ":", bg="white")\
              .grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            # clave sin espacios ni tildes
            clave = campo.lower().replace("á","a").replace("ó","o").replace("é","e").replace("í","i").replace("ú","u").replace("ñ","n").replace(" ", "_")
            self.entradas[clave] = entry

        # Botones
        btns = tk.Frame(self, bg="white")
        btns.pack(pady=10)
        acciones = [
            ("Guardar", self.guardar_cliente),
            ("Editar",  self.editar_cliente),
            ("Buscar",  self.buscar_cliente),
            ("Eliminar",self.eliminar_cliente),
            ("Recargar",self.cargar_tabla)
        ]
        for texto, cmd in acciones:
            ttk.Button(btns, text=texto, command=cmd, width=12)\
              .pack(side="left", padx=5)

        # Tabla de clientes
        cols = ("id", "nombre", "rut", "direccion", "telefono")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c.capitalize())
            self.tabla.column(c, width=120, anchor="center")
        self.tabla.bind("<<TreeviewSelect>>", self._seleccionar_fila)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def cargar_tabla(self, datos=None):
        """
        Limpia y carga la tabla de clientes.
        """
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        registros = datos if datos is not None else Cliente.listar_todos()
        for r in registros:
            self.tabla.insert("", tk.END, values=r)

    def guardar_cliente(self):
        """
        Crea un nuevo cliente.
        """
        try:
            d = {k: v.get().strip() for k, v in self.entradas.items()}
            if not all(d.values()):
                raise ValueError("Todos los campos son obligatorios.")
            Cliente.crear(d["nombre"], d["rut"], d["direccion"], d["telefono"])
            messagebox.showinfo("✅ Éxito", "Cliente creado correctamente.")
            self._limpiar_form()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def buscar_cliente(self):
        """
        Filtra por nombre.
        """
        nombre = self.entradas["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("⚠️ Atención", "Ingresa un nombre para buscar.")
            return
        resultados = Cliente.buscar_por_nombre(nombre)
        self.cargar_tabla(resultados)

    def _seleccionar_fila(self, event):
        """
        Carga los datos de la fila seleccionada en el formulario.
        """
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        self.cliente_seleccionado_id = vals[0]
        keys = list(self.entradas.keys())
        for i, key in enumerate(keys):
            self.entradas[key].delete(0, tk.END)
            self.entradas[key].insert(0, vals[i+1])

    def editar_cliente(self):
        """
        Actualiza el cliente seleccionado.
        """
        if not self.cliente_seleccionado_id:
            return messagebox.showwarning("⚠️ Atención", "Selecciona un cliente para editar.")
        try:
            d = {k: v.get().strip() for k, v in self.entradas.items()}
            if not all(d.values()):
                raise ValueError("Todos los campos son obligatorios.")
            Cliente.editar(
                self.cliente_seleccionado_id,
                d["nombre"], d["rut"], d["direccion"], d["telefono"]
            )
            messagebox.showinfo("✏️ Editado", "Cliente actualizado correctamente.")
            self._limpiar_form()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def eliminar_cliente(self):
        """
        Elimina el cliente seleccionado.
        """
        if not self.cliente_seleccionado_id:
            return messagebox.showwarning("⚠️ Atención", "Selecciona un cliente para eliminar.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar este cliente?"):
            return
        try:
            Cliente.eliminar(self.cliente_seleccionado_id)
            messagebox.showinfo("🗑️ Eliminado", "Cliente eliminado correctamente.")
            self._limpiar_form()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def _limpiar_form(self):
        """
        Limpia el formulario y resetea la selección.
        """
        self.cliente_seleccionado_id = None
        for e in self.entradas.values():
            e.delete(0, tk.END)
