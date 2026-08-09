import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle

if platform == 'android':
    from jnius import autoclass
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    UUID = autoclass('java.util.UUID')

# Inicializar Base de Datos SQLite y Tablas
def inicializar_db():
    conexion = sqlite3.connect("sistemapos.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            precio REAL,
            stock INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            telefono TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recibos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            total REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_recibos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recibo_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            precio REAL,
            subtotal REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT,
            monto REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reportes_guardados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_reporte DATE,
            contenido TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conexion.commit()
    conexion.close()

KV = '''
<MenuDrawer>:
    canvas.before:
        Color:
            rgba: 0.92, 0.92, 0.92, 1
        Rectangle:
            pos: self.pos
            size: self.size
    
    # Área principal de la aplicación (ocupa el 100% de la pantalla)
    BoxLayout:
        orientation: 'vertical'
        size_hint: 1, 1
        pos_hint: {'x': 0, 'y': 0}
        
        # Barra superior con botón de menú
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            canvas.before:
                Color:
                    rgba: 0.15, 0.45, 0.75, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "≡"
                size_hint_x: None
                width: dp(60)
                font_size: '26sp'
                background_color: 0, 0, 0, 0
                color: 1, 1, 1, 1
                on_press: root.toggle_menu()
            Label:
                text: root.titulo_pantalla
                color: 1, 1, 1, 1
                font_size: '18sp'
                bold: True
                halign: 'left'
                valign: 'middle'
            
        ScreenManager:
            id: sm
            
            # 1. IMPRESION DE RECIBOS
            Screen:
                name: 'recibos'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size

                    BoxLayout:
                        size_hint_y: None
                        height: dp(55)
                        spacing: dp(10)
                        Spinner:
                            id: spinner_cliente
                            text: "Seleccionar Cliente"
                            values: []
                            font_size: '16sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_x: 0.75
                        Button:
                            text: "Recargar"
                            size_hint_x: 0.25
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            bold: True
                            font_size: '14sp'
                            on_press: root.cargar_datos_db()

                    BoxLayout:
                        size_hint_y: None
                        height: dp(55)
                        spacing: dp(10)
                        Spinner:
                            id: spinner_producto
                            text: "Seleccionar Producto"
                            values: []
                            font_size: '16sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_x: 0.55
                        TextInput:
                            id: txt_cantidad
                            text: "1"
                            hint_text: "Cant"
                            input_filter: 'int'
                            font_size: '16sp'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_x: 0.2
                        Button:
                            text: "+"
                            size_hint_x: 0.25
                            background_color: 0.1, 0.6, 0.2, 1
                            color: 1, 1, 1, 1
                            bold: True
                            font_size: '22sp'
                            on_press: root.agregar_al_carrito(spinner_producto.text, txt_cantidad.text)

                    ScrollView:
                        BoxLayout:
                            id: carrito_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)
                            Label:
                                text: "Carrito vacío"
                                color: 0.3, 0.3, 0.3, 1
                                font_size: '16sp'
                                size_hint_y: None
                                height: dp(40)

                    BoxLayout:
                        size_hint_y: None
                        height: dp(130)
                        orientation: 'vertical'
                        canvas.before:
                            Color:
                                rgba: 1, 1, 1, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        padding: dp(10)
                        spacing: dp(5)
                        Label:
                            id: lbl_subtotal
                            text: "Subtotal: $ 0.00"
                            color: 0, 0, 0, 1
                            font_size: '16sp'
                            halign: 'right'
                        Label:
                            id: lbl_total
                            text: "Total: $ 0.00"
                            color: 0, 0, 0, 1
                            font_size: '20sp'
                            bold: True
                        BoxLayout:
                            spacing: dp(10)
                            size_hint_y: None
                            height: dp(50)
                            Button:
                                text: "IMPRIMIR"
                                background_color: 0.1, 0.6, 0.2, 1
                                color: 1, 1, 1, 1
                                font_size: '16sp'
                                bold: True
                                on_press: root.imprimir_ticket()
                            Button:
                                text: "GUARDAR"
                                background_color: 0.2, 0.4, 0.7, 1
                                color: 1, 1, 1, 1
                                font_size: '16sp'
                                bold: True
                                on_press: root.guardar_venta()

            # 2. CLIENTES
            Screen:
                name: 'clientes'
                ScrollView:
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(20)
                        spacing: dp(15)
                        size_hint_y: None
                        height: self.minimum_height
                        canvas.before:
                            Color:
                                rgba: 0.92, 0.92, 0.92, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        
                        Label:
                            text: "Gestión de Clientes"
                            color: 0, 0, 0, 1
                            font_size: '22sp'
                            bold: True
                            size_hint_y: None
                            height: dp(40)
                        
                        Label:
                            text: "Nuevo Cliente:"
                            color: 0.3, 0.3, 0.3, 1
                            font_size: '14sp'
                            bold: True
                            size_hint_y: None
                            height: dp(25)

                        TextInput:
                            id: cliente_nombre
                            hint_text: "Nombre del cliente"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        TextInput:
                            id: cliente_telefono
                            hint_text: "Teléfono"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        Button:
                            text: "Guardar Cliente"
                            size_hint_y: None
                            height: dp(50)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            font_size: '16sp'
                            bold: True
                            on_press: root.guardar_cliente(cliente_nombre.text, cliente_telefono.text)

                        Label:
                            text: "--------------------------------------------------"
                            color: 0.5, 0.5, 0.5, 1
                            size_hint_y: None
                            height: dp(20)

                        Label:
                            text: "Modificar / Editar Cliente Existente:"
                            color: 0.3, 0.3, 0.3, 1
                            font_size: '14sp'
                            bold: True
                            size_hint_y: None
                            height: dp(25)

                        Spinner:
                            id: spinner_editar_cliente
                            text: "Seleccionar cliente a editar"
                            values: []
                            font_size: '16sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            on_text: root.cargar_datos_cliente_editar(self.text)

                        TextInput:
                            id: cliente_edit_nombre
                            hint_text: "Nuevo nombre"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        TextInput:
                            id: cliente_edit_telefono
                            hint_text: "Nuevo teléfono"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        Button:
                            text: "Actualizar Cliente"
                            size_hint_y: None
                            height: dp(50)
                            background_color: 0.1, 0.6, 0.2, 1
                            color: 1, 1, 1, 1
                            font_size: '16sp'
                            bold: True
                            on_press: root.actualizar_cliente(spinner_editar_cliente.text, cliente_edit_nombre.text, cliente_edit_telefono.text)

            # 3. PRODUCTOS
            Screen:
                name: 'productos'
                ScrollView:
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(20)
                        spacing: dp(15)
                        size_hint_y: None
                        height: self.minimum_height
                        canvas.before:
                            Color:
                                rgba: 0.92, 0.92, 0.92, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        
                        Label:
                            text: "Gestión de Productos"
                            color: 0, 0, 0, 1
                            font_size: '22sp'
                            bold: True
                            size_hint_y: None
                            height: dp(40)
                        
                        TextInput:
                            id: prod_nombre
                            hint_text: "Nombre del producto"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        TextInput:
                            id: prod_precio
                            hint_text: "Precio ($)"
                            input_filter: 'float'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        TextInput:
                            id: prod_stock
                            hint_text: "Stock / Cantidad inicial"
                            input_filter: 'int'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        Button:
                            text: "Registrar Producto"
                            size_hint_y: None
                            height: dp(50)
                            background_color: 0.1, 0.6, 0.2, 1
                            color: 1, 1, 1, 1
                            font_size: '16sp'
                            bold: True
                            on_press: root.guardar_producto(prod_nombre.text, prod_precio.text, prod_stock.text)

                        Label:
                            text: "--------------------------------------------------"
                            color: 0.5, 0.5, 0.5, 1
                            size_hint_y: None
                            height: dp(20)

                        Label:
                            text: "Modificar / Editar Producto Existente:"
                            color: 0.3, 0.3, 0.3, 1
                            font_size: '14sp'
                            bold: True
                            size_hint_y: None
                            height: dp(25)

                        Spinner:
                            id: spinner_editar_producto
                            text: "Seleccionar producto a editar"
                            values: []
                            font_size: '16sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            on_text: root.cargar_datos_producto_editar(self.text)

                        TextInput:
                            id: prod_edit_nombre
                            hint_text: "Nuevo nombre"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        TextInput:
                            id: prod_edit_precio
                            hint_text: "Nuevo precio ($)"
                            input_filter: 'float'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        TextInput:
                            id: prod_edit_stock
                            hint_text: "Nuevo stock"
                            input_filter: 'int'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(50)
                            font_size: '16sp'

                        Button:
                            text: "Actualizar Producto"
                            size_hint_y: None
                            height: dp(50)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            font_size: '16sp'
                            bold: True
                            on_press: root.actualizar_producto(spinner_editar_producto.text, prod_edit_nombre.text, prod_edit_precio.text, prod_edit_stock.text)

            # 4. INVENTARIOS
            Screen:
                name: 'inventarios'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: dp(10)
                        Label:
                            text: "Control de Inventarios en Tiempo Real"
                            color: 0, 0, 0, 1
                            font_size: '20sp'
                            bold: True
                            halign: 'left'
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(100)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            bold: True
                            on_press: root.cargar_inventario_tiempo_real()

                    ScrollView:
                        BoxLayout:
                            id: inventario_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)

            # 5. REPORTE DEL DÍA
            Screen:
                name: 'informes'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(15)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    Label:
                        text: "Generación de Reporte del Día"
                        color: 0, 0, 0, 1
                        font_size: '22sp'
                        bold: True
                        size_hint_y: None
                        height: dp(40)
                    Button:
                        text: "Generar y Visualizar Reporte de Hoy"
                        size_hint_y: None
                        height: dp(60)
                        background_color: 0.2, 0.5, 0.8, 1
                        color: 1, 1, 1, 1
                        font_size: '16sp'
                        bold: True
                        on_press: root.generar_reporte_completo_dia()
                    Widget:

            # 6. VENTAS DIARIAS (HISTORIAL)
            Screen:
                name: 'ventas_diarias'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "Historial de Ventas Diarias"
                            color: 0, 0, 0, 1
                            font_size: '20sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(100)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            bold: True
                            on_press: root.cargar_ventas_diarias_historial()
                    ScrollView:
                        BoxLayout:
                            id: ventas_diarias_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)

            # 7. PRODUCTOS MÁS VENDIDOS
            Screen:
                name: 'mas_vendidos'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "Ranking de Productos Más Vendidos"
                            color: 0, 0, 0, 1
                            font_size: '20sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(100)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            bold: True
                            on_press: root.cargar_productos_mas_vendidos_pantalla()
                    ScrollView:
                        BoxLayout:
                            id: mas_vendidos_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)

            # 8. REPORTES GUARDADOS
            Screen:
                name: 'reportes_guardados'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "Historial de Reportes Guardados"
                            color: 0, 0, 0, 1
                            font_size: '20sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(100)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            bold: True
                            on_press: root.cargar_lista_reportes_guardados()
                    ScrollView:
                        BoxLayout:
                            id: reportes_guardados_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)

            # 9. GASTOS / COMPRAS
            Screen:
                name: 'gastos'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(15)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    Label:
                        text: "Registro de Compras de Mercancía / Gastos"
                        color: 0, 0, 0, 1
                        font_size: '20sp'
                        bold: True
                        size_hint_y: None
                        height: dp(40)
                    
                    Spinner:
                        id: spinner_producto_compra
                        text: "Seleccionar producto a reabastecer (Opcional)"
                        values: []
                        font_size: '16sp'
                        background_color: 1, 1, 1, 1
                        color: 0, 0, 0, 1
                        size_hint_y: None
                        height: dp(50)

                    TextInput:
                        id: compra_cantidad_prod
                        hint_text: "Cantidad a sumar al inventario (ej. 10)"
                        input_filter: 'int'
                        foreground_color: 0, 0, 0, 1
                        background_color: 1, 1, 1, 1
                        cursor_color: 0, 0, 0, 1
                        size_hint_y: None
                        height: dp(50)
                        font_size: '16sp'

                    TextInput:
                        id: gasto_desc
                        hint_text: "Descripción (ej. Compra de mercancía)"
                        foreground_color: 0, 0, 0, 1
                        background_color: 1, 1, 1, 1
                        cursor_color: 0, 0, 0, 1
                        size_hint_y: None
                        height: dp(50)
                        font_size: '16sp'

                    TextInput:
                        id: gasto_monto
                        hint_text: "Monto total gastado ($)"
                        input_filter: 'float'
                        foreground_color: 0, 0, 0, 1
                        background_color: 1, 1, 1, 1
                        cursor_color: 0, 0, 0, 1
                        size_hint_y: None
                        height: dp(50)
                        font_size: '16sp'

                    Button:
                        text: "Registrar Compra / Gasto y Actualizar Stock"
                        size_hint_y: None
                        height: dp(55)
                        background_color: 0.8, 0.3, 0.2, 1
                        color: 1, 1, 1, 1
                        font_size: '16sp'
                        bold: True
                        on_press: root.guardar_compra_gasto(spinner_producto_compra.text, compra_cantidad_prod.text, gasto_desc.text, gasto_monto.text)
                    Widget:

            # 10. RECIBOS ANTERIORES
            Screen:
                name: 'recibos_anteriores'
                BoxLayout:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    canvas.before:
                        Color:
                            rgba: 0.92, 0.92, 0.92, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        Label:
                            text: "Historial de Recibos Anteriores"
                            color: 0, 0, 0, 1
                            font_size: '20sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(100)
                            background_color: 0.2, 0.5, 0.8, 1
                            color: 1, 1, 1, 1
                            bold: True
                            on_press: root.cargar_recibos_anteriores()
                    ScrollView:
                        BoxLayout:
                            id: recibos_anteriores_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)

    # Panel lateral deslizable (Menú Flotante Superpuesto / Overlay)
    # Declarado al final para que se dibuje ENCIMA de la pantalla principal
    BoxLayout:
        id: nav_panel
        orientation: 'vertical'
        size_hint: None, 1
        width: dp(0)
        x: 0
        y: 0
        canvas.before:
            Color:
                rgba: 0.96, 0.96, 0.96, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        # Cabecera del Menú Lateral
        BoxLayout:
            size_hint_y: None
            height: dp(120)
            padding: 15
            canvas.before:
                Color:
                    rgba: 0.15, 0.45, 0.75, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "Impresion Termica\\nBluetooth"
                color: 1, 1, 1, 1
                font_size: '18sp'
                bold: True

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(2)
                padding: [0, 10, 0, 10]

                Label:
                    text: "POS"
                    color: 0.4, 0.4, 0.4, 1
                    size_hint_y: None
                    height: dp(30)
                    font_size: '14sp'
                    bold: True
                    padding_x: 15

                Button:
                    text: "   Impresión de Recibos"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('recibos')

                Button:
                    text: "   Clientes"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('clientes')

                Button:
                    text: "   Productos"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('productos')

                Button:
                    text: "   Inventarios"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('inventarios')

                Button:
                    text: "   Reporte del Día"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('informes')

                Button:
                    text: "   Ventas Diarias (Historial)"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('ventas_diarias')

                Button:
                    text: "   Productos Más Vendidos"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('mas_vendidos')

                Button:
                    text: "   Reportes Guardados"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('reportes_guardados')

                Button:
                    text: "   Gastos / Compras"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('gastos')

                Button:
                    text: "   Recibos anteriores"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(50)
                    background_color: 1, 1, 1, 1
                    color: 0.1, 0.1, 0.1, 1
                    font_size: '16sp'
                    on_press: root.cambiar_pantalla('recibos_anteriores')
'''

class MenuDrawer(FloatLayout):
    titulo_pantalla = StringProperty("Impresión de Recibos")
    menu_abierto = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carrito = []
        self.cargar_datos_db()

    def cargar_datos_db(self):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        
        cursor.execute("SELECT nombre FROM clientes")
        clientes = [row[0] for row in cursor.fetchall()]
        if clientes:
            self.ids.spinner_cliente.values = clientes
            self.ids.spinner_cliente.text = clientes[0]
            self.ids.spinner_editar_cliente.values = clientes
            self.ids.spinner_editar_cliente.text = "Seleccionar cliente a editar"
        else:
            self.ids.spinner_cliente.values = ["Sin clientes guardados"]
            self.ids.spinner_cliente.text = "Sin clientes guardados"
            self.ids.spinner_editar_cliente.values = ["Sin clientes guardados"]
            self.ids.spinner_editar_cliente.text = "Sin clientes guardados"

        cursor.execute("SELECT nombre FROM productos")
        productos = [row[0] for row in cursor.fetchall()]
        if productos:
            self.ids.spinner_producto.values = productos
            self.ids.spinner_producto.text = productos[0]
            self.ids.spinner_producto_compra.values = ["Seleccionar producto a reabastecer"] + productos
            self.ids.spinner_producto_compra.text = "Seleccionar producto a reabastecer"
            self.ids.spinner_editar_producto.values = productos
            self.ids.spinner_editar_producto.text = "Seleccionar producto a editar"
        else:
            self.ids.spinner_producto.values = ["Sin productos en inventario"]
            self.ids.spinner_producto.text = "Sin productos en inventario"
            self.ids.spinner_producto_compra.values = ["Sin productos en inventario"]
            self.ids.spinner_producto_compra.text = "Sin productos en inventario"
            self.ids.spinner_editar_producto.values = ["Sin productos en inventario"]
            self.ids.spinner_editar_producto.text = "Sin productos en inventario"
            
        conexion.close()
        self.cargar_inventario_tiempo_real()
        self.cargar_ventas_diarias_historial()
        self.cargar_productos_mas_vendidos_pantalla()
        self.cargar_lista_reportes_guardados()
        self.cargar_recibos_anteriores()

    def cargar_datos_cliente_editar(self, nombre_cliente):
        if not nombre_cliente or "Seleccionar" in nombre_cliente or "Sin clientes" in nombre_cliente:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, telefono FROM clientes WHERE nombre = ?", (nombre_cliente,))
        res = cursor.fetchone()
        conexion.close()
        if res:
            self.ids.cliente_edit_nombre.text = res[0]
            self.ids.cliente_edit_telefono.text = str(res[1] if res[1] else "")

    def actualizar_cliente(self, cliente_antiguo, nuevo_nombre, nuevo_telefono):
        if not cliente_antiguo or "Seleccionar" in cliente_antiguo or not nuevo_nombre.strip():
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("UPDATE clientes SET nombre = ?, telefono = ? WHERE nombre = ?", (nuevo_nombre, nuevo_telefono, cliente_antiguo))
        conexion.commit()
        conexion.close()
        self.ids.cliente_edit_nombre.text = ""
        self.ids.cliente_edit_telefono.text = ""
        self.cargar_datos_db()

    def cargar_datos_producto_editar(self, nombre_producto):
        if not nombre_producto or "Seleccionar" in nombre_producto or "Sin productos" in nombre_producto:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, precio, stock FROM productos WHERE nombre = ?", (nombre_producto,))
        res = cursor.fetchone()
        conexion.close()
        if res:
            self.ids.prod_edit_nombre.text = res[0]
            self.ids.prod_edit_precio.text = str(res[1])
            self.ids.prod_edit_stock.text = str(res[2])

    def actualizar_producto(self, producto_antiguo, nuevo_nombre, nuevo_precio, nuevo_stock):
        if not producto_antiguo or "Seleccionar" in producto_antiguo or not nuevo_nombre.strip() or not nuevo_precio.strip():
            return
        try:
            p = float(nuevo_precio)
            s = int(nuevo_stock) if nuevo_stock.strip() else 0
        except ValueError:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE nombre = ?", (nuevo_nombre, p, s, producto_antiguo))
        conexion.commit()
        conexion.close()
        self.ids.prod_edit_nombre.text = ""
        self.ids.prod_edit_precio.text = ""
        self.ids.prod_edit_stock.text = ""
        self.cargar_datos_db()

    def cargar_inventario_tiempo_real(self):
        layout = self.ids.inventario_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, precio, stock FROM productos")
        productos = cursor.fetchall()
        conexion.close()

        if not productos:
            lbl = Label(text="No hay productos registrados.", color=(0.3, 0.3, 0.3, 1), font_size='16sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            header_layout = BoxLayout(size_hint_y=None, height=dp(40))
            header_layout.add_widget(Label(text="[b]Producto[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            header_layout.add_widget(Label(text="[b]Precio[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            header_layout.add_widget(Label(text="[b]Stock[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            layout.add_widget(header_layout)

            for prod, precio, stock in productos:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(Label(text=str(prod), color=(0, 0, 0, 1), font_size='14sp'))
                row.add_widget(Label(text=f"${precio:.2f}", color=(0, 0, 0, 1), font_size='14sp'))
                row.add_widget(Label(text=str(stock), color=(0, 0, 0, 1), font_size='14sp', bold=True))
                layout.add_widget(row)

    def cargar_ventas_diarias_historial(self):
        layout = self.ids.ventas_diarias_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT date(fecha) as dia, COUNT(id) as total_tickets, SUM(total) as suma_total 
            FROM recibos 
            GROUP BY date(fecha) 
            ORDER BY dia ASC
        """)
        resultados = cursor.fetchall()
        conexion.close()

        if not resultados:
            lbl = Label(text="Aún no hay registros de ventas diarias.", color=(0.3, 0.3, 0.3, 1), font_size='16sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            header_layout = BoxLayout(size_hint_y=None, height=dp(40))
            header_layout.add_widget(Label(text="[b]Día / Fecha[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            header_layout.add_widget(Label(text="[b]Tickets[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            header_layout.add_widget(Label(text="[b]Total Vendido[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            layout.add_widget(header_layout)

            for i, (dia, num_tickets, suma_total) in enumerate(resultados, 1):
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(Label(text=f"Día {i} ({dia})", color=(0, 0, 0, 1), font_size='14sp', bold=True))
                row.add_widget(Label(text=str(num_tickets), color=(0, 0, 0, 1), font_size='14sp'))
                row.add_widget(Label(text=f"${suma_total:.2f}", color=(0, 0, 0, 1), font_size='14sp', bold=True))
                layout.add_widget(row)

    def guardar_cliente(self, nombre, telefono):
        if not nombre.strip():
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO clientes (nombre, telefono) VALUES (?, ?)", (nombre, telefono))
        conexion.commit()
        conexion.close()
        self.ids.cliente_nombre.text = ""
        self.ids.cliente_telefono.text = ""
        self.cargar_datos_db()
        self.cambiar_pantalla('recibos')

    def guardar_producto(self, nombre, precio, stock):
        if not nombre.strip() or not precio.strip():
            return
        try:
            p = float(precio)
            s = int(stock) if stock.strip() else 0
        except ValueError:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)", (nombre, p, s))
        conexion.commit()
        conexion.close()
        self.ids.prod_nombre.text = ""
        self.ids.prod_precio.text = ""
        self.ids.prod_stock.text = ""
        self.cargar_datos_db()
        self.cambiar_pantalla('recibos')

    def guardar_compra_gasto(self, producto_nombre, cantidad_str, descripcion, monto_str):
        if not descripcion.strip() or not monto_str.strip():
            return
        try:
            monto = float(monto_str)
        except ValueError:
            return
            
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO gastos (descripcion, monto) VALUES (?, ?)", (descripcion, monto))
        
        if producto_nombre and "Seleccionar" not in producto_nombre and "Sin productos" not in producto_nombre:
            try:
                cantidad_a_sumar = int(cantidad_str) if cantidad_str.strip() else 0
                if cantidad_a_sumar > 0:
                    cursor.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (cantidad_a_sumar, producto_nombre))
            except ValueError:
                pass
                
        conexion.commit()
        conexion.close()
        
        self.ids.gasto_desc.text = ""
        self.ids.gasto_monto.text = ""
        self.ids.compra_cantidad_prod.text = ""
        self.ids.spinner_producto_compra.text = "Seleccionar producto a reabastecer"
        self.cargar_datos_db()

    def agregar_al_carrito(self, producto_nombre, cantidad_str):
        if not producto_nombre or "Sin productos" in producto_nombre:
            return
        try:
            cantidad = int(cantidad_str) if cantidad_str else 1
        except ValueError:
            cantidad = 1

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT precio FROM productos WHERE nombre = ?", (producto_nombre,))
        res = cursor.fetchone()
        conexion.close()

        if res:
            precio = res[0]
            subtotal = precio * cantidad
            encontrado = False
            for item in self.carrito:
                if item['nombre'] == producto_nombre:
                    item['cantidad'] += cantidad
                    item['subtotal'] = item['cantidad'] * item['precio']
                    encontrado = True
                    break
            if not encontrado:
                self.carrito.append({
                    'nombre': producto_nombre,
                    'precio': precio,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
            self.actualizar_vista_carrito()

    def actualizar_vista_carrito(self):
        layout = self.ids.carrito_layout
        layout.clear_widgets()
        
        total_general = 0.0
        if not self.carrito:
            lbl = Label(text="Carrito vacío", color=(0.3, 0.3, 0.3, 1), font_size='16sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            for item in self.carrito:
                total_general += item['subtotal']
                texto_item = f"{item['cantidad']}x {item['nombre']} - ${item['subtotal']:.2f}"
                lbl = Label(text=texto_item, color=(0, 0, 0, 1), font_size='16sp', size_hint_y=None, height=dp(40), halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                layout.add_widget(lbl)

        self.ids.lbl_subtotal.text = f"Subtotal: $ {total_general:.2f}"
        self.ids.lbl_total.text = f"Total: $ {total_general:.2f}"

    def guardar_venta(self):
        if not self.carrito:
            return
        cliente = self.ids.spinner_cliente.text
        total_general = sum(item['subtotal'] for item in self.carrito)

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        
        cursor.execute("INSERT INTO recibos (cliente, total) VALUES (?, ?)", (cliente, total_general))
        recibo_id = cursor.lastrowid

        for item in self.carrito:
            cursor.execute("""
                INSERT INTO detalle_recibos (recibo_id, producto, cantidad, precio, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (recibo_id, item['nombre'], item['cantidad'], item['precio'], item['subtotal']))
            
            cursor.execute("""
                UPDATE productos SET stock = stock - ? WHERE nombre = ?
            """, (item['cantidad'], item['nombre']))
        
        conexion.commit()
        conexion.close()

        self.carrito = []
        self.actualizar_vista_carrito()
        self.cargar_datos_db()

    def cargar_recibos_anteriores(self):
        layout = self.ids.recibos_anteriores_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT id, cliente, total, fecha FROM recibos ORDER BY id DESC")
        recibos = cursor.fetchall()
        conexion.close()

        if not recibos:
            lbl = Label(text="No hay recibos registrados aún.", color=(0.3, 0.3, 0.3, 1), font_size='16sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            for rec_id, cliente, total, fecha in recibos:
                btn = Button(
                    text=f"Ticket #{rec_id} | Cliente: {cliente} | Total: ${total:.2f} | {fecha}",
                    size_hint_y=None,
                    height=dp(50),
                    background_color=(0.2, 0.5, 0.8, 1),
                    color=(1, 1, 1, 1),
                    bold=True,
                    font_size='14sp'
                )
                btn.bind(on_press=lambda instance, rid=rec_id: self.ver_detalle_recibo_anterior(rid))
                layout.add_widget(btn)

    def ver_detalle_recibo_anterior(self, recibo_id):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT cliente, total, fecha FROM recibos WHERE id = ?", (recibo_id,))
        recibo = cursor.fetchone()
        
        cursor.execute("SELECT producto, cantidad, precio, subtotal FROM detalle_recibos WHERE recibo_id = ?", (recibo_id,))
        detalles = cursor.fetchall()
        conexion.close()

        if recibo:
            cliente, total, fecha = recibo
            
            texto_ticket = f"ABARROTES CERF S.A.\n"
            texto_ticket += f"Ticket #{recibo_id}\n"
            texto_ticket += f"Fecha: {fecha}\n"
            texto_ticket += f"Cliente: {cliente}\n"
            texto_ticket += "--------------------------------\n"
            texto_ticket += "Cant   Articulo       Subtotal\n"
            for prod, cant, precio, subtotal in detalles:
                texto_ticket += f"{cant:<6} {prod:<10} ${subtotal:.2f}\n"
            texto_ticket += "--------------------------------\n"
            texto_ticket += f"TOTAL: ${total:.2f}\n"
            texto_ticket += "Gracias por su preferencia\n\n\n"

            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            with content.canvas.before:
                Color(1, 1, 1, 1)
                self.bg_rect_recibo = Rectangle(pos=content.pos, size=content.size)
            content.bind(pos=lambda s, p: setattr(self.bg_rect_recibo, 'pos', p),
                         size=lambda s, sz: setattr(self.bg_rect_recibo, 'size', sz))

            scroll = ScrollView()
            
            lbl = Label(
                text=texto_ticket, 
                color=(0,0,0,1), 
                size_hint_y=None, 
                font_size='14sp', 
                halign='left', 
                valign='top'
            )
            lbl.bind(width=lambda s, w: setattr(s, 'text_size', (int(w), None)))
            lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
            
            scroll.add_widget(lbl)
            content.add_widget(scroll)

            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
            btn_imprimir = Button(text="Reimprimir Ticket", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True)
            btn_cerrar = Button(text="Cerrar", background_color=(0.7, 0.2, 0.2, 1), color=(1,1,1,1), bold=True)
            
            popup = Popup(title=f"Detalle Ticket #{recibo_id}", content=content, size_hint=(0.9, 0.9))
            
            scroll.bind(width=lambda s, w: setattr(lbl, 'width', int(w)))

            btn_imprimir.bind(on_press=lambda instance: self.imprimir_texto_directo(texto_ticket))
            btn_cerrar.bind(on_press=popup.dismiss)
            
            btn_layout.add_widget(btn_imprimir)
            btn_layout.add_widget(btn_cerrar)
            content.add_widget(btn_layout)
            popup.open()

    def generar_reporte_completo_dia(self):
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        
        cursor.execute("SELECT id, cliente, total FROM recibos WHERE date(fecha) = ?", (fecha_hoy,))
        ventas = cursor.fetchall()
        total_vendido = sum(v[2] for v in ventas)
        
        cursor.execute("SELECT descripcion, monto FROM gastos WHERE date(fecha) = ?", (fecha_hoy,))
        gastos_compras = cursor.fetchall()
        total_gastos = sum(g[1] for g in gastos_compras)
        
        conexion.close()
        
        texto_reporte = f"REPORTE DEL DIA: {fecha_hoy}\n"
        texto_reporte += "================================\n"
        texto_reporte += f"Total Vendido: ${total_vendido:.2f}\n"
        texto_reporte += f"Total Compras/Gastos: ${total_gastos:.2f}\n"
        texto_reporte += f"Balance Neto: ${total_vendido - total_gastos:.2f}\n\n"
        
        texto_reporte += "--- DETALLE DE VENTAS ---\n"
        if ventas:
            for v in ventas:
                texto_reporte += f"Ticket #{v[0]} | Cliente: {v[1]} | ${v[2]:.2f}\n"
        else:
            texto_reporte += "No hay ventas registradas hoy.\n"
            
        texto_reporte += "\n--- DETALLE DE GASTOS/COMPRAS ---\n"
        if gastos_compras:
            for g in gastos_compras:
                texto_reporte += f"- {g[0]}: ${g[1]:.2f}\n"
        else:
            texto_reporte += "No hay gastos registrados hoy.\n"

        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        with content.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect_reporte = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda s, p: setattr(self.bg_rect_reporte, 'pos', p),
                     size=lambda s, sz: setattr(self.bg_rect_reporte, 'size', sz))

        scroll = ScrollView()
        
        lbl = Label(text=texto_reporte, color=(0,0,0,1), size_hint_y=None, font_size='14sp', halign='left', valign='top')
        lbl.bind(width=lambda s, w: setattr(s, 'text_size', (int(w), None)))
        lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
        
        scroll.add_widget(lbl)
        content.add_widget(scroll)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
        btn_imprimir = Button(text="Imprimir", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True)
        btn_guardar = Button(text="Guardar Reporte", background_color=(0.2, 0.4, 0.7, 1), color=(1,1,1,1), bold=True)
        btn_cerrar = Button(text="Cerrar", background_color=(0.7, 0.2, 0.2, 1), color=(1,1,1,1), bold=True)
        
        popup = Popup(title=f"Reporte Diario - {fecha_hoy}", content=content, size_hint=(0.9, 0.9))
        
        def imprimir_desde_popup(instance):
            self.imprimir_texto_directo(texto_reporte)

        def guardar_desde_popup(instance):
            self.guardar_reporte_en_db(fecha_hoy, texto_reporte)
            popup.dismiss()

        btn_imprimir.bind(on_press=imprimir_desde_popup)
        btn_guardar.bind(on_press=guardar_desde_popup)
        btn_cerrar.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(btn_imprimir)
        btn_layout.add_widget(btn_guardar)
        btn_layout.add_widget(btn_cerrar)
        content.add_widget(btn_layout)
        
        popup.open()

    def guardar_reporte_en_db(self, fecha, contenido):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO reportes_guardados (fecha_reporte, contenido) VALUES (?, ?)", (fecha, contenido))
        conexion.commit()
        conexion.close()
        self.cargar_lista_reportes_guardados()

    def cargar_lista_reportes_guardados(self):
        layout = self.ids.reportes_guardados_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fecha_reporte, fecha_creacion FROM reportes_guardados ORDER BY id DESC")
        reportes = cursor.fetchall()
        conexion.close()

        if not reportes:
            lbl = Label(text="No hay reportes guardados.", color=(0.3, 0.3, 0.3, 1), font_size='16sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            for rep_id, fecha_rep, fecha_creacion in reportes:
                btn = Button(
                    text=f"Reporte del {fecha_rep} (Guardado: {fecha_creacion})",
                    size_hint_y=None,
                    height=dp(50),
                    background_color=(0.2, 0.5, 0.8, 1),
                    color=(1, 1, 1, 1),
                    bold=True
                )
                btn.bind(on_press=lambda instance, rid=rep_id: self.ver_detalle_reporte_guardado(rid))
                layout.add_widget(btn)

    def ver_detalle_reporte_guardado(self, reporte_id):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT fecha_reporte, contenido FROM reportes_guardados WHERE id = ?", (reporte_id,))
        res = cursor.fetchone()
        conexion.close()

        if res:
            fecha_rep, contenido = res
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            
            with content.canvas.before:
                Color(1, 1, 1, 1)
                self.bg_rect_guardado = Rectangle(pos=content.pos, size=content.size)
            content.bind(pos=lambda s, p: setattr(self.bg_rect_guardado, 'pos', p),
                         size=lambda s, sz: setattr(self.bg_rect_guardado, 'size', sz))

            scroll = ScrollView()
            lbl = Label(text=contenido, color=(0,0,0,1), size_hint_y=None, font_size='14sp', halign='left', valign='top')
            lbl.bind(width=lambda s, w: setattr(s, 'text_size', (int(w), None)))
            lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
            scroll.add_widget(lbl)
            content.add_widget(scroll)

            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
            btn_imprimir = Button(text="Imprimir", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True)
            btn_cerrar = Button(text="Cerrar", background_color=(0.7, 0.2, 0.2, 1), color=(1,1,1,1), bold=True)
            
            popup = Popup(title=f"Reporte Guardado - {fecha_rep}", content=content, size_hint=(0.9, 0.9))
            
            btn_imprimir.bind(on_press=lambda instance: self.imprimir_texto_directo(contenido))
            btn_cerrar.bind(on_press=popup.dismiss)
            
            btn_layout.add_widget(btn_imprimir)
            btn_layout.add_widget(btn_cerrar)
            content.add_widget(btn_layout)
            popup.open()

    def cargar_productos_mas_vendidos_pantalla(self):
        layout = self.ids.mas_vendidos_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT producto, SUM(cantidad) as total_cant, SUM(subtotal) as total_dinero 
            FROM detalle_recibos 
            GROUP BY producto 
            ORDER BY total_cant DESC
        """)
        resultados = cursor.fetchall()
        conexion.close()

        if not resultados:
            lbl = Label(text="Aún no hay registros de ventas.", color=(0.3, 0.3, 0.3, 1), font_size='16sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            header_layout = BoxLayout(size_hint_y=None, height=dp(40))
            header_layout.add_widget(Label(text="[b]Producto[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            header_layout.add_widget(Label(text="[b]Cant. Vendida[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            header_layout.add_widget(Label(text="[b]Total Ingresos[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='15sp'))
            layout.add_widget(header_layout)

            for prod, cant, dinero in resultados:
                row = BoxLayout(size_hint_y=None, height=dp(45))
                row.add_widget(Label(text=str(prod), color=(0, 0, 0, 1), font_size='14sp'))
                row.add_widget(Label(text=str(cant), color=(0, 0, 0, 1), font_size='14sp', bold=True))
                row.add_widget(Label(text=f"${dinero:.2f}", color=(0, 0, 0, 1), font_size='14sp'))
                layout.add_widget(row)

    def imprimir_texto_directo(self, texto):
        comando_negrita = b'\x1b\x45\x01'
        comando_normal = b'\x1b\x45\x00'
        bytes_ticket = comando_negrita + b"COMPROBANTE\n" + comando_normal + texto.encode('utf-8', errors='ignore') + b"\n\n\n"
        
        if platform == 'android':
            try:
                bluetooth_adapter = BluetoothAdapter.getDefaultAdapter()
                paired_devices = bluetooth_adapter.getBondedDevices().toArray()
                socket = None
                for device in paired_devices:
                    nombre_dev = device.getName().lower()
                    if "mp210" in nombre_dev or "printer" in nombre_dev or "mtp" in nombre_dev or "rp" in nombre_dev:
                        uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
                        socket = device.createInsecureRfcommSocketToServiceRecord(uuid)
                        socket.connect()
                        break
                
                if socket:
                    output_stream = socket.getOutputStream()
                    output_stream.write(bytes_ticket)
                    output_stream.flush()
                    socket.close()
            except Exception as e:
                print(f"Error Bluetooth: {e}")
        else:
            print("Simulación de impresión directa:")
            print(texto)

    def toggle_menu(self):
        nav = self.ids.nav_panel
        if self.menu_abierto:
            nav.width = 0
            self.menu_abierto = False
        else:
            nav.width = dp(260)
            self.menu_abierto = True

    def cambiar_pantalla(self, nombre_pantalla):
        self.ids.sm.current = nombre_pantalla
        nombres = {
            'recibos': "Impresión de Recibos",
            'clientes': "Clientes",
            'productos': "Productos",
            'inventarios': "Inventarios",
            'informes': "Reporte del Día",
            'ventas_diarias': "Ventas Diarias (Historial)",
            'mas_vendidos': "Productos Más Vendidos",
            'reportes_guardados': "Reportes Guardados",
            'gastos': "Gastos / Compras",
            'recibos_anteriores': "Recibos anteriores"
        }
        self.titulo_pantalla = nombres.get(nombre_pantalla, "POS")
        self.ids.nav_panel.width = 0
        self.menu_abierto = False
        if nombre_pantalla == 'inventarios':
            self.cargar_inventario_tiempo_real()
        elif nombre_pantalla == 'ventas_diarias':
            self.cargar_ventas_diarias_historial()
        elif nombre_pantalla == 'mas_vendidos':
            self.cargar_productos_mas_vendidos_pantalla()
        elif nombre_pantalla == 'reportes_guardados':
            self.cargar_lista_reportes_guardados()
        elif nombre_pantalla == 'recibos_anteriores':
            self.cargar_recibos_anteriores()

    def imprimir_ticket(self):
        comando_negrita = b'\x1b\x45\x01'
        comando_normal = b'\x1b\x45\x00'
        
        cliente = self.ids.spinner_cliente.text
        total_general = sum(item['subtotal'] for item in self.carrito) if self.carrito else 0.0

        texto_ticket = (
            comando_negrita + b"ABARROTES CERF S.A.\n" +
            comando_normal +
            b"Cliente: " + cliente.encode('utf-8', errors='ignore') + b"\n" +
            b"--------------------------------\n" +
            b"Cant   Articulo       Subtotal\n"
        )
        for item in self.carrito:
            linea = f"{item['cantidad']:<6} {item['nombre']:<10} ${item['subtotal']:.2f}\n"
            texto_ticket += linea.encode('utf-8', errors='ignore')

        texto_ticket += (
            b"--------------------------------\n" +
            comando_negrita + f"TOTAL: ${total_general:.2f}\n".encode('utf-8') +
            comando_normal +
            b"Gracias por su preferencia\n\n\n"
        )
        
        if platform == 'android':
            try:
                bluetooth_adapter = BluetoothAdapter.getDefaultAdapter()
                paired_devices = bluetooth_adapter.getBondedDevices().toArray()
                socket = None
                for device in paired_devices:
                    nombre_dev = device.getName().lower()
                    if "mp210" in nombre_dev or "printer" in nombre_dev or "mtp" in nombre_dev or "rp" in nombre_dev:
                        uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
                        socket = device.createInsecureRfcommSocketToServiceRecord(uuid)
                        socket.connect()
                        break
                
                if socket:
                    output_stream = socket.getOutputStream()
                    output_stream.write(texto_ticket)
                    output_stream.flush()
                    socket.close()
            except Exception as e:
                print(f"Error Bluetooth: {e}")
        else:
            print("Simulación de impresión en PC:")
            print(texto_ticket.decode('utf-8', errors='ignore'))


class MiAppPOS(App):
    def build(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            def callback(permissions, results):
                pass
            request_permissions([
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_ADMIN,
                Permission.BLUETOOTH
            ], callback)
            
        inicializar_db()
        Builder.load_string(KV)
        return MenuDrawer()


if __name__ == '__main__':
    MiAppPOS().run()
