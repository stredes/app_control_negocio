# control_negocio/app/ui/categorias_view.py

import tkinter as tk
from tkinter import END, messagebox
from app.models.categoria import Categoria

class CategoriasView(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, bg="white")
        self.master = master
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        # Título
        tk.Label(self, text="🏷️ Gestión de Categorías", 
                 font=("Arial", 16, "bold"), bg="white")\
          .pack(pady=10)

        # Entrada nueva categoría
        self.entrada = tk.Entry(self, width=40)
        self.entrada.pack(pady=5)

        # Botón agregar
        tk.Button(self, text="➕ Agregar Categoría", 
                  command=self.agregar_categoria)\
          .pack(pady=5)

        # Listbox con scroll
        container = tk.Frame(self, bg="white")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        self.lista = tk.Listbox(container, width=50, height=15)
        self.lista.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(container, command=self.lista.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista.config(yscrollcommand=scrollbar.set)

        # Botón eliminar selección
        tk.Button(self, text="🗑 Eliminar Seleccionada", 
                  command=self.eliminar_categoria)\
          .pack(pady=5)

        self.cargar_categorias()

    def cargar_categorias(self):
        """Carga todas las categorías en el Listbox."""
        self.lista.delete(0, END)
        for cat in Categoria.listar():
            # cat = (id, nombre)
            self.lista.insert(END, f"{cat[0]} - {cat[1]}")

    def agregar_categoria(self):
        """Agrega una nueva categoría y refresca la lista."""
        nombre = self.entrada.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debes ingresar un nombre.")
            return
        Categoria.agregar(nombre)
        self.entrada.delete(0, END)
        self.cargar_categorias()

    def eliminar_categoria(self):
        """Elimina la categoría seleccionada en el Listbox."""
        seleccion = self.lista.curselection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona una categoría.")
            return
        valor = self.lista.get(seleccion[0])
        id_cat = int(valor.split(" - ")[0])
        Categoria.eliminar(id_cat)
        self.cargar_categorias()
