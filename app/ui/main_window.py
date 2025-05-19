import tkinter as tk
from tkinter import messagebox

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

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control de Tu Negocio")
        self.geometry("1024x600")
        self.configure(bg="#f0f0f0")

        # ✅ Opciones del menú con emojis
        self.opciones = [
            "📦 Productos",
            "👥 Clientes",
            "🏢 Proveedores",
            "🛒 Compras",
            "💰 Ventas",
            "📦 Inventario",
            "📊 Finanzas",
            "💳 Ctas por cobrar",
            "💸 Ctas por pagar",
            "🧾 Consulta de Ingresos",
            "📉 Gastos",
            "📈 Estado de Resultados",
            "🏷️ Categorías"
        ]

        # ✅ Mapeo de vistas (sin emojis)
        self.vistas = {
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
            "Categorías": CategoriasView
        }

        self.crear_menu_lateral()
        self.contenedor_principal = tk.Frame(self, bg="white")
        self.contenedor_principal.pack(expand=True, fill="both", side="right")

    def crear_menu_lateral(self):
        menu_frame = tk.Frame(self, bg="#2c3e50", width=200)
        menu_frame.pack(side="left", fill="y")

        for texto in self.opciones:
            btn = tk.Button(
                menu_frame, text=texto, fg="white", bg="#34495e",
                activebackground="#1abc9c", bd=0, height=2,
                command=lambda t=texto: self.mostrar_vista(t)
            )
            btn.pack(fill="x", padx=10, pady=5)

    def mostrar_vista(self, nombre_vista):
        for widget in self.contenedor_principal.winfo_children():
            widget.destroy()

        # Extraer texto sin emoji
        nombre_limpio = nombre_vista.split(" ", 1)[1] if " " in nombre_vista else nombre_vista
        clase_vista = self.vistas.get(nombre_limpio)

        if clase_vista:
            vista = clase_vista(self.contenedor_principal)
            vista.pack(expand=True, fill="both")
        else:
            etiqueta = tk.Label(
                self.contenedor_principal,
                text=f"Vista no implementada: {nombre_limpio}",
                font=("Arial", 18), bg="white"
            )
            etiqueta.pack(pady=50)

def iniciar_app():
    app = MainWindow()
    app.mainloop()
