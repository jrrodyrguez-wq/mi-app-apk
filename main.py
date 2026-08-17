import sqlite3
import urllib.parse
import webbrowser
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, Line
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivy.core.audio import SoundLoader
import cv2
from pyzbar.pyzbar import decode as zbar_decode
import numpy as np

# Configuración para que el teclado virtual no tape las cajas de texto
Window.keyboard_anim_args = {'d': 0.2, 't': 'in_out_quad'}
Window.softinput_mode = 'below_target'

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
            stock INTEGER,
            codigo TEXT
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            telefono TEXT,
            detalle TEXT,
            direccion TEXT,
            estado TEXT DEFAULT 'Pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conexion.commit()
    conexion.close()

KV = '''
<BotonLista>:
    background_color: 0.3, 0.6, 0.9, 1
    color: 1, 1, 1, 1

<MenuDrawer>:
    canvas.before:
        Color:
            rgba: 0.92, 0.92, 0.92, 1
        Rectangle:
            pos: self.pos
            size: self.size
    
    BoxLayout:
        orientation: 'vertical'
        size_hint: 1, 1

        # Barra superior estática
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

        # Contenedor de las pantallas del sistema
        ScreenManager:
            id: sm
            
            # 1. IMPRESION DE RECIBOS
            Screen:
                name: 'recibos'
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(10)
                        spacing: dp(10)
                        size_hint_y: None
                        height: self.minimum_height
                        canvas.before:
                            Color:
                                rgba: 0.92, 0.92, 0.92, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size

                        # --- CLIENTE Y CARRITO ---
                        BoxLayout:
                            size_hint_y: None
                            height: dp(45)
                            spacing: dp(10)
                            Spinner:
                                id: spinner_cliente
                                text: "Cliente General"
                                values: []
                                font_size: '14sp'
                                background_color: 1, 1, 1, 1
                                color: 0, 0, 0, 1
                                size_hint_x: 0.7
                            Button:
                                text: "Recargar"
                                size_hint_x: 0.3
                                background_color: 0.3, 0.6, 0.9, 1
                                color: 1, 1, 1, 1
                                bold: True
                                font_size: '12sp'
                                on_press: root.cargar_datos_db()

                        Label:
                            text: "Ticket de Venta / Carrito"
                            size_hint_y: None
                            height: dp(25)
                            font_size: '16sp'
                            color: 0, 0, 0, 1
                            bold: True

                        BoxLayout:
                            id: carrito_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)
                            Label:
                                text: "Carrito vacío"
                                color: 0.3, 0.3, 0.3, 1
                                font_size: '14sp'
                                size_hint_y: None
                                height: dp(40)

                        BoxLayout:
                            size_hint_y: None
                            height: dp(110)
                            orientation: 'vertical'
                            canvas.before:
                                Color:
                                    rgba: 1, 1, 1, 1
                                Rectangle:
                                    pos: self.pos
                                    size: self.size
                            padding: dp(8)
                            spacing: dp(5)
                            Label:
                                id: lbl_subtotal
                                text: "Subtotal: $ 0.00"
                                color: 0, 0, 0, 1
                                font_size: '13sp'
                                halign: 'right'
                            Label:
                                id: lbl_total
                                text: "Total: $ 0.00"
                                color: 0, 0, 0, 1
                                font_size: '17sp'
                                bold: True
                            BoxLayout:
                                spacing: dp(10)
                                size_hint_y: None
                                height: dp(40)
                                Button:
                                    text: "IMPRIMIR"
                                    background_color: 0.1, 0.6, 0.2, 1
                                    color: 1, 1, 1, 1
                                    font_size: '14sp'
                                    bold: True
                                    on_press: root.imprimir_ticket()
                                Button:
                                    text: "GUARDAR"
                                    background_color: 0.3, 0.6, 0.9, 1
                                    color: 1, 1, 1, 1
                                    font_size: '14sp'
                                    bold: True
                                    on_press: root.guardar_venta()

                        # --- BUSCADOR Y ESCÁNER DE PRODUCTOS ---
                        Label:
                            text: "Buscar Productos"
                            size_hint_y: None
                            height: dp(25)
                            color: 0.1, 0.1, 0.1, 1
                            bold: True
                            font_size: '14sp'

                        BoxLayout:
                            size_hint_y: None
                            height: dp(40)
                            spacing: dp(5)
                            TextInput:
                                id: input_prod
                                hint_text: "Nombre o código..."
                                size_hint_x: 0.7
                                multiline: False
                                foreground_color: 0, 0, 0, 1
                                background_color: 1, 1, 1, 1
                                cursor_color: 0, 0, 0, 1
                                on_text: root.buscar_productos(self.text)
                            Button:
                                text: "📷 Escanear"
                                size_hint_x: 0.3
                                background_color: 0.1, 0.6, 0.2, 1
                                color: 1, 1, 1, 1
                                bold: True
                                font_size: '12sp'
                                on_press: root.abrir_escaner_camara(modo='carrito')

                        # --- CONTROLES PARA CANTIDAD MULTIPLE ---
                        BoxLayout:
                            size_hint_y: None
                            height: dp(40)
                            spacing: dp(5)
                            Label:
                                text: "Cant:"
                                size_hint_x: None
                                width: dp(45)
                                color: 0, 0, 0, 1
                                bold: True
                                font_size: '13sp'
                            TextInput:
                                id: input_cant_agregar
                                text: "1"
                                input_filter: 'int'
                                multiline: False
                                size_hint_x: 0.3
                                font_size: '15sp'
                                foreground_color: 0, 0, 0, 1
                                background_color: 1, 1, 1, 1
                                cursor_color: 0, 0, 0, 1
                                halign: 'center'
                            Button:
                                text: "+1"
                                size_hint_x: 0.23
                                background_color: 0.3, 0.6, 0.9, 1
                                color: 1, 1, 1, 1
                                bold: True
                                on_press: root.sumar_cantidad_input(1)
                            Button:
                                text: "+5"
                                size_hint_x: 0.23
                                background_color: 0.3, 0.6, 0.9, 1
                                color: 1, 1, 1, 1
                                bold: True
                                on_press: root.sumar_cantidad_input(5)
                            Button:
                                text: "+10"
                                size_hint_x: 0.24
                                background_color: 0.3, 0.6, 0.9, 1
                                color: 1, 1, 1, 1
                                bold: True
                                on_press: root.sumar_cantidad_input(10)

                        RecycleView:
                            id: rv_productos
                            data: root.productos_data
                            viewclass: 'BotonLista'
                            size_hint_y: None
                            height: dp(160)
                            RecycleBoxLayout:
                                default_size: None, dp(40)
                                default_size_hint: 1, None
                                size_hint_y: None
                                height: self.minimum_height
                                orientation: 'vertical'

                        # --- BUSCADOR DE CLIENTES ---
                        Label:
                            text: "Buscar Clientes"
                            size_hint_y: None
                            height: dp(25)
                            color: 0.1, 0.1, 0.1, 1
                            bold: True
                            font_size: '14sp'

                        TextInput:
                            id: input_cli
                            hint_text: "Nombre o teléfono..."
                            size_hint_y: None
                            height: dp(40)
                            multiline: False
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            on_text: root.buscar_clientes(self.text)

                        RecycleView:
                            id: rv_clientes
                            data: root.clientes_data
                            viewclass: 'BotonLista'
                            size_hint_y: None
                            height: dp(120)
                            RecycleBoxLayout:
                                default_size: None, dp(40)
                                default_size_hint: 1, None
                                size_hint_y: None
                                height: self.minimum_height
                                orientation: 'vertical'

            # 2. PEDIDOS Y WHATSAPP
            Screen:
                name: 'pedidos'
                ScrollView:
                    do_scroll_x: False
                    do_scroll_y: True
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(15)
                        spacing: dp(12)
                        size_hint_y: None
                        height: self.minimum_height
                        canvas.before:
                            Color:
                                rgba: 0.92, 0.92, 0.92, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size

                        Label:
                            text: "Registro y Envío de Pedidos"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                            size_hint_y: None
                            height: dp(30)

                        BoxLayout:
                            size_hint_y: None
                            height: dp(45)
                            spacing: dp(10)
                            Spinner:
                                id: spinner_pedido_cliente
                                text: "Seleccionar cliente registrado..."
                                values: []
                                font_size: '13sp'
                                background_color: 1, 1, 1, 1
                                color: 0, 0, 0, 1
                                on_text: root.rellenar_cliente_pedido(self.text)
                            Button:
                                text: "Actualizar"
                                size_hint_x: None
                                width: dp(90)
                                background_color: 0.3, 0.6, 0.9, 1
                                color: 1, 1, 1, 1
                                bold: True
                                font_size: '12sp'
                                on_press: root.cargar_datos_db()

                        TextInput:
                            id: pedido_nombre_cliente
                            hint_text: "Nombre del cliente o negocio"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '14sp'

                        TextInput:
                            id: pedido_telefono
                            hint_text: "Teléfono (ej: 52614...)"
                            input_filter: 'int'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '14sp'

                        TextInput:
                            id: pedido_detalle
                            hint_text: "Detalles del pedido (Productos, cantidades)..."
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(80)
                            font_size: '14sp'

                        TextInput:
                            id: pedido_direccion
                            hint_text: "Dirección de entrega (Opcional)"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '14sp'

                        BoxLayout:
                            size_hint_y: None
                            height: dp(45)
                            spacing: dp(10)
                            Button:
                                text: "Guardar"
                                background_color: 0.3, 0.6, 0.9, 1
                                color: 1, 1, 1, 1
                                font_size: '14sp'
                                bold: True
                                on_press: root.guardar_nuevo_pedido()
                            Button:
                                text: "WhatsApp 📱"
                                background_color: 0.1, 0.6, 0.3, 1
                                color: 1, 1, 1, 1
                                font_size: '14sp'
                                bold: True
                                on_press: root.enviar_pedido_whatsapp()

                        Label:
                            text: "Historial de Pedidos Registrados"
                            color: 0, 0, 0, 1
                            font_size: '15sp'
                            bold: True
                            size_hint_y: None
                            height: dp(30)

                        BoxLayout:
                            id: lista_pedidos_layout
                            orientation: 'vertical'
                            size_hint_y: None
                            height: self.minimum_height
                            spacing: dp(5)

            # 3. CLIENTES
            Screen:
                name: 'clientes'
                ScrollView:
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(15)
                        spacing: dp(12)
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
                            font_size: '20sp'
                            bold: True
                            size_hint_y: None
                            height: dp(35)
                        
                        TextInput:
                            id: cliente_nombre
                            hint_text: "Nombre del cliente"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        TextInput:
                            id: cliente_telefono
                            hint_text: "Teléfono"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        Button:
                            text: "Guardar Cliente"
                            size_hint_y: None
                            height: dp(45)
                            background_color: 0.3, 0.6, 0.9, 1
                            color: 1, 1, 1, 1
                            font_size: '15sp'
                            bold: True
                            on_press: root.guardar_cliente(cliente_nombre.text, cliente_telefono.text)

                        Label:
                            text: "--------------------------------------------------"
                            color: 0.5, 0.5, 0.5, 1
                            size_hint_y: None
                            height: dp(20)

                        Spinner:
                            id: spinner_editar_cliente
                            text: "Seleccionar cliente a editar"
                            values: []
                            font_size: '14sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            on_text: root.cargar_datos_cliente_editar(self.text)

                        TextInput:
                            id: cliente_edit_nombre
                            hint_text: "Nuevo nombre"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        TextInput:
                            id: cliente_edit_telefono
                            hint_text: "Nuevo teléfono"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        Button:
                            text: "Actualizar Cliente"
                            size_hint_y: None
                            height: dp(45)
                            background_color: 0.1, 0.6, 0.2, 1
                            color: 1, 1, 1, 1
                            font_size: '15sp'
                            bold: True
                            on_press: root.actualizar_cliente(spinner_editar_cliente.text, cliente_edit_nombre.text, cliente_edit_telefono.text)

            # 4. PRODUCTOS
            Screen:
                name: 'productos'
                ScrollView:
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(15)
                        spacing: dp(12)
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
                            font_size: '20sp'
                            bold: True
                            size_hint_y: None
                            height: dp(35)
                        
                        TextInput:
                            id: prod_nombre
                            hint_text: "Nombre del producto"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        TextInput:
                            id: prod_precio
                            hint_text: "Precio ($)"
                            input_filter: 'float'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        TextInput:
                            id: prod_stock
                            hint_text: "Stock / Cantidad inicial"
                            input_filter: 'int'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        BoxLayout:
                            size_hint_y: None
                            height: dp(45)
                            spacing: dp(5)
                            TextInput:
                                id: prod_codigo
                                hint_text: "Código de barras (Opcional)"
                                size_hint_x: 0.7
                                foreground_color: 0, 0, 0, 1
                                background_color: 1, 1, 1, 1
                                cursor_color: 0, 0, 0, 1
                                font_size: '15sp'
                            Button:
                                text: "📷 Escanear"
                                size_hint_x: 0.3
                                background_color: 0.1, 0.6, 0.2, 1
                                color: 1, 1, 1, 1
                                bold: True
                                font_size: '12sp'
                                on_press: root.abrir_escaner_camara(modo='alta_codigo')

                        Button:
                            text: "Registrar Producto"
                            size_hint_y: None
                            height: dp(45)
                            background_color: 0.1, 0.6, 0.2, 1
                            color: 1, 1, 1, 1
                            font_size: '15sp'
                            bold: True
                            on_press: root.guardar_producto(prod_nombre.text, prod_precio.text, prod_stock.text, prod_codigo.text)

                        Label:
                            text: "--------------------------------------------------"
                            color: 0.5, 0.5, 0.5, 1
                            size_hint_y: None
                            height: dp(20)

                        Spinner:
                            id: spinner_editar_producto
                            text: "Seleccionar producto a editar"
                            values: []
                            font_size: '14sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            on_text: root.cargar_datos_producto_editar(self.text)

                        TextInput:
                            id: prod_edit_nombre
                            hint_text: "Nuevo nombre"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        TextInput:
                            id: prod_edit_precio
                            hint_text: "Nuevo precio ($)"
                            input_filter: 'float'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        TextInput:
                            id: prod_edit_stock
                            hint_text: "Nuevo stock"
                            input_filter: 'int'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '15sp'

                        BoxLayout:
                            size_hint_y: None
                            height: dp(45)
                            spacing: dp(5)
                            TextInput:
                                id: prod_edit_codigo
                                hint_text: "Nuevo código"
                                size_hint_x: 0.7
                                foreground_color: 0, 0, 0, 1
                                background_color: 1, 1, 1, 1
                                cursor_color: 0, 0, 0, 1
                                font_size: '15sp'
                            Button:
                                text: "📷 Escanear"
                                size_hint_x: 0.3
                                background_color: 0.1, 0.6, 0.2, 1
                                color: 1, 1, 1, 1
                                bold: True
                                font_size: '12sp'
                                on_press: root.abrir_escaner_camara(modo='edit_codigo')

                        Button:
                            text: "Actualizar Producto"
                            size_hint_y: None
                            height: dp(45)
                            background_color: 0.3, 0.6, 0.9, 1
                            color: 1, 1, 1, 1
                            font_size: '15sp'
                            bold: True
                            on_press: root.actualizar_producto(spinner_editar_producto.text, prod_edit_nombre.text, prod_edit_precio.text, prod_edit_stock.text, prod_edit_codigo.text)

            # 5. INVENTARIOS
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
                            text: "Inventarios"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(90)
                            background_color: 0.3, 0.6, 0.9, 1
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

            # 6. REPORTE DEL DÍA
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
                        font_size: '20sp'
                        bold: True
                        size_hint_y: None
                        height: dp(40)
                    Button:
                        text: "Generar Reporte de Hoy"
                        size_hint_y: None
                        height: dp(55)
                        background_color: 0.3, 0.6, 0.9, 1
                        color: 1, 1, 1, 1
                        font_size: '16sp'
                        bold: True
                        on_press: root.generar_reporte_completo_dia()
                    Widget:

            # 7. VENTAS DIARIAS (HISTORIAL)
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
                            text: "Ventas Diarias"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(90)
                            background_color: 0.3, 0.6, 0.9, 1
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

            # 8. PRODUCTOS MÁS VENDIDOS
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
                            text: "Más Vendidos"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(90)
                            background_color: 0.3, 0.6, 0.9, 1
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

            # 9. REPORTES GUARDADOS
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
                            text: "Reportes Guardados"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(90)
                            background_color: 0.3, 0.6, 0.9, 1
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

            # 10. GASTOS / COMPRAS
            Screen:
                name: 'gastos'
                ScrollView:
                    BoxLayout:
                        orientation: 'vertical'
                        padding: dp(15)
                        spacing: dp(12)
                        size_hint_y: None
                        height: self.minimum_height
                        canvas.before:
                            Color:
                                rgba: 0.92, 0.92, 0.92, 1
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        Label:
                            text: "Registro de Compras / Gastos"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                            size_hint_y: None
                            height: dp(35)
                        
                        Spinner:
                            id: spinner_producto_compra
                            text: "Seleccionar producto a reabastecer (Opcional)"
                            values: []
                            font_size: '13sp'
                            background_color: 1, 1, 1, 1
                            color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)

                        TextInput:
                            id: compra_cantidad_prod
                            hint_text: "Cantidad a sumar al inventario"
                            input_filter: 'int'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '14sp'

                        TextInput:
                            id: gasto_desc
                            hint_text: "Descripción del gasto"
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '14sp'

                        TextInput:
                            id: gasto_monto
                            hint_text: "Monto total gastado ($)"
                            input_filter: 'float'
                            foreground_color: 0, 0, 0, 1
                            background_color: 1, 1, 1, 1
                            cursor_color: 0, 0, 0, 1
                            size_hint_y: None
                            height: dp(45)
                            font_size: '14sp'

                        Button:
                            text: "Registrar Compra / Gasto"
                            size_hint_y: None
                            height: dp(45)
                            background_color: 0.8, 0.3, 0.2, 1
                            color: 1, 1, 1, 1
                            font_size: '15sp'
                            bold: True
                            on_press: root.guardar_compra_gasto(spinner_producto_compra.text, compra_cantidad_prod.text, gasto_desc.text, gasto_monto.text)

            # 11. RECIBOS ANTERIORES
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
                            text: "Historial de Recibos"
                            color: 0, 0, 0, 1
                            font_size: '18sp'
                            bold: True
                        Button:
                            text: "Actualizar"
                            size_hint_x: None
                            width: dp(90)
                            background_color: 0.3, 0.6, 0.9, 1
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

    # --- PANEL LATERAL OVERLAY ---
    BoxLayout:
        id: nav_panel
        orientation: 'vertical'
        size_hint: None, 1
        width: 0
        x: self.parent.x if self.parent else 0
        y: self.parent.y if self.parent else 0
        canvas.before:
            Color:
                rgba: 0.96, 0.96, 0.96, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        BoxLayout:
            size_hint_y: None
            height: dp(90)
            padding: 10
            canvas.before:
                Color:
                    rgba: 0.15, 0.45, 0.75, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "SISTEMA POS RUTA"
                color: 1, 1, 1, 1
                font_size: '16sp'
                bold: True

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(2)
                padding: [0, 5, 0, 5]

                Button:
                    text: "   Impresión de Recibos"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('recibos')

                Button:
                    text: "   Pedidos y WhatsApp"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('pedidos')

                Button:
                    text: "   Clientes"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('clientes')

                Button:
                    text: "   Productos"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('productos')

                Button:
                    text: "   Inventarios"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('inventarios')

                Button:
                    text: "   Reporte del Día"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('informes')

                Button:
                    text: "   Ventas Diarias (Historial)"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('ventas_diarias')

                Button:
                    text: "   Productos Más Vendidos"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('mas_vendidos')

                Button:
                    text: "   Reportes Guardados"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('reportes_guardados')

                Button:
                    text: "   Gastos / Compras"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('gastos')

                Button:
                    text: "   Recibos anteriores"
                    halign: 'left'
                    valign: 'middle'
                    size_hint_y: None
                    height: dp(45)
                    background_color: 0.3, 0.6, 0.9, 1
                    color: 1, 1, 1, 1
                    font_size: '14sp'
                    on_press: root.cambiar_pantalla('recibos_anteriores')
'''

Builder.load_string(KV)

class BotonLista(Button):
    pass

class MenuDrawer(FloatLayout):
    titulo_pantalla = StringProperty("Impresión de Recibos")
    menu_abierto = False
    
    productos_data = ListProperty([])
    clientes_data = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carrito = []
        self.sound_beep = SoundLoader.load('Barcode scanner beep sound (sound effect).mp3')
        self.cargar_datos_db()

    def reproducir_beep(self):
        if self.sound_beep:
            self.sound_beep.play()

    def abrir_escaner_camara(self, modo='carrito'):
        layout = FloatLayout()
        
        # Inicialización rápida de cámara
        # OPTIMIZACIÓN: fijar una resolución baja (en vez de dejar que el driver
        # negocie la máxima resolución del sensor). Esto hace que la cámara
        # abra más rápido y que cada frame pese menos para procesar.
        camara = Camera(index=0, play=True, size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                         resolution=(640, 480))
        layout.add_widget(camara)
        
        overlay = FloatLayout(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        with overlay.canvas:
            Color(1, 0, 0, 0.8)
            self.linea_roja = Line(points=[], width=2)

        def actualizar_linea(instance, value):
            center_y = camara.center_y
            self.linea_roja.points = [camara.x + dp(20), center_y, camara.right - dp(20), center_y]

        camara.bind(pos=actualizar_linea, size=actualizar_linea)
        layout.add_widget(overlay)
        
        lbl_estado = Label(
            text="Alinea el código con la línea roja...",
            size_hint=(1, None), height=dp(30),
            pos_hint={'x': 0, 'top': 0.98},
            color=(1, 1, 1, 1), bold=True
        )
        layout.add_widget(lbl_estado)
        
        btn_cerrar = Button(
            text="Cancelar / Cerrar",
            size_hint=(1, None), height=dp(45),
            pos_hint={'x': 0, 'y': 0},
            background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1), bold=True
        )
        layout.add_widget(btn_cerrar)

        popup = Popup(title="Escáner de Código de Barras", content=layout, size_hint=(0.95, 0.85), auto_dismiss=False)
        
        def cerrar_popup(instance):
            Clock.unschedule(procesar_frame)
            camara.play = False
            popup.dismiss()

        btn_cerrar.bind(on_press=cerrar_popup)

        def procesar_frame(dt):
            if not camara.texture:
                return
            try:
                buffer = camara.texture.pixels
                w, h = camara.texture.size
                
                if not buffer or len(buffer) != w * h * 4:
                    return

                frame = np.frombuffer(buffer, dtype=np.uint8).reshape((h, w, 4))

                # OPTIMIZACIÓN 1: recortar solo la franja central (alrededor de la
                # línea roja donde el usuario alinea el código). Menos píxeles
                # que analizar = detección mucho más rápida. Se deja suficiente
                # alto para que también entren códigos QR.
                franja_alto = int(h * 0.55)
                centro_y = h // 2
                y0 = max(0, centro_y - franja_alto // 2)
                y1 = min(h, centro_y + franja_alto // 2)
                frame_franja = frame[y0:y1, :]

                # OPTIMIZACIÓN 2: Reducir tamaño de la imagen para procesamiento ultra rápido
                escala = 0.45
                frame_small = cv2.resize(frame_franja, (0, 0), fx=escala, fy=escala, interpolation=cv2.INTER_NEAREST)
                frame_small = cv2.flip(frame_small, 0)
                
                # OPTIMIZACIÓN 3: Extracción directa de canal escala de grises
                gray = cv2.cvtColor(frame_small, cv2.COLOR_RGBA2GRAY)

                # OPTIMIZACIÓN 4: pyzbar lee códigos de barras 1D y QR directamente
                # sobre la imagen en escala de grises (más liviano que a color).
                barcodes = zbar_decode(gray)
                for barcode in barcodes:
                    codigo_detectado = barcode.data.decode('utf-8', errors='ignore')
                    if codigo_detectado:
                        Clock.unschedule(procesar_frame)
                        camara.play = False
                        self.reproducir_beep()
                        popup.dismiss()
                        
                        if modo == 'carrito':
                            self.procesar_codigo_escaneado(codigo_detectado)
                        elif modo == 'alta_codigo':
                            self.ids.prod_codigo.text = codigo_detectado
                        elif modo == 'edit_codigo':
                            self.ids.prod_edit_codigo.text = codigo_detectado
                        break
            except Exception as e:
                print(f"Error procesando frame del escáner: {e}")

        # OPTIMIZACIÓN 5: Ejecutar el escaneo a 30 FPS. Como cada frame ahora
        # pesa mucho menos (franja recortada + menor resolución + menor escala),
        # este intervalo se cumple de verdad en vez de ir "atrasado", que era
        # la causa real de que el escaneo se sintiera lento.
        Clock.schedule_interval(procesar_frame, 1.0 / 30.0)
        popup.open()

    def procesar_codigo_escaneado(self, codigo):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, precio, stock FROM productos WHERE codigo = ?", (codigo,))
        producto = cursor.fetchone()
        conexion.close()

        if producto:
            nombre, precio, stock_actual = producto
            cant_str = self.ids.input_cant_agregar.text.strip()
            self.agregar_al_carrito(nombre, cant_str if cant_str else "1")
            self.ids.input_cant_agregar.text = "1"
        else:
            self.popup_producto_no_registrado_alerta(codigo)

    def popup_producto_no_registrado_alerta(self, codigo):
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        content.add_widget(Label(
            text="⚠️ PRODUCTO NO REGISTRADO",
            color=(0.9, 0.2, 0.2, 1), font_size='16sp', bold=True, size_hint_y=None, height=dp(30)
        ))
        
        content.add_widget(Label(
            text=f"El código scanneado [{codigo}] no se encuentra en el inventario.\n\nPor favor, regístrelo en la sección de Productos para continuar.",
            color=(0, 0, 0, 1), font_size='14sp', halign='center'
        ))

        btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        btn_ir_a_registrar = Button(
            text="Ir a Registrar Producto",
            background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True
        )
        btn_cerrar = Button(
            text="Cerrar",
            background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1), bold=True
        )

        popup = Popup(title="Aviso de Inventario", content=content, size_hint=(0.85, 0.45), auto_dismiss=False)

        def ir_a_productos(instance):
            popup.dismiss()
            self.cambiar_pantalla('productos')
            self.ids.prod_codigo.text = codigo

        btn_ir_a_registrar.bind(on_press=ir_a_productos)
        btn_cerrar.bind(on_press=popup.dismiss)

        btn_layout.add_widget(btn_ir_a_registrar)
        btn_layout.add_widget(btn_cerrar)
        content.add_widget(btn_layout)

        with content.canvas.before:
            Color(1, 1, 1, 1)
            rect = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda s, p: setattr(rect, 'pos', p), size=lambda s, sz: setattr(rect, 'size', sz))

        popup.open()

    def sumar_cantidad_input(self, valor):
        try:
            val_actual = int(self.ids.input_cant_agregar.text)
        except ValueError:
            val_actual = 0
        self.ids.input_cant_agregar.text = str(val_actual + valor)

    def cargar_datos_db(self):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        
        cursor.execute("SELECT nombre FROM clientes")
        clientes_db = [row[0] for row in cursor.fetchall()]
        if clientes_db:
            self.ids.spinner_cliente.values = clientes_db
            self.ids.spinner_cliente.text = clientes_db[0]
            self.ids.spinner_editar_cliente.values = clientes_db
            self.ids.spinner_editar_cliente.text = "Seleccionar cliente a editar"
            self.ids.spinner_pedido_cliente.values = ["Seleccionar cliente registrado..."] + clientes_db
            self.ids.spinner_pedido_cliente.text = "Seleccionar cliente registrado..."
        else:
            self.ids.spinner_cliente.values = ["Sin clientes guardados"]
            self.ids.spinner_cliente.text = "Sin clientes guardados"
            self.ids.spinner_editar_cliente.values = ["Sin clientes guardados"]
            self.ids.spinner_editar_cliente.text = "Sin clientes guardados"
            self.ids.spinner_pedido_cliente.values = ["Sin clientes guardados"]
            self.ids.spinner_pedido_cliente.text = "Sin clientes guardados"

        cursor.execute("SELECT nombre FROM productos")
        productos_db = [row[0] for row in cursor.fetchall()]
        if productos_db:
            self.ids.spinner_producto_compra.values = ["Seleccionar producto a reabastecer"] + productos_db
            self.ids.spinner_producto_compra.text = "Seleccionar producto a reabastecer"
            self.ids.spinner_editar_producto.values = productos_db
            self.ids.spinner_editar_producto.text = "Seleccionar producto a editar"
        else:
            self.ids.spinner_producto_compra.values = ["Sin productos en inventario"]
            self.ids.spinner_producto_compra.text = "Sin productos en inventario"
            self.ids.spinner_editar_producto.values = ["Sin productos en inventario"]
            self.ids.spinner_editar_producto.text = "Sin productos en inventario"
            
        conexion.close()
        
        self.buscar_productos("")
        self.buscar_clientes("")
        
        self.cargar_inventario_tiempo_real()
        self.cargar_ventas_diarias_historial()
        self.cargar_productos_mas_vendidos_pantalla()
        self.cargar_lista_reportes_guardados()
        self.cargar_recibos_anteriores()
        self.cargar_lista_pedidos()

    def buscar_productos(self, texto):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        query = f"%{texto}%"
        cursor.execute("SELECT nombre, precio, codigo FROM productos WHERE nombre LIKE ? OR codigo LIKE ?", (query, query))
        resultados = cursor.fetchall()
        conexion.close()
        
        self.productos_data = [
            {
                'text': f"{row[0]} - ${row[1]}",
                'on_press': lambda r=row: self.agregar_al_carrito_desde_buscador(r[0])
            } for row in resultados
        ]

    def buscar_clientes(self, texto):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        query = f"%{texto}%"
        cursor.execute("SELECT nombre, telefono FROM clientes WHERE nombre LIKE ? OR telefono LIKE ?", (query, query))
        resultados = cursor.fetchall()
        conexion.close()
        
        self.clientes_data = [
            {
                'text': f"{row[0]} ({row[1]})",
                'on_press': lambda r=row: self.seleccionar_cliente_desde_buscador(r[0])
            } for row in resultados
        ]

    def seleccionar_cliente_desde_buscador(self, nombre_cliente):
        self.ids.spinner_cliente.text = nombre_cliente

    def agregar_al_carrito_desde_buscador(self, producto_nombre):
        cant_str = self.ids.input_cant_agregar.text.strip()
        self.agregar_al_carrito(producto_nombre, cant_str if cant_str else "1")
        self.ids.input_cant_agregar.text = "1"

    def rellenar_cliente_pedido(self, nombre_cliente):
        if not nombre_cliente or "Seleccionar" in nombre_cliente or "Sin clientes" in nombre_cliente:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, telefono FROM clientes WHERE nombre = ?", (nombre_cliente,))
        res = cursor.fetchone()
        conexion.close()
        if res:
            self.ids.pedido_nombre_cliente.text = res[0]
            self.ids.pedido_telefono.text = str(res[1] if res[1] else "")

    def guardar_nuevo_pedido(self):
        cliente = self.ids.pedido_nombre_cliente.text.strip()
        telefono = self.ids.pedido_telefono.text.strip()
        detalle = self.ids.pedido_detalle.text.strip()
        direccion = self.ids.pedido_direccion.text.strip()

        if not cliente or not detalle:
            return

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO pedidos (cliente, telefono, detalle, direccion, estado)
            VALUES (?, ?, ?, ?, 'Pendiente')
        """, (cliente, telefono, detalle, direccion))
        conexion.commit()
        conexion.close()

        self.ids.pedido_nombre_cliente.text = ""
        self.ids.pedido_telefono.text = ""
        self.ids.pedido_detalle.text = ""
        self.ids.pedido_direccion.text = ""
        self.cargar_lista_pedidos()

    def cargar_lista_pedidos(self):
        layout = self.ids.lista_pedidos_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT id, cliente, telefono, detalle, direccion, estado, fecha FROM pedidos ORDER BY id DESC")
        pedidos = cursor.fetchall()
        conexion.close()

        if not pedidos:
            lbl = Label(text="No hay pedidos registrados.", color=(0.3, 0.3, 0.3, 1), font_size='14sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            for p_id, cli, tel, det, dir_, estado, fecha in pedidos:
                row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
                
                texto_btn = f"#{p_id} | {cli} | {estado}"
                btn_det = Button(text=texto_btn, size_hint_x=0.7, background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True, font_size='12sp')
                btn_det.bind(on_press=lambda instance, pid=p_id: self.ver_detalle_pedido(pid))

                btn_wsp = Button(text="📱 WSP", size_hint_x=0.3, background_color=(0.1, 0.6, 0.3, 1), color=(1,1,1,1), bold=True, font_size='12sp')
                btn_wsp.bind(on_press=lambda instance, t=tel, c=cli, d=det, dr=dir_: self.enviar_whatsapp_directo(t, c, d, dr))

                row.add_widget(btn_det)
                row.add_widget(btn_wsp)
                layout.add_widget(row)

    def enviar_pedido_whatsapp(self):
        cli = self.ids.pedido_nombre_cliente.text.strip()
        tel = self.ids.pedido_telefono.text.strip()
        det = self.ids.pedido_detalle.text.strip()
        dir_ = self.ids.pedido_direccion.text.strip()

        if not cli or not det:
            return
        
        self.enviar_whatsapp_directo(tel, cli, det, dir_)

    def enviar_whatsapp_directo(self, telefono, cliente, detalle, direccion):
        mensaje = f"*¡Hola, {cliente}!* 🛒\n\nAquí tienes los detalles de tu pedido en *SISTEMA POS RUTA*:\n\n"
        mensaje += f"📝 *Detalle:* \n{detalle}\n\n"
        if direccion:
            mensaje += f"📍 *Dirección de entrega:* {direccion}\n\n"
        mensaje += "¡Gracias por tu preferencia! Quedamos a tus órdenes. 🙌"

        texto_codificado = urllib.parse.quote(mensaje)
        tel_limpio = "".join(filter(str.isdigit, telefono))
        
        if tel_limpio:
            url = f"https://wa.me/{tel_limpio}?text={texto_codificado}"
        else:
            url = f"https://wa.me/?text={texto_codificado}"

        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Error al abrir WhatsApp: {e}")

    def ver_detalle_pedido(self, pedido_id):
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT cliente, telefono, detalle, direccion, estado, fecha FROM pedidos WHERE id = ?", (pedido_id,))
        p = cursor.fetchone()
        conexion.close()

        if p:
            cli, tel, det, dir_, estado, fecha = p
            texto = f"Pedido ID: #{pedido_id}\nFecha: {fecha}\nCliente: {cli}\nTeléfono: {tel}\nEstado: {estado}\n\nDetalle:\n{det}\n\nDirección:\n{dir_ if dir_ else 'N/A'}"

            content = BoxLayout(orientation='vertical', padding=15, spacing=10)
            with content.canvas.before:
                Color(1, 1, 1, 1)
                self.bg_rect_ped = Rectangle(pos=content.pos, size=content.size)
            content.bind(pos=lambda s, pos: setattr(self.bg_rect_ped, 'pos', pos),
                         size=lambda s, sz: setattr(self.bg_rect_ped, 'size', sz))

            scroll = ScrollView(size_hint=(1, 1))
            lbl = Label(text=texto, color=(0,0,0,1), font_size='14sp', halign='left', valign='top', size_hint_y=None)
            lbl.bind(width=lambda s, w: setattr(s, 'text_size', (w, None)))
            lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
            scroll.add_widget(lbl)
            content.add_widget(scroll)

            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
            btn_wsp = Button(text="Enviar WSP", background_color=(0.1, 0.6, 0.3, 1), color=(1,1,1,1), bold=True)
            btn_cerrar = Button(text="Cerrar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True)

            popup = Popup(title=f"Detalle Pedido #{pedido_id}", content=content, size_hint=(0.9, 0.75))

            btn_wsp.bind(on_press=lambda instance: self.enviar_whatsapp_directo(tel, cli, det, dir_))
            btn_cerrar.bind(on_press=popup.dismiss)

            btn_layout.add_widget(btn_wsp)
            btn_layout.add_widget(btn_cerrar)
            content.add_widget(btn_layout)
            popup.open()

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
        cursor.execute("SELECT nombre, precio, stock, codigo FROM productos WHERE nombre = ?", (nombre_producto,))
        res = cursor.fetchone()
        conexion.close()
        if res:
            self.ids.prod_edit_nombre.text = res[0]
            self.ids.prod_edit_precio.text = str(res[1])
            self.ids.prod_edit_stock.text = str(res[2])
            self.ids.prod_edit_codigo.text = str(res[3] if res[3] else "")

    def actualizar_producto(self, producto_antiguo, nuevo_nombre, nuevo_precio, nuevo_stock, nuevo_codigo):
        if not producto_antiguo or "Seleccionar" in producto_antiguo or not nuevo_nombre.strip() or not nuevo_precio.strip():
            return
        try:
            p = float(nuevo_precio)
            s = int(nuevo_stock) if nuevo_stock.strip() else 0
        except ValueError:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("UPDATE productos SET nombre = ?, precio = ?, stock = ?, codigo = ? WHERE nombre = ?", (nuevo_nombre, p, s, nuevo_codigo, producto_antiguo))
        conexion.commit()
        conexion.close()
        self.ids.prod_edit_nombre.text = ""
        self.ids.prod_edit_precio.text = ""
        self.ids.prod_edit_stock.text = ""
        self.ids.prod_edit_codigo.text = ""
        self.cargar_datos_db()

    def cargar_inventario_tiempo_real(self):
        layout = self.ids.inventario_layout
        layout.clear_widgets()

        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, precio, stock, codigo FROM productos")
        productos = cursor.fetchall()
        conexion.close()

        if not productos:
            lbl = Label(text="No hay productos registrados.", color=(0.3, 0.3, 0.3, 1), font_size='15sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            header_layout = BoxLayout(size_hint_y=None, height=dp(35))
            header_layout.add_widget(Label(text="[b]Producto[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Precio[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Stock[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Código[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            layout.add_widget(header_layout)

            for prod, precio, stock, codigo in productos:
                row = BoxLayout(size_hint_y=None, height=dp(40))
                row.add_widget(Label(text=str(prod), color=(0, 0, 0, 1), font_size='12sp'))
                row.add_widget(Label(text=f"${precio:.2f}", color=(0, 0, 0, 1), font_size='12sp'))
                row.add_widget(Label(text=str(stock), color=(0, 0, 0, 1), font_size='12sp', bold=True))
                row.add_widget(Label(text=str(codigo if codigo else ""), color=(0, 0, 0, 1), font_size='12sp'))
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
            lbl = Label(text="Aún no hay registros de ventas diarias.", color=(0.3, 0.3, 0.3, 1), font_size='15sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            header_layout = BoxLayout(size_hint_y=None, height=dp(35))
            header_layout.add_widget(Label(text="[b]Fecha[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Tickets[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Total[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            layout.add_widget(header_layout)

            for dia, num_tickets, suma_total in resultados:
                row = BoxLayout(size_hint_y=None, height=dp(40))
                row.add_widget(Label(text=str(dia), color=(0, 0, 0, 1), font_size='12sp', bold=True))
                row.add_widget(Label(text=str(num_tickets), color=(0, 0, 0, 1), font_size='12sp'))
                row.add_widget(Label(text=f"${suma_total:.2f}", color=(0, 0, 0, 1), font_size='12sp', bold=True))
                layout.add_widget(row)

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
            lbl = Label(text="Aún no hay registros de ventas.", color=(0.3, 0.3, 0.3, 1), font_size='15sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            header_layout = BoxLayout(size_hint_y=None, height=dp(35))
            header_layout.add_widget(Label(text="[b]Producto[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Cant.[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            header_layout.add_widget(Label(text="[b]Total[/b]", markup=True, color=(0.1, 0.1, 0.1, 1), font_size='13sp'))
            layout.add_widget(header_layout)

            for prod, cant, dinero in resultados:
                row = BoxLayout(size_hint_y=None, height=dp(40))
                row.add_widget(Label(text=str(prod), color=(0, 0, 0, 1), font_size='12sp'))
                row.add_widget(Label(text=str(cant), color=(0, 0, 0, 1), font_size='12sp', bold=True))
                row.add_widget(Label(text=f"${dinero:.2f}", color=(0, 0, 0, 1), font_size='12sp'))
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

    def guardar_producto(self, nombre, precio, stock, codigo):
        if not nombre.strip() or not precio.strip():
            return
        try:
            p = float(precio)
            s = int(stock) if stock.strip() else 0
        except ValueError:
            return
        conexion = sqlite3.connect("sistemapos.db")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO productos (nombre, precio, stock, codigo) VALUES (?, ?, ?, ?)", (nombre, p, s, codigo))
        conexion.commit()
        conexion.close()
        self.ids.prod_nombre.text = ""
        self.ids.prod_precio.text = ""
        self.ids.prod_stock.text = ""
        self.ids.prod_codigo.text = ""
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
            if cantidad <= 0:
                cantidad = 1
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
            lbl = Label(text="Carrito vacío", color=(0.3, 0.3, 0.3, 1), font_size='14sp', size_hint_y=None, height=dp(35))
            layout.add_widget(lbl)
        else:
            for item in self.carrito:
                total_general += item['subtotal']
                
                row = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(5))
                texto_item = f"{item['cantidad']}x {item['nombre']} (${item['precio']}) - ${item['subtotal']:.2f}"
                lbl = Label(text=texto_item, color=(0, 0, 0, 1), font_size='12sp', size_hint_x=0.6, halign='left', valign='middle')
                lbl.bind(size=lbl.setter('text_size'))
                
                btn_editar = Button(text="Editar $", size_hint_x=0.2, background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), font_size='10sp', bold=True)
                btn_editar.bind(on_press=lambda instance, prod_name=item['nombre']: self.abrir_popup_editar_precio(prod_name))
                
                btn_eliminar = Button(text="X", size_hint_x=0.2, background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1), font_size='11sp', bold=True)
                btn_eliminar.bind(on_press=lambda instance, prod_name=item['nombre']: self.abrir_popup_eliminar(prod_name))
                
                row.add_widget(lbl)
                row.add_widget(btn_editar)
                row.add_widget(btn_eliminar)
                layout.add_widget(row)

        self.ids.lbl_subtotal.text = f"Subtotal: $ {total_general:.2f}"
        self.ids.lbl_total.text = f"Total: $ {total_general:.2f}"

    def abrir_popup_editar_precio(self, producto_nombre):
        item_actual = next((i for i in self.carrito if i['nombre'] == producto_nombre), None)
        if not item_actual:
            return

        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        content.add_widget(Label(text=f"Editar precio unitario para:\n{producto_nombre}", color=(0,0,0,1), font_size='14sp', halign='center'))
        content.add_widget(Label(text=f"Precio actual: ${item_actual['precio']:.2f}", color=(0.3,0.3,0.3,1), font_size='13sp'))

        txt_nuevo_precio = TextInput(hint_text="Nuevo precio unitario", input_filter='float', multiline=False, font_size='16sp', size_hint_y=None, height=dp(45))
        content.add_widget(txt_nuevo_precio)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        btn_guardar = Button(text="Guardar", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True)
        btn_cancelar = Button(text="Cancelar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True)

        popup = Popup(title="Editar Precio", content=content, size_hint=(0.85, 0.45))

        def guardar_nuevo_precio(instance):
            try:
                nuevo_p = float(txt_nuevo_precio.text)
                if nuevo_p >= 0:
                    item_actual['precio'] = nuevo_p
                    item_actual['subtotal'] = item_actual['cantidad'] * nuevo_p
                    self.actualizar_vista_carrito()
                    popup.dismiss()
            except ValueError:
                pass

        btn_guardar.bind(on_press=guardar_nuevo_precio)
        btn_cancelar.bind(on_press=popup.dismiss)

        btn_layout.add_widget(btn_guardar)
        btn_layout.add_widget(btn_cancelar)
        content.add_widget(btn_layout)

        with content.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect_ed = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda s, p: setattr(self.bg_rect_ed, 'pos', p),
                     size=lambda s, sz: setattr(self.bg_rect_ed, 'size', sz))

        popup.open()

    def abrir_popup_eliminar(self, producto_nombre):
        item_actual = next((i for i in self.carrito if i['nombre'] == producto_nombre), None)
        if not item_actual:
            return

        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        content.add_widget(Label(text=f"¿Cuántas unidades de\n'{producto_nombre}' deseas eliminar?", color=(0,0,0,1), font_size='14sp', halign='center'))
        content.add_widget(Label(text=f"Cantidad actual: {item_actual['cantidad']}", color=(0.3,0.3,0.3,1), font_size='13sp'))

        txt_cantidad = TextInput(text="0", input_filter='int', multiline=False, font_size='18sp', size_hint_y=None, height=dp(45))
        content.add_widget(txt_cantidad)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        btn_aceptar = Button(text="Eliminar", background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1), bold=True)
        btn_cancelar = Button(text="Cancelar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True)

        popup = Popup(title="Eliminar del Carrito", content=content, size_hint=(0.85, 0.45))

        def procesar_eliminacion(instance):
            try:
                cant_a_quitar = int(txt_cantidad.text)
                if cant_a_quitar > 0:
                    if cant_a_quitar >= item_actual['cantidad']:
                        self.carrito.remove(item_actual)
                    else:
                        item_actual['cantidad'] -= cant_a_quitar
                        item_actual['subtotal'] = item_actual['cantidad'] * item_actual['precio']
                    self.actualizar_vista_carrito()
                popup.dismiss()
            except ValueError:
                pass

        btn_aceptar.bind(on_press=procesar_eliminacion)
        btn_cancelar.bind(on_press=popup.dismiss)

        btn_layout.add_widget(btn_aceptar)
        btn_layout.add_widget(btn_cancelar)
        content.add_widget(btn_layout)

        with content.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect_del = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda s, p: setattr(self.bg_rect_del, 'pos', p),
                     size=lambda s, sz: setattr(self.bg_rect_del, 'size', sz))

        popup.open()

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
            lbl = Label(text="No hay recibos registrados aún.", color=(0.3, 0.3, 0.3, 1), font_size='15sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            for rec_id, cliente, total, fecha in recibos:
                btn = Button(
                    text=f"Ticket #{rec_id} | {cliente} | ${total:.2f}",
                    size_hint_y=None,
                    height=dp(45),
                    background_color=(0.3, 0.6, 0.9, 1),
                    color=(1, 1, 1, 1),
                    bold=True,
                    font_size='13sp'
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
            
            texto_ticket = f"SISTEMA POS RUTA\n"
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
            lbl = Label(text=texto_ticket, color=(0,0,0,1), size_hint_y=None, font_size='13sp', halign='left', valign='top')
            lbl.bind(width=lambda s, w: setattr(s, 'text_size', (int(w), None)))
            lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
            scroll.add_widget(lbl)
            content.add_widget(scroll)

            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
            btn_imprimir = Button(text="Reimprimir", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True)
            btn_cerrar = Button(text="Cerrar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True)
            
            popup = Popup(title=f"Detalle Ticket #{recibo_id}", content=content, size_hint=(0.9, 0.85))
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
        lbl = Label(text=texto_reporte, color=(0,0,0,1), size_hint_y=None, font_size='13sp', halign='left', valign='top')
        lbl.bind(width=lambda s, w: setattr(s, 'text_size', (int(w), None)))
        lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
        scroll.add_widget(lbl)
        content.add_widget(scroll)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=5)
        btn_imprimir = Button(text="Imprimir", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True, font_size='12sp')
        btn_guardar = Button(text="Guardar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True, font_size='12sp')
        btn_cerrar = Button(text="Cerrar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True, font_size='12sp')
        
        popup = Popup(title=f"Reporte Diario - {fecha_hoy}", content=content, size_hint=(0.9, 0.85))
        
        btn_imprimir.bind(on_press=lambda instance: self.imprimir_texto_directo(texto_reporte))
        btn_guardar.bind(on_press=lambda instance: (self.guardar_reporte_en_db(fecha_hoy, texto_reporte), popup.dismiss()))
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
            lbl = Label(text="No hay reportes guardados.", color=(0.3, 0.3, 0.3, 1), font_size='15sp', size_hint_y=None, height=dp(40))
            layout.add_widget(lbl)
        else:
            for rep_id, fecha_rep, fecha_creacion in reportes:
                btn = Button(
                    text=f"Reporte {fecha_rep}",
                    size_hint_y=None,
                    height=dp(45),
                    background_color=(0.3, 0.6, 0.9, 1),
                    color=(1, 1, 1, 1),
                    bold=True,
                    font_size='13sp'
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
            lbl = Label(text=contenido, color=(0,0,0,1), size_hint_y=None, font_size='13sp', halign='left', valign='top')
            lbl.bind(width=lambda s, w: setattr(s, 'text_size', (int(w), None)))
            lbl.bind(texture_size=lambda s, t: setattr(s, 'height', t[1]))
            scroll.add_widget(lbl)
            content.add_widget(scroll)

            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
            btn_imprimir = Button(text="Imprimir", background_color=(0.1, 0.6, 0.2, 1), color=(1,1,1,1), bold=True)
            btn_cerrar = Button(text="Cerrar", background_color=(0.3, 0.6, 0.9, 1), color=(1,1,1,1), bold=True)
            
            popup = Popup(title=f"Reporte Guardado - {fecha_rep}", content=content, size_hint=(0.9, 0.85))
            btn_imprimir.bind(on_press=lambda instance: self.imprimir_texto_directo(contenido))
            btn_cerrar.bind(on_press=popup.dismiss)
            
            btn_layout.add_widget(btn_imprimir)
            btn_layout.add_widget(btn_cerrar)
            content.add_widget(btn_layout)
            popup.open()

    def imprimir_texto_directo(self, texto):
        try:
            bytes_ticket = bytearray()
            bytes_ticket.extend(b'\x1B\x45\x01')
            bytes_ticket.extend(texto.encode('utf-8', errors='ignore'))
            bytes_ticket.extend(b"\n\n\n")
            bytes_ticket.extend(b'\x1B\x45\x00')
            bytes_ticket.extend(b'\x1D\x56\x41\x00')
            
            if platform == 'android':
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
                    output_stream.write(bytes(bytes_ticket))
                    output_stream.flush()
                    socket.close()
            else:
                print("Simulación de impresión directa:")
                print(bytes_ticket.decode('utf-8', errors='ignore'))
        except Exception as e:
            print(f"Error Bluetooth directo: {e}")

    def toggle_menu(self):
        nav = self.ids.nav_panel
        if self.menu_abierto:
            nav.width = 0
            self.menu_abierto = False
        else:
            nav.width = dp(240)
            self.menu_abierto = True

    def cambiar_pantalla(self, nombre_pantalla):
        if self.menu_abierto:
            self.toggle_menu()

        self.ids.sm.current = nombre_pantalla
        nombres = {
            'recibos': "Impresión de Recibos",
            'pedidos': "Pedidos y WhatsApp",
            'clientes': "Clientes",
            'productos': "Productos",
            'inventarios': "Inventarios",
            'informes': "Reporte del Día",
            'ventas_diarias': "Ventas Diarias",
            'mas_vendidos': "Más Vendidos",
            'reportes_guardados': "Reportes Guardados",
            'gastos': "Gastos / Compras",
            'recibos_anteriores': "Recibos anteriores"
        }
        self.titulo_pantalla = nombres.get(nombre_pantalla, "POS")
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
        elif nombre_pantalla == 'pedidos':
            self.cargar_lista_pedidos()

    def imprimir_ticket(self):
        if not self.carrito:
            return
        
        cliente = self.ids.spinner_cliente.text
        total_general = sum(item['subtotal'] for item in self.carrito)

        try:
            bytes_ticket = bytearray()
            bytes_ticket.extend(b'\x1B\x45\x01')
            bytes_ticket.extend(b"================================\n")
            bytes_ticket.extend(b"       SISTEMA POS RUTA         \n")
            bytes_ticket.extend(b"================================\n")
            bytes_ticket.extend(f"Cliente: {cliente}\n".encode('utf-8', errors='ignore'))
            bytes_ticket.extend(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n".encode('utf-8'))
            bytes_ticket.extend(b"--------------------------------\n")
            bytes_ticket.extend(b"Cant   Articulo       Subtotal\n")
            for item in self.carrito:
                nombre_p = item['nombre'][:12]
                linea = f"{item['cantidad']:<6} {nombre_p:<12} ${item['subtotal']:.2f}\n"
                bytes_ticket.extend(linea.encode('utf-8', errors='ignore'))
            bytes_ticket.extend(b"--------------------------------\n")
            bytes_ticket.extend(f"TOTAL: ${total_general:.2f}\n".encode('utf-8'))
            bytes_ticket.extend(b"================================\n")
            bytes_ticket.extend(b"  Gracias por su preferencia!   \n\n\n\n")
            bytes_ticket.extend(b'\x1B\x45\x00')
            bytes_ticket.extend(b'\x1D\x56\x41\x00')

            if platform == 'android':
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
                    output_stream.write(bytes(bytes_ticket))
                    output_stream.flush()
                    socket.close()
                    self.guardar_venta()
            else:
                print("Simulación de impresión de ticket:")
                print(bytes_ticket.decode('utf-8', errors='ignore'))
                self.guardar_venta()
        except Exception as e:
            print(f"Error al imprimir ticket: {e}")

class SistemaPOSApp(App):
    def build(self):
        inicializar_db()
        return MenuDrawer()

if __name__ == '__main__':
    SistemaPOSApp().run()
