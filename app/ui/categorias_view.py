# control_negocio/app/ui/categorias_view.py

import tkinter as tk
from tkinter import END, messagebox
import sqlite3

from app.models.categoria import Categoria


class CategoriasView(tk.Frame):
    def __init__(self, master=None, servicios=None):
        """
        Vista de gestión de categorías.
        - No se hace pack/grid aquí: lo realiza el contenedor (MainWindow).
        - 'servicios' queda por compatibilidad con inyección futura.
        """
        super().__init__(master, bg="white")
        self.servicios = servicios or {}
        self._build_ui()
        # Cargar datos cuando la vista ya fue montada
        self.after(0, self.cargar_categorias)

    # ------------------------
    # UI
    # ------------------------
    def _build_ui(self):
        # Título
        tk.Label(
            self,
            text="🏷️ Gestión de Categorías",
            font=("Segoe UI", 16, "bold"),
            bg="white",
        ).pack(pady=(12, 4))

        # Entrada + botones
        top = tk.Frame(self, bg="white")
        top.pack(fill="x", padx=12, pady=6)

        tk.Label(top, text="Nombre:", bg="white").pack(side="left", padx=(0, 6))
        self.entrada = tk.Entry(top, width=38)
        self.entrada.pack(side="left", padx=(0, 8))
        self.entrada.bind("<Return>", lambda e: self.agregar_categoria())

        btns = tk.Frame(top, bg="white")
        btns.pack(side="left")

        tk.Button(btns, text="➕ Agregar", command=self.agregar_categoria).pack(side="left", padx=4)
        tk.Button(btns, text="✏️ Renombrar", command=self.renombrar_categoria).pack(side="left", padx=4)
        tk.Button(btns, text="🔄 Recargar", command=self.cargar_categorias).pack(side="left", padx=4)

        # Lista con scroll
        container = tk.Frame(self, bg="white")
        container.pack(fill="both", expand=True, padx=12, pady=(6, 10))

        self.lista = tk.Listbox(container, width=50, height=16, activestyle="none")
        self.lista.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, command=self.lista.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista.config(yscrollcommand=scrollbar.set)

        self.lista.bind("<<ListboxSelect>>", self._on_select)

        # Botón eliminar
        tk.Button(
            self,
            text="🗑 Eliminar Seleccionada",
            command=self.eliminar_categoria,
            bg="#f8f8f8",
        ).pack(pady=(0, 10))

        # Mensaje de estado simple
        self.status = tk.StringVar(value="Listo.")
        tk.Label(self, textvariable=self.status, bg="white", fg="#555").pack(pady=(0, 8))

    # ------------------------
    # Lógica
    # ------------------------
    def cargar_categorias(self):
        """Carga todas las categorías en el Listbox."""
        try:
            self.lista.delete(0, END)
            for cat_id, nombre in Categoria.listar():
                self.lista.insert(END, f"{cat_id} - {nombre}")
            self.status.set(f"Se cargaron {self.lista.size()} categorías.")
        except Exception as e:
            self.status.set("Error al cargar categorías.")
            messagebox.showerror("Error", f"No se pudieron cargar las categorías.\n\n{e}")

    def _selected_id(self) -> int | None:
        """Devuelve el ID seleccionado en la lista, o None si no hay selección."""
        sel = self.lista.curselection()
        if not sel:
            return None
        try:
            valor = self.lista.get(sel[0])
            return int(str(valor).split(" - ", 1)[0])
        except Exception:
            return None

    def _on_select(self, _event=None):
        """Cuando seleccionas una fila, copia el nombre a la entrada para edición rápida."""
        sel = self.lista.curselection()
        if not sel:
            return
        valor = self.lista.get(sel[0])
        try:
            _, nombre = str(valor).split(" - ", 1)
        except ValueError:
            nombre = ""
        self.entrada.delete(0, END)
        self.entrada.insert(0, nombre)

    def agregar_categoria(self):
        """Agrega una nueva categoría y refresca la lista."""
        nombre = (self.entrada.get() or "").strip()
        if not nombre:
            messagebox.showwarning("Atención", "Debes ingresar un nombre.")
            return
        try:
            Categoria.agregar(nombre)
            self.entrada.delete(0, END)
            self.cargar_categorias()
            self.status.set(f"Categoría '{nombre}' agregada.")
        except sqlite3.IntegrityError:
            # UNIQUE(nombre) en DB
            messagebox.showwarning("Duplicado", "Ya existe una categoría con ese nombre.")
            self.status.set("Intento duplicado.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar la categoría.\n\n{e}")
            self.status.set("Error al agregar.")

    def renombrar_categoria(self):
        """Renombra la categoría seleccionada usando el texto de la entrada."""
        cat_id = self._selected_id()
        if cat_id is None:
            messagebox.showwarning("Atención", "Selecciona una categoría para renombrar.")
            return
        nuevo = (self.entrada.get() or "").strip()
        if not nuevo:
            messagebox.showwarning("Atención", "Debes ingresar un nuevo nombre.")
            return
        try:
            Categoria.editar(cat_id, nuevo)
            self.cargar_categorias()
            self.status.set(f"Categoría #{cat_id} renombrada a '{nuevo}'.")
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicado", "Ya existe una categoría con ese nombre.")
            self.status.set("Intento duplicado al renombrar.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo renombrar la categoría.\n\n{e}")
            self.status.set("Error al renombrar.")

    def eliminar_categoria(self):
        """Elimina la categoría seleccionada en el Listbox."""
        cat_id = self._selected_id()
        if cat_id is None:
            messagebox.showwarning("Atención", "Selecciona una categoría.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta categoría?"):
            return
        try:
            Categoria.eliminar(cat_id)
            self.cargar_categorias()
            self.entrada.delete(0, END)
            self.status.set(f"Categoría #{cat_id} eliminada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la categoría.\n\n{e}")
            self.status.set("Error al eliminar.")
