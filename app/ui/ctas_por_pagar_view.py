# app/ui/ctas_por_pagar_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from app.models.finanzas import Finanzas

# Intentar usar el modelo extendido si está disponible
try:
    from app.models.factura import Factura
except Exception:
    Factura = None

# Tipos de documento (si existen)
try:
    from app.config.tipos import DocTipo
    DOC_TIPOS = [
        DocTipo.FACTURA.value,
        DocTipo.FACTURA_EXENTA.value,
        DocTipo.BOLETA.value,
        DocTipo.BOLETA_EXENTA.value,
        DocTipo.BOLETA_HONORARIOS.value,
    ]
except Exception:
    DocTipo = None
    DOC_TIPOS = ["FACTURA", "FACTURA_EXENTA", "BOLETA", "BOLETA_EXENTA", "BOLETA_HONORARIOS"]

DEFAULT_PAYMENT_DAYS = 30  # fallback si no tienes la constante centralizada


class CtasPorPagarView(tk.Frame):
    """
    - Modo extendido: usa columnas doc_tipo, neto, iva, retencion, total, vencimiento si existen.
    - Modo legacy: usa Finanzas.* (monto, estado, fecha, etc.).
    - No llama pack()/grid() en __init__.
    """

    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.cta_sel_id = None
        self.var_estado_filtro = tk.StringVar(value="todos")
        self._extended = self._is_extended_schema()

        self._build_ui()
        self.after(0, self.cargar_ctas)

    # ---------------- Utilidades ----------------

    def _is_extended_schema(self) -> bool:
        try:
            if Factura is None:
                return False
            return bool(Factura._extended_enabled())
        except Exception:
            return False

    def _fmt_money(self, x) -> str:
        try:
            val = float(x or 0)
        except Exception:
            val = 0.0
        return f"${val:,.2f}"

    def _default_venc(self, iso: str) -> str:
        try:
            y, m, d = map(int, iso.split("-"))
            return (date(y, m, d) + timedelta(days=DEFAULT_PAYMENT_DAYS)).isoformat()
        except Exception:
            return iso

    # ---------------- UI ----------------

    def _build_ui(self):
        tk.Label(self, text="📋 Cuentas por Pagar", font=("Segoe UI", 16, "bold"), bg="white")\
            .pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(padx=10, pady=6, anchor="w")

        # Número
        tk.Label(form, text="Número:", bg="white").grid(row=0, column=0, sticky="e", padx=6, pady=3)
        self.ent_numero = ttk.Entry(form, width=22)
        self.ent_numero.grid(row=0, column=1, padx=6, pady=3)

        # Proveedor
        tk.Label(form, text="Proveedor:", bg="white").grid(row=1, column=0, sticky="e", padx=6, pady=3)
        self.ent_proveedor = ttk.Entry(form, width=22)
        self.ent_proveedor.grid(row=1, column=1, padx=6, pady=3)

        # Monto (total)
        tk.Label(form, text="Monto (total):", bg="white").grid(row=2, column=0, sticky="e", padx=6, pady=3)
        self.ent_monto = ttk.Entry(form, width=22)
        self.ent_monto.grid(row=2, column=1, padx=6, pady=3)

        # Estado
        tk.Label(form, text="Estado:", bg="white").grid(row=3, column=0, sticky="e", padx=6, pady=3)
        self.cmb_estado = ttk.Combobox(form, values=["pendiente", "emitida", "pagada", "vencida"],
                                       state="readonly", width=20)
        self.cmb_estado.grid(row=3, column=1, padx=6, pady=3)
        self.cmb_estado.set("pendiente")

        # Fecha
        tk.Label(form, text="Fecha:", bg="white").grid(row=4, column=0, sticky="e", padx=6, pady=3)
        self.ent_fecha = ttk.Entry(form, width=22)
        self.ent_fecha.grid(row=4, column=1, padx=6, pady=3)
        self.ent_fecha.insert(0, date.today().isoformat())

        # Campos extendidos
        if self._extended:
            tk.Label(form, text="Tipo doc:", bg="white").grid(row=0, column=2, sticky="e", padx=6, pady=3)
            self.cmb_doc = ttk.Combobox(form, values=DOC_TIPOS, state="readonly", width=22)
            self.cmb_doc.grid(row=0, column=3, padx=6, pady=3)
            self.cmb_doc.set(DOC_TIPOS[0])

            tk.Label(form, text="Vencimiento:", bg="white").grid(row=1, column=2, sticky="e", padx=6, pady=3)
            self.ent_venc = ttk.Entry(form, width=22)
            self.ent_venc.grid(row=1, column=3, padx=6, pady=3)
            self.ent_venc.insert(0, self._default_venc(self.ent_fecha.get()))

        # Botones
        toolbar = tk.Frame(self, bg="white")
        toolbar.pack(pady=6)
        ttk.Button(toolbar, text="➕ Agregar", command=self.agregar_cta, width=12).pack(side="left", padx=4)
        ttk.Button(toolbar, text="✏️ Editar", command=self.editar_cta, width=12).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🗑️ Eliminar", command=self.eliminar_cta, width=12).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄 Refrescar", command=self.cargar_ctas, width=12).pack(side="left", padx=4)

        # Filtro
        tk.Label(toolbar, text="Estado:", bg="white").pack(side="left", padx=(16, 6))
        self.cmb_filtro = ttk.Combobox(toolbar, textvariable=self.var_estado_filtro,
                                       values=["todos", "pendiente", "emitida", "pagada", "vencida"],
                                       width=14, state="readonly")
        self.cmb_filtro.pack(side="left")
        self.cmb_filtro.bind("<<ComboboxSelected>>", lambda e: self.cargar_ctas())

        # Tabla + scroll
        self.table_box = tk.Frame(self, bg="white")
        self.table_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.columns_legacy = ("ID", "Número", "Proveedor", "Monto", "Estado", "Fecha")
        self.columns_extended = ("ID", "Número", "Proveedor", "DocTipo", "Neto", "IVA", "Retención",
                                 "Total", "Estado", "Fecha", "Vencimiento")
        self._build_tree(self.columns_extended if self._extended else self.columns_legacy)

    def _build_tree(self, columns: tuple[str, ...]):
        for w in self.table_box.winfo_children():
            w.destroy()

        self.tree = ttk.Treeview(self.table_box, columns=columns, show="headings")
        for c in columns:
            self.tree.heading(c, text=c)
            anchor, width = "center", 110
            if c in ("Número", "Proveedor"):
                anchor, width = "w", 180
            if c in ("Neto", "IVA", "Retención", "Total", "Monto"):
                anchor, width = "e", 120
            self.tree.column(c, anchor=anchor, width=width)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        yscroll = ttk.Scrollbar(self.table_box, orient="vertical", command=self.tree.yview)
        yscroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(fill="both", expand=True)

    # ---------------- CRUD ----------------

    def _leer_form(self):
        numero = self.ent_numero.get().strip()
        proveedor = self.ent_proveedor.get().strip()
        monto = float(self.ent_monto.get() or 0)
        estado = self.cmb_estado.get().strip()
        fecha = self.ent_fecha.get().strip()

        if not numero or not proveedor:
            raise ValueError("Debes ingresar Número y Proveedor.")
        if monto < 0:
            raise ValueError("El monto debe ser ≥ 0.")

        data = {"numero": numero, "proveedor": proveedor, "monto": monto, "estado": estado, "fecha": fecha}

        if self._extended:
            doc_tipo = (self.cmb_doc.get().strip() if hasattr(self, "cmb_doc") else None) or None
            venc = (self.ent_venc.get().strip() if hasattr(self, "ent_venc") else None) or None
            data["doc_tipo"] = doc_tipo
            data["vencimiento"] = venc
        return data

    def agregar_cta(self):
        try:
            d = self._leer_form()
            if self._extended and Factura is not None:
                # Guardamos total=monto y también en 'monto' legacy para compatibilidad
                Factura.crear_extendida(
                    numero=d["numero"],
                    tercero=d["proveedor"],
                    doc_tipo=d.get("doc_tipo"),
                    neto=float(d["monto"]),     # si quieres desglose real, usa tu service de impuestos
                    iva=0.0,
                    retencion=0.0,
                    total=float(d["monto"]),
                    tipo="proveedor",
                    fecha=d["fecha"],
                    vencimiento=d.get("vencimiento"),
                    estado=d["estado"],
                )
            else:
                Finanzas.registrar_factura(
                    d["numero"], d["proveedor"], float(d["monto"]), d["estado"], d["fecha"], "proveedor"
                )

            messagebox.showinfo("✅ Éxito", "Cuenta registrada.")
            self._limpiar_form()
            self.cargar_ctas()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def editar_cta(self):
        if not self.cta_sel_id:
            return messagebox.showwarning("Atención", "Selecciona una cuenta.")
        try:
            d = self._leer_form()
            # En este ejemplo reusamos Finanzas.editar_factura (compatibilidad).
            # Si quieres edición 100% extendida, implementa Factura.editar_extendida() en el modelo.
            Finanzas.editar_factura(
                self.cta_sel_id,
                d["numero"],
                d["proveedor"],
                float(d["monto"]),
                d["estado"],
                d["fecha"],
                "proveedor",
            )
            # Asegurar estado si hay extendido
            if self._extended and Factura is not None:
                try:
                    Factura.cambiar_estado(self.cta_sel_id, d["estado"])
                except Exception:
                    pass

            messagebox.showinfo("✏️ Editado", "Cuenta actualizada.")
            self._limpiar_form()
            self.cargar_ctas()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def eliminar_cta(self):
        if not self.cta_sel_id:
            return messagebox.showwarning("Atención", "Selecciona una cuenta.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar la cuenta seleccionada?"):
            return
        try:
            Finanzas.eliminar_factura(self.cta_sel_id)
            messagebox.showinfo("🗑️ Eliminado", "Cuenta eliminada.")
            self._limpiar_form()
            self.cargar_ctas()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    # ---------------- Tabla ----------------

    def _on_select(self, _evt):
        sel = self.tree.selection()
        if not sel:
            self.cta_sel_id = None
            return
        vals = self.tree.item(sel[0])["values"]
        self.cta_sel_id = vals[0]

        if self._extended and len(vals) >= 11:
            # (ID, Número, Proveedor, DocTipo, Neto, IVA, Retención, Total, Estado, Fecha, Vencimiento)
            _, numero, proveedor, doc_tipo, neto, iva, ret, total, estado, fecha, venc = vals
            self.ent_numero.delete(0, tk.END);     self.ent_numero.insert(0, numero)
            self.ent_proveedor.delete(0, tk.END);  self.ent_proveedor.insert(0, proveedor)
            self.ent_monto.delete(0, tk.END);      self.ent_monto.insert(0, str(total).replace(",", "").replace("$", ""))
            self.cmb_estado.set(estado)
            self.ent_fecha.delete(0, tk.END);      self.ent_fecha.insert(0, fecha)
            if hasattr(self, "cmb_doc"): self.cmb_doc.set(str(doc_tipo or ""))
            if hasattr(self, "ent_venc") and venc:
                self.ent_venc.delete(0, tk.END);   self.ent_venc.insert(0, venc)
        else:
            # Legacy: (ID, Número, Proveedor, Monto, Estado, Fecha)
            _, numero, proveedor, monto, estado, fecha = vals
            self.ent_numero.delete(0, tk.END);     self.ent_numero.insert(0, numero)
            self.ent_proveedor.delete(0, tk.END);  self.ent_proveedor.insert(0, proveedor)
            self.ent_monto.delete(0, tk.END);      self.ent_monto.insert(0, str(monto).replace(",", "").replace("$", ""))
            self.cmb_estado.set(estado)
            self.ent_fecha.delete(0, tk.END);      self.ent_fecha.insert(0, fecha)

    def cargar_ctas(self):
        try:
            for r in self.tree.get_children():
                self.tree.delete(r)

            facturas = Finanzas.listar_facturas()  # (id, numero, proveedor, monto, estado, fecha, tipo)
            facturas = [f for f in facturas if (f[6] or "").strip().lower() == "proveedor"]

            estado = self.var_estado_filtro.get().lower().strip()
            if estado != "todos":
                facturas = [f for f in facturas if (f[4] or "").strip().lower() == estado]

            if self._extended and Factura is not None:
                ids = [f[0] for f in facturas]
                extendidas = {}
                for idf in ids:
                    try:
                        row = Factura.obtener_por_id(int(idf))
                        # row extendido: (id, numero, proveedor, monto, estado, fecha, tipo, doc_tipo, neto, iva, retencion, total, vencimiento)
                        if row and len(row) >= 13:
                            extendidas[idf] = row
                    except Exception:
                        pass

                if extendidas:
                    if tuple(self.tree["columns"]) != self.columns_extended:
                        self._build_tree(self.columns_extended)

                    for f in facturas:
                        base = extendidas.get(f[0])
                        if base:
                            (_, numero, proveedor, _monto_legacy, estado, fecha, _tipo,
                             doc_tipo, neto, iva, ret, total, venc) = base
                            self.tree.insert(
                                "",
                                tk.END,
                                values=(
                                    f[0],
                                    numero or "",
                                    proveedor or "",
                                    doc_tipo or "",
                                    self._fmt_money(neto),
                                    self._fmt_money(iva),
                                    self._fmt_money(ret),
                                    self._fmt_money(total),
                                    estado or "",
                                    fecha or "",
                                    venc or "",
                                ),
                            )
                        else:
                            if tuple(self.tree["columns"]) != self.columns_legacy:
                                self._build_tree(self.columns_legacy)
                            self.tree.insert(
                                "",
                                tk.END,
                                values=(f[0], f[1], f[2], self._fmt_money(f[3]), f[4], f[5]),
                            )
                else:
                    if tuple(self.tree["columns"]) != self.columns_legacy:
                        self._build_tree(self.columns_legacy)
                    for f in facturas:
                        self.tree.insert("", tk.END, values=(f[0], f[1], f[2], self._fmt_money(f[3]), f[4], f[5]))
            else:
                if tuple(self.tree["columns"]) != self.columns_legacy:
                    self._build_tree(self.columns_legacy)
                for f in facturas:
                    self.tree.insert("", tk.END, values=(f[0], f[1], f[2], self._fmt_money(f[3]), f[4], f[5]))

        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar las CxP.\n\n{e}")

    # ---------------- Aux ----------------

    def _limpiar_form(self):
        self.cta_sel_id = None
        self.ent_numero.delete(0, tk.END)
        self.ent_proveedor.delete(0, tk.END)
        self.ent_monto.delete(0, tk.END)
        self.cmb_estado.set("pendiente")
        self.ent_fecha.delete(0, tk.END); self.ent_fecha.insert(0, date.today().isoformat())
        if self._extended and hasattr(self, "ent_venc"):
            self.ent_venc.delete(0, tk.END); self.ent_venc.insert(0, self._default_venc(self.ent_fecha.get()))
        if self._extended and hasattr(self, "cmb_doc"):
            self.cmb_doc.set(DOC_TIPOS[0])
