# app/ui/ctas_por_cobrar_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from app.models.finanzas import Finanzas

# Opcional (schema extendido): usar Factura si está disponible
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


DEFAULT_PAYMENT_DAYS = 30  # fallback si no tienes constantes centralizadas


class CtasPorCobrarView(tk.Frame):
    """
    - Soporta schema extendido (doc_tipo, neto, iva, retencion, total, vencimiento) si existe.
    - Fallback a Finanzas.* (legacy) si no existe el extendido.
    - No llama pack()/grid() en __init__ (lo hace MainWindow).
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
        """
        True si existe el modelo Factura y su schema extendido está habilitado.
        """
        try:
            if Factura is None:
                return False
            return bool(Factura._extended_enabled())  # método del modelo Factura
        except Exception:
            return False

    def _fmt_money(self, x) -> str:
        try:
            val = float(x or 0)
        except Exception:
            val = 0.0
        # Cambia a :,.0f si trabajas sin decimales
        return f"${val:,.2f}"

    def _default_venc(self, iso: str) -> str:
        try:
            y, m, d = map(int, iso.split("-"))
            return (date(y, m, d) + timedelta(days=DEFAULT_PAYMENT_DAYS)).isoformat()
        except Exception:
            return iso

    # ---------------- UI ----------------

    def _build_ui(self):
        tk.Label(self, text="📋 Cuentas por Cobrar", font=("Segoe UI", 16, "bold"), bg="white").pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(padx=10, pady=6, anchor="w")

        # Número doc
        tk.Label(form, text="Número:", bg="white").grid(row=0, column=0, sticky="e", padx=6, pady=3)
        self.ent_numero = ttk.Entry(form, width=22)
        self.ent_numero.grid(row=0, column=1, padx=6, pady=3)

        # Cliente
        tk.Label(form, text="Cliente:", bg="white").grid(row=1, column=0, sticky="e", padx=6, pady=3)
        self.ent_cliente = ttk.Entry(form, width=22)
        self.ent_cliente.grid(row=1, column=1, padx=6, pady=3)

        # Monto (en legacy será el total; en extendido puedes dejarlo como total también)
        tk.Label(form, text="Monto (total):", bg="white").grid(row=2, column=0, sticky="e", padx=6, pady=3)
        self.ent_monto = ttk.Entry(form, width=22)
        self.ent_monto.grid(row=2, column=1, padx=6, pady=3)

        # Estado
        tk.Label(form, text="Estado:", bg="white").grid(row=3, column=0, sticky="e", padx=6, pady=3)
        self.cmb_estado = ttk.Combobox(form, values=["pendiente", "emitida", "pagada", "vencida"], state="readonly", width=20)
        self.cmb_estado.grid(row=3, column=1, padx=6, pady=3)
        self.cmb_estado.set("pendiente")

        # Fecha
        tk.Label(form, text="Fecha:", bg="white").grid(row=4, column=0, sticky="e", padx=6, pady=3)
        self.ent_fecha = ttk.Entry(form, width=22)
        self.ent_fecha.grid(row=4, column=1, padx=6, pady=3)
        self.ent_fecha.insert(0, date.today().isoformat())

        # Solo para extendido: doc_tipo + vencimiento
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

        # Filtro por estado
        tk.Label(toolbar, text="Estado:", bg="white").pack(side="left", padx=(16, 6))
        self.cmb_filtro = ttk.Combobox(toolbar, textvariable=self.var_estado_filtro, values=["todos", "pendiente", "emitida", "pagada", "vencida"], width=14, state="readonly")
        self.cmb_filtro.pack(side="left")
        self.cmb_filtro.bind("<<ComboboxSelected>>", lambda e: self.cargar_ctas())

        # Tabla + scroll
        self.table_box = tk.Frame(self, bg="white")
        self.table_box.pack(fill="both", expand=True, padx=10, pady=10)

        # columnas por defecto (legacy)
        self.columns_legacy = ("ID", "Número", "Cliente", "Monto", "Estado", "Fecha")
        # columnas extendidas
        self.columns_extended = ("ID", "Número", "Cliente", "DocTipo", "Neto", "IVA", "Retención", "Total", "Estado", "Fecha", "Vencimiento")

        self._build_tree(self.columns_extended if self._extended else self.columns_legacy)

    def _build_tree(self, columns: tuple[str, ...]):
        # limpiar contenedor
        for w in self.table_box.winfo_children():
            w.destroy()

        self.tree = ttk.Treeview(self.table_box, columns=columns, show="headings")
        for c in columns:
            self.tree.heading(c, text=c)
            anchor = "center"
            width = 110
            if c in ("Número", "Cliente"):
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
        cliente = self.ent_cliente.get().strip()
        monto = float(self.ent_monto.get() or 0)
        estado = self.cmb_estado.get().strip()
        fecha = self.ent_fecha.get().strip()

        if not numero or not cliente:
            raise ValueError("Debes ingresar Número y Cliente.")
        if monto < 0:
            raise ValueError("El monto debe ser ≥ 0.")

        data = {"numero": numero, "cliente": cliente, "monto": monto, "estado": estado, "fecha": fecha}

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
                # En extendido: guardamos total en "total" y también en "monto" (compat)
                Factura.crear_extendida(
                    numero=d["numero"],
                    tercero=d["cliente"],
                    doc_tipo=d.get("doc_tipo"),
                    neto=float(d["monto"]),         # si quieres desglose real, cámbialo por servicio de impuestos
                    iva=0.0,
                    retencion=0.0,
                    total=float(d["monto"]),
                    tipo="cliente",
                    fecha=d["fecha"],
                    vencimiento=d.get("vencimiento"),
                    estado=d["estado"],
                )
            else:
                # Legacy: usa el servicio Finanzas
                Finanzas.registrar_factura(d["numero"], d["cliente"], float(d["monto"]), d["estado"], d["fecha"], "cliente")

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
            if self._extended and Factura is not None:
                # El modelo Factura no tiene editar extendida; al menos cambiamos estado y campos legacy compatibles
                # Para edición completa, podrías implementar Factura.editar_extendida similar a Compras/Ventas.
                Finanzas.editar_factura(
                    self.cta_sel_id,
                    d["numero"],
                    d["cliente"],
                    float(d["monto"]),
                    d["estado"],
                    d["fecha"],
                    "cliente",
                )
                # Además si quieres cambiar solo el estado de forma segura:
                try:
                    Factura.cambiar_estado(self.cta_sel_id, d["estado"])
                except Exception:
                    pass
            else:
                Finanzas.editar_factura(
                    self.cta_sel_id,
                    d["numero"],
                    d["cliente"],
                    float(d["monto"]),
                    d["estado"],
                    d["fecha"],
                    "cliente",
                )

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

        # Mapear según columnas activas
        if self._extended and len(vals) >= 11:
            # (ID, Número, Cliente, DocTipo, Neto, IVA, Retención, Total, Estado, Fecha, Vencimiento)
            _, numero, cliente, doc_tipo, neto, iva, ret, total, estado, fecha, venc = vals
            self.ent_numero.delete(0, tk.END);  self.ent_numero.insert(0, numero)
            self.ent_cliente.delete(0, tk.END); self.ent_cliente.insert(0, cliente)
            # Por simplicidad, cargamos "monto" con Total
            self.ent_monto.delete(0, tk.END);   self.ent_monto.insert(0, str(total).replace(",", "").replace("$", ""))
            self.cmb_estado.set(estado)
            self.ent_fecha.delete(0, tk.END);   self.ent_fecha.insert(0, fecha)
            if hasattr(self, "cmb_doc"): self.cmb_doc.set(str(doc_tipo or ""))
            if hasattr(self, "ent_venc") and venc: 
                self.ent_venc.delete(0, tk.END); self.ent_venc.insert(0, venc)
        else:
            # Legacy: (ID, Número, Cliente, Monto, Estado, Fecha)
            _, numero, cliente, monto, estado, fecha = vals
            self.ent_numero.delete(0, tk.END);  self.ent_numero.insert(0, numero)
            self.ent_cliente.delete(0, tk.END); self.ent_cliente.insert(0, cliente)
            self.ent_monto.delete(0, tk.END);   self.ent_monto.insert(0, str(monto).replace(",", "").replace("$", ""))
            self.cmb_estado.set(estado)
            self.ent_fecha.delete(0, tk.END);   self.ent_fecha.insert(0, fecha)

    def cargar_ctas(self):
        try:
            for r in self.tree.get_children():
                self.tree.delete(r)

            facturas = Finanzas.listar_facturas()  # legacy: (id, numero, proveedor, monto, estado, fecha, tipo)
            # Filtra por tipo 'cliente'
            facturas = [f for f in facturas if (f[6] or "").strip().lower() == "cliente"]

            estado = self.var_estado_filtro.get().lower().strip()
            if estado != "todos":
                facturas = [f for f in facturas if (f[4] or "").strip().lower() == estado]

            if self._extended and Factura is not None:
                # Intentar leer extendido para esas mismas IDs, si existen
                ids = [f[0] for f in facturas]
                extendidas = {}
                # Leer una por una (simple y robusto)
                for idf in ids:
                    try:
                        row = Factura.obtener_por_id(int(idf))
                        # row extendido: (id, numero, proveedor, monto, estado, fecha, tipo, doc_tipo, neto, iva, retencion, total, vencimiento)
                        if row and len(row) >= 13:
                            extendidas[idf] = row
                    except Exception:
                        pass

                # Si hay extendidas, usamos las columnas extendidas
                if extendidas:
                    if tuple(self.tree["columns"]) != self.columns_extended:
                        self._build_tree(self.columns_extended)

                    for f in facturas:
                        base = extendidas.get(f[0])
                        if base:
                            (_, numero, cliente, _monto_legacy, estado, fecha, _tipo,
                             doc_tipo, neto, iva, ret, total, venc) = base
                            self.tree.insert(
                                "",
                                tk.END,
                                values=(
                                    f[0],
                                    numero or "",
                                    cliente or "",
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
                            # No hay extendida: caer a legacy en fila
                            if tuple(self.tree["columns"]) != self.columns_legacy:
                                self._build_tree(self.columns_legacy)
                            self.tree.insert(
                                "",
                                tk.END,
                                values=(f[0], f[1], f[2], self._fmt_money(f[3]), f[4], f[5]),
                            )
                else:
                    # No hay extendidas: usar legacy
                    if tuple(self.tree["columns"]) != self.columns_legacy:
                        self._build_tree(self.columns_legacy)
                    for f in facturas:
                        self.tree.insert(
                            "",
                            tk.END,
                            values=(f[0], f[1], f[2], self._fmt_money(f[3]), f[4], f[5]),
                        )
            else:
                # Legacy puro
                if tuple(self.tree["columns"]) != self.columns_legacy:
                    self._build_tree(self.columns_legacy)
                for f in facturas:
                    self.tree.insert("", tk.END, values=(f[0], f[1], f[2], self._fmt_money(f[3]), f[4], f[5]))

        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar las CxC.\n\n{e}")

    # ---------------- Aux ----------------

    def _limpiar_form(self):
        self.cta_sel_id = None
        self.ent_numero.delete(0, tk.END)
        self.ent_cliente.delete(0, tk.END)
        self.ent_monto.delete(0, tk.END)
        self.cmb_estado.set("pendiente")
        self.ent_fecha.delete(0, tk.END); self.ent_fecha.insert(0, date.today().isoformat())
        if self._extended and hasattr(self, "ent_venc"):
            self.ent_venc.delete(0, tk.END); self.ent_venc.insert(0, self._default_venc(self.ent_fecha.get()))
        if self._extended and hasattr(self, "cmb_doc"):
            self.cmb_doc.set(DOC_TIPOS[0])
