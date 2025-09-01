# app/ui/proveedores_view.py
import re
import unicodedata
import tkinter as tk
from tkinter import ttk, messagebox

from app.models.proveedor import Proveedor


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _rut_clean(rut: str) -> str:
    """Quita puntos/espacios/guiones, deja sólo dígitos + DV (K permitido)."""
    if not rut:
        return ""
    r = rut.replace(".", "").replace(" ", "").replace("-", "").upper()
    return r


def _rut_is_valid(rut: str) -> bool:
    """
    Valida RUT chileno (módulo 11).
    Acepta '12.345.678-5', '12345678-5', '123456785', o '12345678K'.
    """
    r = _rut_clean(rut)
    if len(r) < 2 or not r[:-1].isdigit():
        return False
    cuerpo, dv = r[:-1], r[-1]
    factores = [2, 3, 4, 5, 6, 7]
    suma, idx = 0, 0
    for d in reversed(cuerpo):
        suma += int(d) * factores[idx]
        idx = (idx + 1) % len(factores)
    resto = 11 - (suma % 11)
    dv_calc = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    return dv_calc == dv


def _email_is_valid(email: str) -> bool:
    if not email:
        return False
    # Regex simple para UI
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None


def _phone_sanitize(phone: str) -> str:
    phone = phone.strip()
    if not phone:
        return phone
    plus = "+" if phone.startswith("+") else ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    return plus + digits


class ProveedoresView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.proveedor_editando = None
        self._build_ui()
        self.cargar_tabla()

    # ------------- Utils -------------
    @staticmethod
    def limpiar_clave(texto: str) -> str:
        # Quita tildes, pasa a minúsculas, espacios -> "_", sólo alfanum/_
        txt = _strip_accents(texto).lower().replace(" ", "_")
        return "".join(c for c in txt if c.isalnum() or c == "_")

    def _get_form_data(self) -> dict:
        """Lee formulario y aplica saneos/validaciones básicas."""
        d = {k: e.get().strip() for k, e in self.entradas.items()}

        # Validaciones mínimas
        if not d["nombre"]:
            raise ValueError("El nombre es obligatorio.")
        if not d["rut"]:
            raise ValueError("El RUT es obligatorio.")
        if not _rut_is_valid(d["rut"]):
            raise ValueError("RUT inválido. Ejemplos válidos: 12.345.678-5 / 12345678-K")

        if not d["correo_electronico"]:
            raise ValueError("El correo es obligatorio.")
        if not _email_is_valid(d["correo_electronico"]):
            raise ValueError("Correo electrónico inválido.")

        # Saneos
        d["telefono"] = _phone_sanitize(d["telefono"])

        return d

    # ------------- UI -------------
    def _build_ui(self):
        tk.Label(
            self, text="🏭 Gestión de Proveedores",
            font=("Arial", 16, "bold"), bg="white"
        ).pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        campos = [
            "Nombre", "RUT", "Dirección", "Teléfono",
            "Razón Social", "Correo Electrónico", "Comuna"
        ]
        self.entradas = {}
        for i, campo in enumerate(campos):
            clave = self.limpiar_clave(campo)
            tk.Label(form, text=campo + ":", bg="white")\
              .grid(row=i, column=0, sticky="e", padx=5, pady=3)
            e = ttk.Entry(form, width=32)
            e.grid(row=i, column=1, padx=5, pady=3)
            self.entradas[clave] = e

        btns = tk.Frame(self, bg="white")
        btns.pack(pady=10)
        acciones = [
            ("Guardar", self.guardar_proveedor),
            ("Buscar", self.buscar_proveedor),
            ("Editar", self.preparar_edicion),
            ("Eliminar", self.eliminar_proveedor),
            ("Recargar", self.cargar_tabla),
        ]
        for texto, cmd in acciones:
            ttk.Button(btns, text=texto, command=cmd, width=12)\
               .pack(side="left", padx=5)

        cols = ("id", "nombre", "rut", "direccion", "telefono",
                "razon_social", "correo", "comuna")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tabla.heading(c, text=c.replace("_", " ").capitalize())
            self.tabla.column(c, width=130 if c != "nombre" else 160, anchor="center")
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar_proveedor)
        self.tabla.pack(fill="both", expand=True, pady=10, padx=10)

    # ------------- Helpers -------------
    def limpiar_entradas(self):
        for e in self.entradas.values():
            e.delete(0, tk.END)
        self.proveedor_editando = None

    def cargar_tabla(self, datos=None):
        for r in self.tabla.get_children():
            self.tabla.delete(r)
        rows = datos if datos is not None else Proveedor.listar_todos()
        for r in rows:
            self.tabla.insert("", tk.END, values=r)

    # ------------- Acciones -------------
    def guardar_proveedor(self):
        try:
            datos = self._get_form_data()

            # Orden posicional tal como espera el modelo:
            # crear(nombre, rut, direccion, telefono, razon_social, correo, comuna)
            args = (
                datos["nombre"],
                datos["rut"],
                datos["direccion"],
                datos["telefono"],
                datos["razon_social"],
                datos["correo_electronico"],
                datos["comuna"],
            )

            if self.proveedor_editando:
                Proveedor.editar(self.proveedor_editando, *args)
                msg = "Proveedor actualizado correctamente."
            else:
                Proveedor.crear(*args)
                msg = "Proveedor creado correctamente."

            self.limpiar_entradas()
            self.cargar_tabla()
            messagebox.showinfo("✅ Éxito", msg)

        except Exception as e:
            messagebox.showerror("❌ Error", f"Ocurrió un error: {e}")

    def buscar_proveedor(self):
        nombre = self.entradas["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("⚠️ Atención", "Ingresa un nombre para buscar.")
            return
        resultados = Proveedor.buscar_por_nombre(nombre)
        if not resultados:
            messagebox.showinfo("🔎 Sin resultados", "No se encontraron proveedores con ese nombre.")
        self.cargar_tabla(resultados)

    def preparar_edicion(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("⚠️ Atención", "Selecciona un proveedor para editar.")
            return
        vals = self.tabla.item(sel[0])["values"]
        self.proveedor_editando = vals[0]

        # Mapea columnas -> formulario (saltamos id)
        mapping = [
            ("nombre", 1),
            ("rut", 2),
            ("direccion", 3),
            ("telefono", 4),
            ("razon_social", 5),
            ("correo_electronico", 6),  # en tabla es 'correo'
            ("comuna", 7),
        ]
        for key, idx in mapping:
            w = self.entradas.get(key)
            if not w:
                continue
            w.delete(0, tk.END)
            w.insert(0, vals[idx])

    def eliminar_proveedor(self):
        sel = self.tabla.selection()
        if not sel:
            return messagebox.showwarning("⚠️ Atención", "Selecciona un proveedor para eliminar.")
        pid = self.tabla.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirmar", "¿Eliminar este proveedor?"):
            return
        try:
            Proveedor.eliminar(pid)
            self.limpiar_entradas()
            self.cargar_tabla()
            messagebox.showinfo("🗑️ Eliminado", "Proveedor eliminado correctamente.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo eliminar: {e}")

    def seleccionar_proveedor(self, _event):
        """
        Carga la fila seleccionada al formulario (sin marcar edición).
        """
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        mapping = [
            ("nombre", 1),
            ("rut", 2),
            ("direccion", 3),
            ("telefono", 4),
            ("razon_social", 5),
            ("correo_electronico", 6),
            ("comuna", 7),
        ]
        for key, idx in mapping:
            w = self.entradas.get(key)
            if not w:
                continue
            w.delete(0, tk.END)
            w.insert(0, vals[idx])
