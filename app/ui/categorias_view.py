from tkinter import Frame, Label, Entry, Button, Listbox, Scrollbar, END, messagebox
from app.models.categoria import Categoria

class CategoriasView(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.crear_widgets()

    def crear_widgets(self):
        Label(self, text="🏷️ Gestión de Categorías", font=("Arial", 16, "bold")).pack(pady=10)

        self.entrada = Entry(self, width=40)
        self.entrada.pack(pady=5)

        Button(self, text="➕ Agregar Categoría", command=self.agregar_categoria).pack(pady=5)

        self.lista = Listbox(self, width=50, height=15)
        self.lista.pack(padx=10, pady=10)

        scrollbar = Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        self.lista.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lista.yview)

        Button(self, text="🗑 Eliminar Seleccionada", command=self.eliminar_categoria).pack(pady=5)

        self.cargar_categorias()

    def cargar_categorias(self):
        self.lista.delete(0, END)
        for cat in Categoria.listar():
            self.lista.insert(END, f"{cat[0]} - {cat[1]}")

    def agregar_categoria(self):
        nombre = self.entrada.get().strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debes ingresar un nombre.")
            return
        Categoria.agregar(nombre)
        self.entrada.delete(0, END)
        self.cargar_categorias()

    def eliminar_categoria(self):
        seleccion = self.lista.curselection()
        if not seleccion:
            return
        valor = self.lista.get(seleccion[0])
        id_cat = int(valor.split(" - ")[0])
        Categoria.eliminar(id_cat)
        self.cargar_categorias()
