# app/ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Type

# Vistas
from app.ui.productos_view import ProductosView
from app.ui.clientes_view import ClientesView
from app.ui.proveedores_view import ProveedoresView
from app.ui.compras_view import ComprasView
from app.ui.ventas_view import VentasView
from app.ui.inventario_view import InventarioView
from app.ui.finanzas_view import FinanzasView
from app.ui.ctas_por_cobrar_view import CtasPorCobrarView
from app.ui.ctas_por_pagar_view import CtasPorPagarView
from app.ui.consulta_ingresos_view import ConsultaIngresosView
from app.ui.gastos_view import GastosView
from app.ui.estado_resultados_view import EstadoResultadosView
from app.ui.categorias_view import CategoriasView
from app.ui.ingreso_inventario_view import IngresoInventarioView


class MainWindow(tk.Tk):
    OPCIONES_EMOJI = [
        "📦 Productos", "👥 Clientes", "🏢 Proveedores", "🛒 Compras", "💰 Ventas",
        "📦 Inventario", "📊 Finanzas", "💳 Ctas por cobrar", "💸 Ctas por pagar",
        "🧾 Consulta de Ingresos", "📉 Gastos", "📈 Estado de Resultados",
        "🏷️ Categorías", "📥 Ingreso de Productos",
    ]

    MAPEO_VISTAS: Dict[str, Type[tk.Frame]] = {
        "Productos": ProductosView,
        "Clientes": ClientesView,
        "Proveedores": ProveedoresView,
        "Compras": ComprasView,
        "Ventas": VentasView,
        "Inventario": InventarioView,
        "Finanzas": FinanzasView,
        "Ctas por cobrar": CtasPorCobrarView,
        "Ctas por pagar": CtasPorPagarView,
        "Consulta de Ingresos": ConsultaIngresosView,
        "Gastos": GastosView,
        "Estado de Resultados": EstadoResultadosView,
        "Categorías": CategoriasView,
        "Ingreso de Productos": IngresoInventarioView,
    }

    def __init__(self, servicios: Dict | None = None):
        super().__init__()
        self.title("Control de Tu Negocio")
        self.geometry("1120x640")
        self.configure(bg="#f0f0f0")

        # Tema y estilos
        try:
            style = ttk.Style(self)
            if "clam" in style.theme_names():
                style.theme_use("clam")
            style.configure("Treeview", rowheight=22, font=("Segoe UI", 10))
            style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
            style.configure("TButton", padding=4)
        except Exception:
            pass

        self.servicios = servicios or {}
        self._cache_vistas: Dict[str, tk.Frame] = {}

        self._build_layout()
        self._build_sidebar()
        self._build_statusbar()

        # Vista por defecto
        self.mostrar_vista("💰 Ventas")

        # Atajos
        self.bind("<Control-q>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self._focus_sidebar())

    # ---- layout ----
    def _build_layout(self):
        self.sidebar = tk.Frame(self, bg="#2c3e50", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.contenedor = tk.Frame(self, bg="white")
        self.contenedor.pack(side="right", expand=True, fill="both")

    def _build_sidebar(self):
        tk.Label(
            self.sidebar, text="Menú", fg="white", bg="#2c3e50",
            font=("Segoe UI", 12, "bold"), pady=12
        ).pack(fill="x")
        for texto in self.OPCIONES_EMOJI:
            tk.Button(
                self.sidebar, text=texto, fg="white", bg="#34495e",
                activebackground="#1abc9c", activeforeground="white", bd=0,
                padx=10, pady=8, anchor="w",
                command=lambda t=texto: self.mostrar_vista(t),
            ).pack(fill="x", padx=10, pady=4)

        tk.Frame(self.sidebar, height=2, bg="#22313F").pack(fill="x", padx=10, pady=8)
        tk.Button(
            self.sidebar, text="Salir  ⌘Q", fg="#ecf0f1", bg="#c0392b",
            activebackground="#e74c3c", activeforeground="white", bd=0,
            padx=10, pady=8, command=self.destroy
        ).pack(fill="x", padx=10, pady=4)

    def _build_statusbar(self):
        self.statusbar = tk.Frame(self, bg="#ecf0f1", height=24)
        self.statusbar.pack(side="bottom", fill="x")
        self.status_msg = tk.StringVar(value="Listo.")
        tk.Label(
            self.statusbar, textvariable=self.status_msg, bg="#ecf0f1",
            fg="#2c3e50", anchor="w", padx=8
        ).pack(side="left", fill="x", expand=True)

    # ---- navegación ----
    @staticmethod
    def _nombre_limpio(texto_menu: str) -> str:
        return texto_menu.split(" ", 1)[1] if " " in texto_menu else texto_menu

    def _focus_sidebar(self):
        # Intenta enfocar el primer botón del menú
        for w in self.sidebar.winfo_children():
            if isinstance(w, tk.Button):
                w.focus_set()
                break

    def _limpiar_contenedor(self):
        for w in self.contenedor.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self.update_idletasks()

    def _mostrar_en_contenedor(self, vista: tk.Frame):
        self._limpiar_contenedor()
        vista.pack(expand=True, fill="both")

    def mostrar_vista(self, texto_menu: str):
        """
        Navega a la vista solicitada (con caché) e intenta crearla:
        1) con 'servicios' (API nueva)
        2) sin 'servicios' (compatibilidad)
        """
        clave = self._nombre_limpio(texto_menu)
        self.status_msg.set(f"Abrir: {clave}")
        vista_cls = self.MAPEO_VISTAS.get(clave)

        if vista_cls is None:
            self._limpiar_contenedor()
            frame = tk.Frame(self.contenedor, bg="white")
            frame.pack(expand=True, fill="both")
            tk.Label(
                frame, text=f"Vista no implementada: {clave}",
                font=("Segoe UI", 16), bg="white"
            ).pack(pady=48)
            return

        # Si ya existe en caché, sólo mostrar
        if clave in self._cache_vistas:
            self._mostrar_en_contenedor(self._cache_vistas[clave])
            return

        # Intento A: con servicios
        holder = tk.Frame(self.contenedor, bg="white")
        holder.pack(expand=True, fill="both")
        try:
            vista = vista_cls(holder, servicios=self.servicios)  # puede fallar si la vista no acepta 'servicios'
            vista.pack(expand=True, fill="both")
            self._cache_vistas[clave] = vista
            return
        except TypeError:
            # Compatibilidad: sin servicios
            try:
                holder.destroy()
            except Exception:
                pass
            self.update_idletasks()
            holder = tk.Frame(self.contenedor, bg="white")
            holder.pack(expand=True, fill="both")
            try:
                vista = vista_cls(holder)  # modo legacy
                vista.pack(expand=True, fill="both")
                self._cache_vistas[clave] = vista
                self.status_msg.set(f"{clave}: modo compatibilidad (sin 'servicios').")
                return
            except Exception as e2:
                try:
                    holder.destroy()
                except Exception:
                    pass
                self.update_idletasks()
                messagebox.showerror("Error al abrir vista", f"No se pudo abrir '{clave}'.\n\n{e2}")
                self.status_msg.set(f"Error abriendo {clave}")
                return
        except Exception as e:
            try:
                holder.destroy()
            except Exception:
                pass
            self.update_idletasks()
            messagebox.showerror("Error al abrir vista", f"No se pudo abrir '{clave}'.\n\n{e}")
            self.status_msg.set(f"Error abriendo {clave}")
            return


def iniciar_app(servicios: Dict | None = None):
    app = MainWindow(servicios=servicios or {})
    app.update_idletasks()
    # Tamaño mínimo prudente para que quepan las vistas
    app.minsize(980, 600)
    app.mainloop()
