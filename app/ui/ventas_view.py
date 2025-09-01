# app/ui/ventas_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from app.models.venta import Venta
from app.models.cliente import Cliente
from app.models.producto import Producto
from app.config.tipos import DocTipo

# Intentamos importar el servicio; si no viene inyectado, usamos el módulo
try:
    from app.services import documentos_service as ds_mod
except Exception:
    ds_mod = None


class VentasView(tk.Frame):
    """
    Vista de Ventas con:
    - Selector de Tipo de Documento (Factura/Boleta/Exenta/Honorarios)
    - Cálculo automático de Neto/IVA/Retención/TOTAL (sin input de IVA manual)
    - Compatibilidad con modelos antiguos (usa iva% si no existe API extendida)
    """

    DOC_OPCIONES = [
        DocTipo.FACTURA.value,
        DocTipo.FACTURA_EXENTA.value,
        DocTipo.BOLETA.value,
        DocTipo.BOLETA_EXENTA.value,
        DocTipo.BOLETA_HONORARIOS.value,
    ]

    def __init__(self, parent, servicios: Dict[str, Any] | None = None):
        super().__init__(parent, bg="white")
        self.parent = parent
        self.servicios = servicios or {}
        self.ds = self.servicios.get("documentos_service") or ds_mod  # módulo o instancia

        # Vars de totales (solo lectura en UI)
        self.var_neto = tk.StringVar(value="0.00")
        self.var_iva = tk.StringVar(value="0.00")
        self.var_ret = tk.StringVar(value="0.00")
        self.var_total = tk.StringVar(value="0.00")

        self.crear_widgets()
        self.cargar_comboboxes()
        self.cargar_tabla()
        self._recalcular()

    # ---------------- UI ----------------

    def crear_widgets(self):
        tk.Label(self, text="Órdenes de Venta", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10, fill="x")

        # Tipo de Documento
        tk.Label(form, text="Tipo Doc:", bg="white").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cmb_doc = ttk.Combobox(form, width=28, state="readonly", values=self.DOC_OPCIONES)
        self.cmb_doc.current(0)  # FACTURA por defecto
        self.cmb_doc.grid(row=0, column=1, padx=5, pady=5)
        self.cmb_doc.bind("<<ComboboxSelected>>", lambda e: self._recalcular())

        # Cliente
        tk.Label(form, text="Cliente:", bg="white").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cliente_cb = ttk.Combobox(form, width=30, state="readonly")
        self.cliente_cb.grid(row=1, column=1, padx=5, pady=5)

        # Producto
        tk.Label(form, text="Producto:", bg="white").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.producto_cb = ttk.Combobox(form, width=30, state="readonly")
        self.producto_cb.grid(row=2, column=1, padx=5, pady=5)
        self.producto_cb.bind("<<ComboboxSelected>>", self.mostrar_ultima_venta)

        # Cantidad
        tk.Label(form, text="Cantidad:", bg="white").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(form, width=30)
        self.entry_cantidad.insert(0, "1")
        self.entry_cantidad.grid(row=3, column=1, padx=5, pady=5)
        self.entry_cantidad.bind("<KeyRelease>", lambda e: self._recalcular())

        # Precio Unitario (NETO)
        tk.Label(form, text="Precio Unitario (NETO):", bg="white").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_precio_unitario = ttk.Entry(form, width=30)
        self.entry_precio_unitario.insert(0, "0")
        self.entry_precio_unitario.grid(row=4, column=1, padx=5, pady=5)
        self.entry_precio_unitario.bind("<KeyRelease>", lambda e: self._recalcular())

        # --- Totales automáticos (solo lectura) ---
        tot_frame = tk.LabelFrame(self, text="Totales", bg="white")
        tot_frame.pack(padx=10, pady=5, fill="x")

        r = 0
        tk.Label(tot_frame, text="Neto:", bg="white").grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_neto, bg="white").grid(row=r, column=1, sticky="e", padx=6, pady=3); r += 1

        tk.Label(tot_frame, text="IVA:", bg="white").grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_iva, bg="white").grid(row=r, column=1, sticky="e", padx=6, pady=3); r += 1

        tk.Label(tot_frame, text="Retención:", bg="white").grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_ret, bg="white").grid(row=r, column=1, sticky="e", padx=6, pady=3); r += 1

        tk.Label(tot_frame, text="TOTAL:", bg="white", font=("Arial", 10, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
        tk.Label(tot_frame, textvariable=self.var_total, bg="white", font=("Arial", 10, "bold")).grid(row=r, column=1, sticky="e", padx=6, pady=3)

        # Información de última venta
        self.info_venta = tk.Label(self, text="", bg="white", fg="gray")
        self.info_venta.pack(pady=(2, 0))

        # Botones
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Registrar Venta", command=self.registrar_venta, width=18).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recargar", command=self.cargar_tabla, width=10).pack(side="left", padx=5)

        # Tabla de ventas (se ajusta dinámicamente según columnas disponibles)
        self.tabla_frame = tk.Frame(self, bg="white")
        self.tabla_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._build_tree(columns=("id", "cliente", "producto", "cantidad", "precio_unitario", "iva", "total", "fecha"))

    def _build_tree(self, columns: tuple[str, ...]):
        # Destruye y crea de nuevo el Treeview con columnas dadas
        for w in self.tabla_frame.winfo_children():
            w.destroy()
        self.tabla = ttk.Treeview(self.tabla_frame, columns=columns, show="headings")
        for col in columns:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=110, anchor="center")
        self.tabla.pack(fill="both", expand=True)

    # ------------- Datos -------------

    def cargar_comboboxes(self):
        # Poblar comboboxes con datos actuales
        try:
            clientes = [c[1] for c in Cliente.listar_todos()]
        except Exception:
            clientes = []
        try:
            productos = [p[1] for p in Producto.listar_todos()]
        except Exception:
            productos = []
        self.cliente_cb["values"] = clientes
        self.producto_cb["values"] = productos

    def cargar_tabla(self):
        # Refrescar tabla con todas las ventas; intenta detectar columnas extendidas
        if hasattr(self, "tabla"):
            for row in self.tabla.get_children():
                self.tabla.delete(row)

        ventas = list(Venta.listar_todas())
        if not ventas:
            return

        # Detección de columnas por longitud de tupla
        # Legacy:   (id, cliente, producto, cantidad, precio_unitario, iva, total, fecha) -> 8
        # Extendido:(id, cliente, producto, cantidad, precio_unitario, doc_tipo, neto, iva, retencion, total, fecha) -> 11
        cols = ("id", "cliente", "producto", "cantidad", "precio_unitario", "iva", "total", "fecha")
        if len(ventas[0]) >= 11:
            cols = (
                "id", "cliente", "producto", "cantidad", "precio_unitario",
                "doc_tipo", "neto", "iva", "retencion", "total", "fecha"
            )

        self._build_tree(columns=cols)

        for v in ventas:
            self.tabla.insert("", tk.END, values=v)

    # ------------- UX -------------

    def mostrar_ultima_venta(self, event=None):
        producto = self.producto_cb.get()
        if not producto:
            self.info_venta.config(text="")
            return

        venta = Venta.ultima_venta_producto(producto)
        if not venta:
            self.info_venta.config(text="Sin ventas anteriores registradas.")
            return

        # Legacy (8 cols): (..., iva[5], total[6], fecha[7])
        # Extendido (11 cols): (..., doc_tipo[5], neto[6], iva[7], ret[8], total[9], fecha[10])
        if len(venta) >= 11:
            total = venta[9]
            fecha = venta[10]
        elif len(venta) >= 8:
            total = venta[6]
            fecha = venta[7]
        else:
            total = ""
            fecha = ""

        # (Opcional) precargar el precio unitario de la última venta
        try:
            precio_unitario = venta[4]
            self.entry_precio_unitario.delete(0, tk.END)
            self.entry_precio_unitario.insert(0, str(precio_unitario))
            self._recalcular()
        except Exception:
            pass

        self.info_venta.config(text=f"🕒 Última venta de {producto}: {fecha} (Total: ${total})")

    # ------------- Lógica -------------

    def _recalcular(self):
        try:
            doc_tipo = DocTipo(self.cmb_doc.get())
            cantidad = int(self.entry_cantidad.get() or "0")
            precio_neto = float(self.entry_precio_unitario.get() or "0")
            neto_total = max(0.0, cantidad * precio_neto)

            tot = self._calcular_totales(doc_tipo, neto_total)

            self.var_neto.set(f"{tot['neto']:.2f}")
            self.var_iva.set(f"{tot['iva']:.2f}")
            self.var_ret.set(f"{tot['retencion']:.2f}")
            self.var_total.set(f"{tot['total']:.2f}")
        except Exception:
            # No rompas la UI si hay tipeos mientras el usuario escribe
            pass

    def _calcular_totales(self, doc_tipo: DocTipo, neto_total: float) -> dict:
        """
        Usa el servicio inyectado (o módulo) para calcular totales desde NETO.
        """
        if hasattr(self.ds, "calcular_totales_desde_neto"):
            return self.ds.calcular_totales_desde_neto(doc_tipo, neto_total)
        # Fallback mínimo si no hay servicio disponible
        if doc_tipo in (DocTipo.FACTURA, DocTipo.BOLETA):
            iva = round(neto_total * 0.19, 2)
            return {"neto": neto_total, "iva": iva, "retencion": 0.0, "total": round(neto_total + iva, 2)}
        if doc_tipo in (DocTipo.FACTURA_EXENTA, DocTipo.BOLETA_EXENTA):
            return {"neto": neto_total, "iva": 0.0, "retencion": 0.0, "total": neto_total}
        if doc_tipo == DocTipo.BOLETA_HONORARIOS:
            ret = round(neto_total * 0.1075, 2)
            return {"neto": neto_total, "iva": 0.0, "retencion": ret, "total": round(neto_total - ret, 2)}
        raise ValueError("Tipo de documento no soportado.")

    def registrar_venta(self):
        try:
            cliente = self.cliente_cb.get().strip()
            producto = self.producto_cb.get().strip()
            cantidad = int(self.entry_cantidad.get())
            precio_neto = float(self.entry_precio_unitario.get())
            if not cliente or not producto:
                raise ValueError("Debe seleccionar cliente y producto.")
            if cantidad <= 0 or precio_neto < 0:
                raise ValueError("Cantidad y precio deben ser válidos.")

            doc_tipo = DocTipo(self.cmb_doc.get())
            neto_total = cantidad * precio_neto
            tot = self._calcular_totales(doc_tipo, neto_total)

            # --- Intento 1: API extendida (recomendada) -----------------
            # Esperada: registrar_extendido(cliente, producto, cantidad, precio_unitario_neto, doc_tipo, neto, iva, retencion, total)
            if hasattr(Venta, "registrar_extendido"):
                Venta.registrar_extendido(
                    cliente=cliente,
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
                # --- Intento 2: método antiguo (compatibilidad) ----------
                # El método antiguo esperaba IVA en PORCENTAJE (ej: 19), no en monto.
                iva_percent = 0.0
                if tot["neto"] > 0 and tot["iva"] > 0:
                    iva_percent = round((tot["iva"] / tot["neto"]) * 100.0, 2)
                Venta.registrar(cliente, producto, cantidad, precio_neto, iva_percent)

            messagebox.showinfo("✅ Éxito", "Venta registrada correctamente.")

            # Limpiar campos
            self.cliente_cb.set("")
            self.producto_cb.set("")
            self.entry_cantidad.delete(0, tk.END); self.entry_cantidad.insert(0, "1")
            self.entry_precio_unitario.delete(0, tk.END); self.entry_precio_unitario.insert(0, "0")
            self.info_venta.config(text="")
            self._recalcular()

            # Refrescar datos
            self.cargar_comboboxes()
            self.cargar_tabla()

        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo registrar la venta:\n{e}")
