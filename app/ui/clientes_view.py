# control_negocio/app/ui/clientes_view.py

import tkinter as tk
from tkinter import ttk, messagebox
import re
from app.models.cliente import Cliente


def _rut_basico_valido(rut: str) -> bool:
    """
    Valida RUT de forma básica: cuerpo-dígito, con o sin puntos, con guion.
    (No calcula dígito verificador; sirve para evitar entradas claramente inválidas.)
    """
    if not rut:
        return False
    rut = rut.replace(".", "").strip().upper()
    return bool(re.fullmatch(r"[0-9]{7,8}-[0-9K]", rut))


class ClientesView(tk.Frame):
    def __init__(self, parent, servicios=None):
        """
        Vista de gestión de clientes.
        - No se hace pack aquí; lo maneja el contenedor.
        - 'servicios' queda para futura inyección (compatibilidad con MainWindow).
        """
        super().__init__(parent, bg="white")
        self.servicios = servicios or {}
        self.cliente_seleccionado_id = None

        self._build_ui()
        # Cargar datos cuando ya está montada
        self.after(0, self.cargar_tabla)

    # -----------------------
    # UI
    # -----------------------
    def _build_ui(self):
        # Título
        tk.Label(
            self, text="👥 Gestión de Clientes",
            font=("Segoe UI", 16, "bold"), bg="white"
        ).pack(pady=(12, 6))

        # Formulario
        form = tk.Frame(self, bg="white")
        form.pack(padx=12, pady=6, anchor="w")

        labels = [("Nombre", "nombre"), ("RUT", "rut"), ("Dirección", "direccion"), ("Teléfono", "telefono")]
        self.entradas = {}

        for i, (etq, key) in enumerate(labels):
            tk.Label(form, text=f"{etq}:", bg="white").grid(row=i, column=0, sticky="e", padx=(0, 8), pady=4)
            ent = ttk.Entry(form, width=36)
            ent.grid(row=i, column=1, sticky="w", padx=(0, 12), pady=4)
            self.entradas[key] = ent

        # Atajos de teclado
        self.entradas["nombre"].bind("<Return>", lambda e: self.guardar_cliente())
        self.entradas["rut"].bind("<Return>", lambda e: self.guardar_cliente())
        self.entradas["direccion"].bind("<Return>", lambda e: self.guardar_cliente())
        self.entradas["telefono"].bind("<Return>", lambda e: self.guardar_cliente())
        self.bind_all("<Control-f>", lambda e: self._focus_nombre())

        # Botones
        btns = tk.Frame(self, bg="white")
        btns.pack(padx=12, pady=(2, 10), anchor="w")
        ttk.Button(btns, text="Guardar", width=12, command=self.guardar_cliente).pack(side="left", padx=4)
        ttk.Button(btns, text="Editar",  width=12, command=self.editar_cliente).pack(side="left", padx=4)
        ttk.Button(btns, text="Buscar",  width=12, command=self.buscar_cliente).pack(side="left", padx=4)
        ttk.Button(btns, text="Eliminar",width=12, command=self.eliminar_cliente).pack(side="left", padx=4)
        ttk.Button(btns, text="Recargar",width=12, command=self.cargar_tabla).pack(side="left", padx=4)
        ttk.Button(btns, text="Limpiar", width=12, command=self._limpiar_form).pack(side="left", padx=4)

        # Tabla
        cols = ("id", "nombre", "rut", "direccion", "telefono")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tabla.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Encabezados y tamaños
        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("rut", text="RUT")
        self.tabla.heading("direccion", text="Dirección")
        self.tabla.heading("telefono", text="Teléfono")

        self.tabla.column("id", width=60, anchor="center", stretch=False)
        self.tabla.column("nombre", width=200, anchor="w")
        self.tabla.column("rut", width=120, anchor="center")
        self.tabla.column("direccion", width=280, anchor="w")
        self.tabla.column("telefono", width=120, anchor="center")

        # Scrollbars
        yscroll = ttk.Scrollbar(self, orient="vertical", command=self.tabla.yview)
        yscroll.place(in_=self.tabla, relx=1.0, x=0, y=0, relheight=1.0, anchor="ne")
        self.tabla.configure(yscrollcommand=yscroll.set)

        # Eventos
        self.tabla.bind("<<TreeviewSelect>>", self._seleccionar_fila)
        self.tabla.bind("<Double-1>", self._on_double_click)

        # Estado
        self.status = tk.StringVar(value="Listo.")
        tk.Label(self, textvariable=self.status, bg="white", fg="#555").pack(padx=12, pady=(0, 8), anchor="w")

    def _focus_nombre(self):
        try:
            self.entradas["nombre"].focus_set()
        except Exception:
            pass

    # -----------------------
    # Lógica
    # -----------------------
    def cargar_tabla(self, datos=None):
        """Limpia y carga la tabla de clientes."""
        try:
            for row in self.tabla.get_children():
                self.tabla.delete(row)
            registros = datos if datos is not None else Cliente.listar_todos()
            for r in registros:
                self.tabla.insert("", tk.END, values=r)
            self.status.set(f"{len(registros)} cliente(s) cargado(s).")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar los clientes.\n\n{e}")
            self.status.set("Error al cargar.")

    def _leer_form(self):
        """Lee y valida campos del formulario."""
        d = {k: v.get().strip() for k, v in self.entradas.items()}
        if not all(d.values()):
            raise ValueError("Todos los campos son obligatorios.")
        if not _rut_basico_valido(d["rut"]):
            raise ValueError("RUT inválido. Usa formato 12345678-9 (sin puntos).")
        return d

    def guardar_cliente(self):
        """Crea un nuevo cliente."""
        try:
            d = self._leer_form()
            Cliente.crear(d["nombre"], d["rut"], d["direccion"], d["telefono"])
            self.status.set("Cliente creado correctamente.")
            messagebox.showinfo("✅ Éxito", "Cliente creado correctamente.")
            self._limpiar_form()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))
            self.status.set("Error al crear cliente.")

    def buscar_cliente(self):
        """Filtra por nombre."""
        nombre = self.entradas["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("⚠️ Atención", "Ingresa un nombre para buscar.")
            return
        try:
            resultados = Cliente.buscar_por_nombre(nombre)
            self.cargar_tabla(resultados)
            self.status.set(f"Búsqueda: {len(resultados)} resultado(s).")
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))
            self.status.set("Error en la búsqueda.")

    def _seleccionar_fila(self, _event=None):
        """Carga los datos de la fila seleccionada en el formulario."""
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        if not vals:
            return
        self.cliente_seleccionado_id = vals[0]
        keys = ["nombre", "rut", "direccion", "telefono"]
        for i, key in enumerate(keys):
            self.entradas[key].delete(0, tk.END)
            self.entradas[key].insert(0, vals[i + 1])

    def _on_double_click(self, _event=None):
        """Doble click: pasa foco al primer campo para edición rápida."""
        self._seleccionar_fila()
        self._focus_nombre()

    def editar_cliente(self):
        """Actualiza el cliente seleccionado."""
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("⚠️ Atención", "Selecciona un cliente para editar.")
            return
        try:
            d = self._leer_form()
            Cliente.editar(
                self.cliente_seleccionado_id,
                d["nombre"], d["rut"], d["direccion"], d["telefono"]
            )
            messagebox.showinfo("✏️ Editado", "Cliente actualizado correctamente.")
            self.status.set("Cliente editado.")
            self._limpiar_form()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))
            self.status.set("Error al editar.")

    def eliminar_cliente(self):
        """Elimina el cliente seleccionado."""
        if not self.cliente_seleccionado_id:
            messagebox.showwarning("⚠️ Atención", "Selecciona un cliente para eliminar.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar este cliente?"):
            return
        try:
            Cliente.eliminar(self.cliente_seleccionado_id)
            messagebox.showinfo("🗑️ Eliminado", "Cliente eliminado correctamente.")
            self.status.set("Cliente eliminado.")
            self._limpiar_form()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))
            self.status.set("Error al eliminar.")

    def _limpiar_form(self):
        """Limpia el formulario y resetea la selección."""
        self.cliente_seleccionado_id = None
        for e in self.entradas.values():
            e.delete(0, tk.END)
        self.status.set("Listo.")
