# app/ui/compras_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

from email.message import EmailMessage
import smtplib

from app.models.compra import Compra
from app.models.producto import Producto
from app.models.proveedor import Proveedor
from app.config.tipos import DocTipo  # ✅ ruta corregida

# Servicio por módulo (fallback si no viene por inyección)
try:
    from app.services import documentos_service as ds_mod
except Exception:
    ds_mod = None


class ComprasView(tk.Frame):
    """
    Órdenes de Compra con lógica chilena:
    - Tipo de documento (Factura, Exenta, Boleta, Exenta, Honorarios)
    - Cálculo automático de neto/IVA/retención/TOTAL (UI solo-lectura)
    - Crédito a 30 días (vencimiento) opcional
    - Compatibilidad con modelos antiguos (usa iva% si no hay API extendida)
    """

    DOC_OPCIONES = [
        DocTipo.FACTURA.value,
        DocTipo.FACTURA_EXENTA.value,
        DocTipo.BOLETA.value,
        DocTipo.BOLETA_EXENTA.value,
        DocTipo.BOLETA_HONORARIOS.value,
    ]

    def __init__(self, parent, servicios: Optional[Dict[str, Any]] = None):
        """
        No hace pack aquí; lo hace el contenedor.
        """
        super().__init__(parent, bg="white")
        self.servicios = servicios or {}
        self.ds = self.servicios.get("documentos_service") or ds_mod

        self.compra_seleccionada_id = None

        # Vars de totales (solo lectura)
        self.var_neto = tk.StringVar(value="0.00")
        self.var_iva = tk.StringVar(value="0.00")
        self.var_ret = tk.StringVar(value="0.00")
        self.var_total = tk.StringVar(value="0.00")

        # Crédito 30 días
        self.var_credito = tk.BooleanVar(value=True)

        self._build_ui()
        self.after(0, self.cargar_combobox)
        self.after(0, self.cargar_tabla)
        self.after(0, self._recalcular)

    # ---------------- UI ----------------

    def _build_ui(self):
        tk.Label(self, text="🛒 Órdenes de Compra", font=("Segoe UI", 16, "bold"), bg="white").pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10, fill="x")

        # Tipo Doc
        tk.Label(form, text="Tipo Doc:", bg="white").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cmb_doc = ttk.Combobox(form, width=28, state="readonly", values=self.DOC_OPCIONES)
        self.cmb_doc.current(0)  # FACTURA
        self.cmb_doc.grid(row=0, column=1, padx=5, pady=5)
        self.cmb_doc.bind("<<ComboboxSelected>>", lambda e: self._recalcular())

        # Crédito 30 días
        self.chk_credito = ttk.Checkbutton(form, text="Compra a crédito (30 días)", variable=self.var_credito)
        self.chk_credito.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # Proveedor
        tk.Label(form, text="Proveedor:", bg="white").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cmb_proveedor = ttk.Combobox(form, width=30, state="readonly")
        self.cmb_proveedor.grid(row=1, column=1, padx=5, pady=5)

        # Producto
        tk.Label(form, text="Producto:", bg="white").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.cmb_producto = ttk.Combobox(form, width=30, state="readonly")
        self.cmb_producto.grid(row=2, column=1, padx=5, pady=5)

        # Cantidad
        tk.Label(form, text="Cantidad:", bg="white").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(form, width=30)
        self.entry_cantidad.insert(0, "1")
        self.entry_cantidad.grid(row=3, column=1, padx=5, pady=5)
        self.entry_cantidad.bind("<KeyRelease>", lambda e: self._recalcular())

        # Precio Unitario (NETO por defecto)
        tk.Label(form, text="Precio Unitario (NETO):", bg="white").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_precio = ttk.Entry(form, width=30)
        self.entry_precio.insert(0, "0")
        self.entry_precio.grid(row=4, column=1, padx=5, pady=5)
        self.entry_precio.bind("<KeyRelease>", lambda e: self._recalcular())

        # Totales (solo lectura)
        tot_frame = tk.LabelFrame(self, text="Totales", bg="white")
        tot_frame.pack(padx=10, pady=5, fill="x")

        r = 0
        tk.Label(tot_frame, text="Neto:", bg="white").grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_neto, bg="white").grid(row=r, column=1, sticky="e", padx=6, pady=3); r += 1

        tk.Label(tot_frame, text="IVA:", bg="white").grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_iva, bg="white").grid(row=r, column=1, sticky="e", padx=6, pady=3); r += 1

        tk.Label(tot_frame, text="Retención:", bg="white").grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_ret, bg="white").grid(row=r, column=1, sticky="e", padx=6, pady=3); r += 1

        tk.Label(tot_frame, text="TOTAL a pagar:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_total, bg="white", font=("Segoe UI", 10, "bold")).grid(row=r, column=1, sticky="e", padx=6, pady=3)

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Registrar", command=self.registrar_compra, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.editar_compra, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.eliminar_compra, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Enviar Email", command=self.enviar_por_correo, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recargar", command=self.cargar_tabla, width=12).pack(side="left", padx=5)

        # Tabla con scroll
        self.tabla_frame = tk.Frame(self, bg="white")
        self.tabla_frame.pack(pady=10, fill="both", expand=True)
        self._build_tree(("id", "proveedor", "producto", "cantidad", "precio_unitario", "iva", "total", "fecha"))

    def _build_tree(self, columns: tuple[str, ...]):
        for w in self.tabla_frame.winfo_children():
            w.destroy()
        self.tabla = ttk.Treeview(self.tabla_frame, columns=columns, show="headings")
        for col in columns:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=110, anchor="center")
        # Scrollbars
        yscroll = ttk.Scrollbar(self.tabla_frame, orient="vertical", command=self.tabla.yview)
        yscroll.pack(side="right", fill="y")
        self.tabla.configure(yscrollcommand=yscroll.set)

        self.tabla.bind("<<TreeviewSelect>>", self._seleccionar_fila)
        self.tabla.pack(fill="both", expand=True)

    # ------------- Datos -------------

    def cargar_combobox(self):
        try:
            # Producto.listar_todos() y Proveedor.listar_todos() → SELECT *; nombre está en idx 1
            self.cmb_proveedor["values"] = [p[1] for p in Proveedor.listar_todos()]
            self.cmb_producto["values"] = [p[1] for p in Producto.listar_todos()]
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar listas.\n\n{e}")

    def cargar_tabla(self):
        try:
            for row in self.tabla.get_children():
                self.tabla.delete(row)

            compras = list(Compra.listar_todas())
            if not compras:
                return

            # Detecta columnas extendidas vs legacy por longitud de tupla
            # extendido: (id, proveedor, producto, cantidad, precio_unitario, doc_tipo, neto, iva, retencion, total, fecha, vencimiento)
            cols = ("id", "proveedor", "producto", "cantidad", "precio_unitario", "iva", "total", "fecha")
            if len(compras[0]) >= 12:
                cols = ("id", "proveedor", "producto", "cantidad", "precio_unitario",
                        "doc_tipo", "neto", "iva", "retencion", "total", "fecha", "vencimiento")

            self._build_tree(cols)
            for c in compras:
                self.tabla.insert("", tk.END, values=c)
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudieron cargar compras.\n\n{e}")

    # ------------- Lógica -------------

    def _parse_int(self, s: str, default: int = 0) -> int:
        try:
            return int(str(s).strip())
        except Exception:
            return default

    def _parse_float(self, s: str, default: float = 0.0) -> float:
        try:
            return float(str(s).strip().replace(",", "."))
        except Exception:
            return default

    def _calcular_totales(self, doc_tipo: DocTipo, neto_total: float) -> dict:
        # Usa servicio inyectado si existe
        if self.ds and hasattr(self.ds, "calcular_totales_desde_neto"):
            return self.ds.calcular_totales_desde_neto(doc_tipo, neto_total)

        # Fallback mínimo
        if doc_tipo in (DocTipo.FACTURA, DocTipo.BOLETA):
            iva = round(neto_total * 0.19, 2)
            return {"neto": round(neto_total, 2), "iva": iva, "retencion": 0.0, "total": round(neto_total + iva, 2)}
        if doc_tipo in (DocTipo.FACTURA_EXENTA, DocTipo.BOLETA_EXENTA):
            return {"neto": round(neto_total, 2), "iva": 0.0, "retencion": 0.0, "total": round(neto_total, 2)}
        if doc_tipo == DocTipo.BOLETA_HONORARIOS:
            ret = round(neto_total * 0.1075, 2)
            return {"neto": round(neto_total, 2), "iva": 0.0, "retencion": ret, "total": round(neto_total - ret, 2)}
        raise ValueError("Tipo de documento no soportado.")

    def _recalcular(self):
        try:
            doc_tipo = DocTipo(self.cmb_doc.get())
            cantidad = self._parse_int(self.entry_cantidad.get(), 0)
            precio_neto = self._parse_float(self.entry_precio.get(), 0.0)
            neto_total = max(0.0, cantidad * precio_neto)

            tot = self._calcular_totales(doc_tipo, neto_total)
            self.var_neto.set(f"{tot['neto']:.2f}")
            self.var_iva.set(f"{tot['iva']:.2f}")
            self.var_ret.set(f"{tot['retencion']:.2f}")
            self.var_total.set(f"{tot['total']:.2f}")
        except Exception:
            # Silencioso para no molestar mientras el usuario teclea
            pass

    # ------------- CRUD -------------

    def registrar_compra(self):
        try:
            proveedor = self.cmb_proveedor.get().strip()
            producto = self.cmb_producto.get().strip()
            cantidad = self._parse_int(self.entry_cantidad.get(), -1)
            precio_neto = self._parse_float(self.entry_precio.get(), -1.0)
            if not proveedor or not producto:
                raise ValueError("Debe seleccionar proveedor y producto.")
            if cantidad <= 0 or precio_neto < 0:
                raise ValueError("Cantidad y precio deben ser válidos.")

            doc_tipo = DocTipo(self.cmb_doc.get())
            neto_total = cantidad * precio_neto
            tot = self._calcular_totales(doc_tipo, neto_total)

            # Vencimiento si es crédito
            vencimiento_iso = None
            if self.var_credito.get() and self.ds and hasattr(self.ds, "calcular_vencimiento"):
                venc = self.ds.calcular_vencimiento()
                if hasattr(venc, "isoformat"):
                    vencimiento_iso = venc.isoformat()

            # --- Intento 1: API extendida -------------------------------
            if hasattr(Compra, "registrar_extendido"):
                Compra.registrar_extendido(
                    proveedor=proveedor,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_neto=precio_neto,
                    doc_tipo=doc_tipo.value,
                    neto=tot["neto"],
                    iva=tot["iva"],
                    retencion=tot["retencion"],
                    total=tot["total"],
                    vencimiento=vencimiento_iso,
                )
            else:
                # --- Intento 2: método antiguo (compatibilidad) ----------
                iva_percent = 0.0
                if tot["neto"] > 0 and tot["iva"] > 0:
                    iva_percent = round((tot["iva"] / tot["neto"]) * 100.0, 2)
                Compra.registrar(proveedor, producto, cantidad, precio_neto, iva_percent)

            messagebox.showinfo("✅ Éxito", "Compra registrada correctamente.")
            self._limpiar_form()
            self.cargar_combobox()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def editar_compra(self):
        if not self.compra_seleccionada_id:
            return messagebox.showwarning("Atención", "Selecciona una orden para editar.")
        try:
            proveedor = self.cmb_proveedor.get().strip()
            producto = self.cmb_producto.get().strip()
            cantidad = self._parse_int(self.entry_cantidad.get(), -1)
            precio_neto = self._parse_float(self.entry_precio.get(), -1.0)
            if not proveedor or not producto:
                raise ValueError("Debe seleccionar proveedor y producto.")
            if cantidad <= 0 or precio_neto < 0:
                raise ValueError("Cantidad y precio deben ser válidos.")

            doc_tipo = DocTipo(self.cmb_doc.get())
            neto_total = cantidad * precio_neto
            tot = self._calcular_totales(doc_tipo, neto_total)

            # API extendida si existe
            if hasattr(Compra, "editar_extendido"):
                Compra.editar_extendido(
                    id_compra=self.compra_seleccionada_id,
                    proveedor=proveedor,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario_neto=precio_neto,
                    doc_tipo=doc_tipo.value,
                    neto=tot["neto"],
                    iva=tot["iva"],
                    retencion=tot["retencion"],
                    total=tot["total"],
                )
            else:
                iva_percent = 0.0
                if tot["neto"] > 0 and tot["iva"] > 0:
                    iva_percent = round((tot["iva"] / tot["neto"]) * 100.0, 2)
                Compra.editar(self.compra_seleccionada_id, proveedor, producto, cantidad, precio_neto, iva_percent)

            messagebox.showinfo("✏️ Editado", "Orden de compra actualizada.")
            self._limpiar_form()
            self.cargar_combobox()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def eliminar_compra(self):
        if not self.compra_seleccionada_id:
            return messagebox.showwarning("Atención", "Selecciona una orden para eliminar.")
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta orden de compra?"):
            return
        try:
            Compra.eliminar(self.compra_seleccionada_id)
            messagebox.showinfo("🗑️ Eliminada", "Orden de compra eliminada.")
            self._limpiar_form()
            self.cargar_combobox()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    # ------------- Selección y Email -------------

    def _seleccionar_fila(self, _event=None):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        if not vals:
            return
        self.compra_seleccionada_id = vals[0]

        # Compatibilidad con ambos sets de columnas
        self.cmb_proveedor.set(vals[1])
        self.cmb_producto.set(vals[2])
        self.entry_cantidad.delete(0, tk.END); self.entry_cantidad.insert(0, vals[3])
        self.entry_precio.delete(0, tk.END);   self.entry_precio.insert(0, vals[4])

        # Recalcula para refrescar totales mostrados
        self._recalcular()

    def enviar_por_correo(self):
        if not self.compra_seleccionada_id:
            return messagebox.showwarning("Atención", "Selecciona una orden para enviar.")
        compra = Compra.obtener_por_id(self.compra_seleccionada_id)
        if not compra:
            return messagebox.showerror("❌ Error", "Compra no encontrada.")

        # Buscar correo del proveedor
        prov = Proveedor.buscar_por_nombre(compra[1])
        correo = None
        if prov:
            # (id, nombre, rut, direccion, telefono, razon_social, correo, comuna)
            for p in prov:
                if p[1] == compra[1]:
                    correo = p[6]
                    break
            if not correo:
                correo = prov[0][6]  # fallback primer match
        if not correo:
            return messagebox.showerror("❌ Error", "No se encontró correo del proveedor.")

        # Cuerpo del correo según estructura
        if len(compra) >= 12:
            _, proveedor, producto, cant, punit, doc_tipo, neto, iva_monto, ret, total, fecha, venc = compra
            iva_txt = f"${iva_monto:.2f}"
            ret_txt = f"${ret:.2f}"
            doc_txt = str(doc_tipo)
            venc_txt = venc or "-"
        else:
            _, proveedor, producto, cant, punit, iva_percent, total, fecha = compra
            iva_txt = f"{iva_percent:.0f}%"
            ret_txt = "-"
            doc_txt = "-"
            venc_txt = "-"

        msg = EmailMessage()
        msg["Subject"] = f"Orden de Compra #{self.compra_seleccionada_id}"
        msg["From"] = "tu_empresa@dominio.com"
        msg["To"] = correo
        cuerpo = (
            f"Orden de Compra #{self.compra_seleccionada_id}\n\n"
            f"Proveedor: {proveedor}\n"
            f"Producto: {producto}\n"
            f"Cantidad: {cant}\n"
            f"Precio Unitario: {punit}\n"
            f"Tipo Doc: {doc_txt}\n"
            f"IVA: {iva_txt}\n"
            f"Retención: {ret_txt}\n"
            f"Total: {total}\n"
            f"Fecha: {fecha}\n"
            f"Vencimiento: {venc_txt}\n"
        )
        msg.set_content(cuerpo)
        try:
            with smtplib.SMTP("localhost") as s:
                s.send_message(msg)
            messagebox.showinfo("✉️ Enviado", f"Orden enviada a {correo}")
        except Exception as e:
            messagebox.showerror("❌ Error al enviar", str(e))

    # ------------- Util -------------

    def _limpiar_form(self):
        self.compra_seleccionada_id = None
        self.cmb_proveedor.set("")
        self.cmb_producto.set("")
        self.entry_cantidad.delete(0, tk.END); self.entry_cantidad.insert(0, "1")
        self.entry_precio.delete(0, tk.END);   self.entry_precio.insert(0, "0")
        self._recalcular()
