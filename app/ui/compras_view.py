import tkinter as tk
from tkinter import ttk, messagebox
import smtplib
from email.message import EmailMessage

from app.models.compra import Compra
from app.models.producto import Producto
from app.models.proveedor import Proveedor

class ComprasView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="white")
        self.compra_seleccionada_id = None
        self.crear_widgets()
        self.cargar_combobox()
        self.cargar_tabla()

    def crear_widgets(self):
        tk.Label(self, text="Órdenes de Compra",
                 font=("Arial", 16, "bold"), bg="white")\
          .pack(pady=10)

        form = tk.Frame(self, bg="white")
        form.pack(pady=10)

        # Campos y widgets
        tk.Label(form, text="Proveedor:", bg="white")\
          .grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cmb_proveedor = ttk.Combobox(form, width=30, state="readonly")
        self.cmb_proveedor.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Producto:", bg="white")\
          .grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cmb_producto = ttk.Combobox(form, width=30, state="readonly")
        self.cmb_producto.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="Cantidad:", bg="white")\
          .grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_cantidad = ttk.Entry(form, width=30)
        self.entry_cantidad.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form, text="Precio Unitario:", bg="white")\
          .grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_precio = ttk.Entry(form, width=30)
        self.entry_precio.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(form, text="IVA (%):", bg="white")\
          .grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_iva = ttk.Entry(form, width=30)
        self.entry_iva.grid(row=4, column=1, padx=5, pady=5)

        # Botones de acción
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Registrar", command=self.registrar_compra, width=12)\
           .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.editar_compra, width=12)\
           .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.eliminar_compra, width=12)\
           .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Enviar Email", command=self.enviar_por_correo, width=12)\
           .pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recargar", command=self.cargar_tabla, width=12)\
           .pack(side="left", padx=5)

        # Tabla de órdenes
        cols = ("id", "proveedor", "producto", "cantidad",
                "precio_unitario", "iva", "total", "fecha")
        self.tabla = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tabla.heading(col, text=col.replace("_", " ").capitalize())
            self.tabla.column(col, width=100, anchor="center")
        self.tabla.bind("<<TreeviewSelect>>", self._seleccionar_fila)
        self.tabla.pack(pady=10, fill="both", expand=True)

    def cargar_combobox(self):
        """Refresca los Combobox con todos los proveedores y productos."""
        self.cmb_proveedor['values'] = [p[1] for p in Proveedor.listar_todos()]
        self.cmb_producto['values']  = [p[1] for p in Producto.listar_todos()]

    def cargar_tabla(self):
        """Refresca la tabla con todas las órdenes de compra."""
        for row in self.tabla.get_children():
            self.tabla.delete(row)
        for c in Compra.listar_todas():
            self.tabla.insert("", tk.END, values=c)

    def registrar_compra(self):
        try:
            datos = {
                "proveedor":       self.cmb_proveedor.get(),
                "producto":        self.cmb_producto.get(),
                "cantidad":        int(self.entry_cantidad.get()),
                "precio_unitario": float(self.entry_precio.get()),
                "iva":             float(self.entry_iva.get())
            }
            Compra.registrar(**datos)
            messagebox.showinfo("✅ Éxito", "Compra registrada correctamente.")
            self._limpiar_form()
            self.cargar_combobox()
            self.cargar_tabla()
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    def _seleccionar_fila(self, event):
        sel = self.tabla.selection()
        if not sel:
            return
        vals = self.tabla.item(sel[0])["values"]
        self.compra_seleccionada_id = vals[0]
        self.cmb_proveedor.set(vals[1])
        self.cmb_producto.set(vals[2])
        self.entry_cantidad.delete(0, tk.END);       self.entry_cantidad.insert(0, vals[3])
        self.entry_precio.delete(0, tk.END);         self.entry_precio.insert(0, vals[4])
        self.entry_iva.delete(0, tk.END);            self.entry_iva.insert(0, vals[5])

    def editar_compra(self):
        if not self.compra_seleccionada_id:
            return messagebox.showwarning("Atención", "Selecciona una orden para editar.")
        try:
            datos = {
                "id_compra":       self.compra_seleccionada_id,
                "proveedor":       self.cmb_proveedor.get(),
                "producto":        self.cmb_producto.get(),
                "cantidad":        int(self.entry_cantidad.get()),
                "precio_unitario": float(self.entry_precio.get()),
                "iva":             float(self.entry_iva.get())
            }
            Compra.editar(
                datos["id_compra"], datos["proveedor"], datos["producto"],
                datos["cantidad"], datos["precio_unitario"], datos["iva"]
            )
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

    def enviar_por_correo(self):
        if not self.compra_seleccionada_id:
            return messagebox.showwarning("Atención", "Selecciona una orden para enviar.")
        compra = Compra.obtener_por_id(self.compra_seleccionada_id)
        # Buscar correo del proveedor
        prov = Proveedor.buscar_por_nombre(compra[1])
        if not prov:
            return messagebox.showerror("❌ Error", "No se encontró correo del proveedor.")
        correo = prov[0][6]  # índice 6 = correo
        # Construir y enviar email
        msg = EmailMessage()
        msg["Subject"] = f"Orden de Compra #{compra[0]}"
        msg["From"]    = "tu_empresa@dominio.com"
        msg["To"]      = correo
        cuerpo = (
            f"Orden de Compra #{compra[0]}\n\n"
            f"Proveedor: {compra[1]}\n"
            f"Producto: {compra[2]}\n"
            f"Cantidad: {compra[3]}\n"
            f"Precio Unitario: {compra[4]}\n"
            f"IVA: {compra[5]*100:.0f}%\n"
            f"Total: {compra[6]}\n"
            f"Fecha: {compra[7]}\n"
        )
        msg.set_content(cuerpo)
        try:
            with smtplib.SMTP("localhost") as s:
                s.send_message(msg)
            messagebox.showinfo("✉️ Enviado", f"Orden enviada a {correo}")
        except Exception as e:
            messagebox.showerror("❌ Error al enviar", str(e))

    def _limpiar_form(self):
        self.compra_seleccionada_id = None
        self.cmb_proveedor.set("")
        self.cmb_producto.set("")
        self.entry_cantidad.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.entry_iva.delete(0, tk.END)
