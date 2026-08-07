from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.utils import platform
import sqlite3
import datetime

Window.clearcolor = (0.95, 0.96, 0.98, 1)

def inicializar_db():
    conn = sqlite3.connect("ruta.db")
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        precio REAL NOT NULL)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_tienda TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
                        folio INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente TEXT,
                        metodo_pago TEXT,
                        total REAL,
                        fecha TEXT)''')

    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO productos (nombre, precio) VALUES (?, ?)", [
            ("Bubbaloo C/50", 45.00),
            ("Tutsi Pop C/24", 68.00),
            ("Mazapan C/30", 110.00),
            ("Pelon Pelo Rico C/12", 85.00),
            ("Galletas Marias 170g", 18.50),
            ("Aceite 1L", 42.00)
        ])

    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO clientes (nombre_tienda) VALUES (?)", [
            ("Abarrotes Don Pedro",),
            ("Tiendita La Esquina",),
            ("Miscelánea Express",)
        ])

    conn.commit()
    conn.close()

class RenglonCarrito(BoxLayout):
    def __init__(self, item, indice, callback_eliminar, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=38, spacing=5, **kwargs)
        self.item = item
        self.indice = indice

        lbl_item = Label(
            text=f"{item['nombre']} (${item['precio']:.2f})",
            color=(0.2, 0.2, 0.2, 1),
            font_size='12sp',
            halign='left',
            valign='middle',
            size_hint_x=0.75
        )
        lbl_item.bind(size=lbl_item.setter('text_size'))

        btn_borrar = Button(
            text="X",
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.9, 0.2, 0.2, 1),
            bold=True,
            font_size='12sp'
        )
        # Eliminación directa y segura con el botón X
        btn_borrar.bind(on_release=lambda x: callback_eliminar(indice, item))

        self.add_widget(lbl_item)
        self.add_widget(btn_borrar)

class TarjetaProducto(BoxLayout):
    def __init__(self, producto, callback_agregar, callback_editar, **kwargs):
        super().__init__(orientation='horizontal', padding=8, spacing=8, **kwargs)
        self.size_hint_y = None
        self.height = 75
        self.producto = producto
        self.callback_agregar = callback_agregar
        self.callback_editar = callback_editar

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.actualizar_canvas, size=self.actualizar_canvas)

        box_info = BoxLayout(orientation='vertical', spacing=2, size_hint_x=0.7)
        lbl_nombre = Label(
            text=f"[b]{producto['nombre']}[/b]", 
            markup=True, 
            color=(0.15, 0.2, 0.25, 1), 
            font_size='14sp',
            halign='left', 
            valign='middle'
        )
        lbl_nombre.bind(size=lbl_nombre.setter('text_size'))

        lbl_precio = Label(
            text=f"${producto['precio']:.2f}", 
            color=(0.0, 0.6, 0.4, 1), 
            bold=True, 
            font_size='14sp',
            halign='left', 
            valign='middle'
        )
        lbl_precio.bind(size=lbl_precio.setter('text_size'))

        box_info.add_widget(lbl_nombre)
        box_info.add_widget(lbl_precio)

        btn_editar = Button(
            text="Edit",
            size_hint=(0.3, 0.75),
            pos_hint={'center_y': 0.5},
            background_normal='',
            background_color=(0.9, 0.5, 0.1, 1),
            bold=True,
            font_size='12sp'
        )
        btn_editar.bind(on_release=lambda x: self.callback_editar(self.producto))

        self.add_widget(box_info)
        self.add_widget(btn_editar)

    def actualizar_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            for child in self.children:
                if child.collide_point(*touch.pos) and isinstance(child, Button):
                    return super().on_touch_down(touch)
            self.callback_agregar(self.producto)
            return True
        return super().on_touch_down(touch)

class PuntoDeVenta(BoxLayout):
    def __init__(self, **kwargs):
        # DISEÑO HORIZONTAL: Catálogo a la izquierda, Ticket a la derecha
        super().__init__(orientation='horizontal', padding=10, spacing=10, **kwargs)
        self.carrito = []
        self.total = 0.0

        self.conn = sqlite3.connect("ruta.db")
        self.cursor = self.conn.cursor()
        
        self.folio_actual = self.obtener_siguiente_folio()

        # PANEL IZQUIERDO: CATÁLOGO (55% del ancho)
        seccion_catalogo = BoxLayout(orientation='vertical', size_hint=(0.55, 1), spacing=8)
        
        header_cat = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=6)
        lbl_titulo = Label(text="Catálogo", font_size='16sp', bold=True, color=(0.1, 0.15, 0.2, 1), halign='left', valign='middle')
        lbl_titulo.bind(size=lbl_titulo.setter('text_size'))
        
        btn_nuevo_prod = Button(
            text="+ Prod", 
            size_hint_x=None,
            width=75,
            background_normal='', 
            background_color=(0.0, 0.5, 0.9, 1), 
            bold=True,
            font_size='12sp'
        )
        btn_nuevo_prod.bind(on_release=self.modal_agregar_producto)
        
        header_cat.add_widget(lbl_titulo)
        header_cat.add_widget(btn_nuevo_prod)
        seccion_catalogo.add_widget(header_cat)
        
        self.scroll_cat = ScrollView(size_hint=(1, 1))
        self.grid_cat = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.grid_cat.bind(minimum_height=self.grid_cat.setter('height'))

        self.scroll_cat.add_widget(self.grid_cat)
        seccion_catalogo.add_widget(self.scroll_cat)

        # PANEL DERECHO: TICKET Y CLIENTE (45% del ancho)
        seccion_ticket = BoxLayout(orientation='vertical', size_hint=(0.45, 1), spacing=8)
        
        panel_derecho = BoxLayout(orientation='vertical', padding=10, spacing=8)
        with panel_derecho.canvas.before:
            Color(1, 1, 1, 1)
            self.rect_panel = RoundedRectangle(pos=panel_derecho.pos, size=panel_derecho.size, radius=[12])
        panel_derecho.bind(pos=self._actualizar_panel, size=self._actualizar_panel)

        self.lbl_folio = Label(
            text=f"[b]Folio #{self.folio_actual:04d}[/b]",
            markup=True,
            font_size='14sp',
            color=(0.1, 0.5, 0.8, 1),
            size_hint_y=None,
            height=25,
            halign='left',
            valign='middle'
        )
        self.lbl_folio.bind(size=self.lbl_folio.setter('text_size'))
        panel_derecho.add_widget(self.lbl_folio)

        header_cliente = BoxLayout(orientation='horizontal', size_hint_y=None, height=32, spacing=4)
        lbl_cli = Label(text="Cliente:", bold=True, color=(0.2, 0.25, 0.3, 1), font_size='12sp', halign='left', valign='middle')
        lbl_cli.bind(size=lbl_cli.setter('text_size'))
        
        btn_nuevo_cliente = Button(
            text="+ Cte", 
            size_hint_x=None,
            width=65,
            background_normal='', 
            background_color=(0.0, 0.5, 0.9, 1),
            bold=True,
            font_size='11sp'
        )
        btn_nuevo_cliente.bind(on_release=self.modal_agregar_cliente)
        header_cliente.add_widget(lbl_cli)
        header_cliente.add_widget(btn_nuevo_cliente)
        panel_derecho.add_widget(header_cliente)

        self.spinner_clientes = Spinner(
            text="Seleccionar", 
            size_hint_y=None,
            height=35,
            background_normal='',
            background_color=(0.92, 0.94, 0.96, 1),
            color=(0.1, 0.1, 0.1, 1),
            font_size='12sp'
        )
        panel_derecho.add_widget(self.spinner_clientes)

        lbl_resumen = Label(text="Resumen:", bold=True, color=(0.2, 0.25, 0.3, 1), size_hint_y=None, height=20, halign='left', font_size='12sp')
        lbl_resumen.bind(size=lbl_resumen.setter('text_size'))
        panel_derecho.add_widget(lbl_resumen)
        
        self.scroll_ticket = ScrollView(size_hint=(1, 1))
        self.grid_ticket = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.grid_ticket.bind(minimum_height=self.grid_ticket.setter('height'))
        self.scroll_ticket.add_widget(self.grid_ticket)
        panel_derecho.add_widget(self.scroll_ticket)

        self.lbl_total = Label(
            text="Total: $0.00", 
            font_size='16sp', 
            bold=True, 
            color=(0.0, 0.6, 0.4, 1), 
            size_hint_y=None,
            height=28,
            halign='right',
            valign='middle'
        )
        self.lbl_total.bind(size=self.lbl_total.setter('text_size'))
        panel_derecho.add_widget(self.lbl_total)

        btn_imprimir = Button(
            text="IMPRIMIR", 
            size_hint_y=None,
            height=40,
            background_normal='', 
            background_color=(0.0, 0.7, 0.45, 1), 
            bold=True,
            font_size='14sp'
        )
        btn_imprimir.bind(on_release=self.generar_ticket)
        panel_derecho.add_widget(btn_imprimir)

        seccion_ticket.add_widget(panel_derecho)

        self.add_widget(seccion_catalogo)
        self.add_widget(seccion_ticket)

        self.cargar_productos()
        self.cargar_clientes()
        self.actualizar_vista()

    def _actualizar_panel(self, instance, value):
        self.rect_panel.pos = instance.pos
        self.rect_panel.size = instance.size

    def obtener_siguiente_folio(self):
        conn = sqlite3.connect("ruta.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(folio) FROM ventas")
        res = cursor.fetchone()[0]
        conn.close()
        return (res or 0) + 1

    def cargar_productos(self):
        self.grid_cat.clear_widgets()
        self.cursor.execute("SELECT id, nombre, precio FROM productos")
        productos = self.cursor.fetchall()
        for prod in productos:
            prod_dict = {"id": prod[0], "nombre": prod[1], "precio": prod[2]}
            tarjeta = TarjetaProducto(prod_dict, self.agregar_producto, self.modal_editar_producto)
            self.grid_cat.add_widget(tarjeta)

    def cargar_clientes(self):
        self.cursor.execute("SELECT nombre_tienda FROM clientes")
        lista_clientes = [row[0] for row in self.cursor.fetchall()]
        self.spinner_clientes.values = tuple(lista_clientes)
        if lista_clientes:
            self.spinner_clientes.text = lista_clientes[0]

    def modal_agregar_producto(self, instance):
        box = BoxLayout(orientation='vertical', padding=15, spacing=12)
        input_nombre = TextInput(hint_text="Nombre del producto", multiline=False, size_hint_y=0.25)
        input_precio = TextInput(hint_text="Precio (ej. 12.50)", multiline=False, input_filter='float', size_hint_y=0.25)
        btn_guardar = Button(text="Guardar Producto", background_normal='', background_color=(0.0, 0.7, 0.45, 1), bold=True, size_hint_y=0.3)

        box.add_widget(Label(text="Nuevo Producto", bold=True, font_size='18sp'))
        box.add_widget(input_nombre)
        box.add_widget(input_precio)
        box.add_widget(btn_guardar)

        popup = Popup(title="Alta de Producto", content=box, size_hint=(0.85, 0.5))

        def guardar(x):
            if input_nombre.text and input_precio.text:
                self.cursor.execute("INSERT INTO productos (nombre, precio) VALUES (?, ?)", 
                                    (input_nombre.text, float(input_precio.text)))
                self.conn.commit()
                self.cargar_productos()
                popup.dismiss()

        btn_guardar.bind(on_release=guardar)
        popup.open()

    def modal_editar_producto(self, producto):
        box = BoxLayout(orientation='vertical', padding=15, spacing=12)
        input_nombre = TextInput(text=producto['nombre'], multiline=False, size_hint_y=0.25)
        input_precio = TextInput(text=str(producto['precio']), multiline=False, input_filter='float', size_hint_y=0.25)
        btn_guardar = Button(text="Actualizar", background_normal='', background_color=(0.9, 0.5, 0.1, 1), bold=True, size_hint_y=0.3)

        box.add_widget(Label(text=f"Editar (ID: {producto['id']})", bold=True, font_size='18sp'))
        box.add_widget(input_nombre)
        box.add_widget(input_precio)
        box.add_widget(btn_guardar)

        popup = Popup(title="Modificar Producto", content=box, size_hint=(0.85, 0.5))

        def actualizar(x):
            if input_nombre.text and input_precio.text:
                self.cursor.execute("UPDATE productos SET nombre = ?, precio = ? WHERE id = ?", 
                                    (input_nombre.text, float(input_precio.text), producto['id']))
                self.conn.commit()
                self.cargar_productos()
                popup.dismiss()

        btn_guardar.bind(on_release=actualizar)
        popup.open()

    def modal_agregar_cliente(self, instance):
        box = BoxLayout(orientation='vertical', padding=15, spacing=12)
        input_nombre = TextInput(hint_text="Nombre de la tienda/cliente", multiline=False, size_hint_y=0.3)
        btn_guardar = Button(text="Guardar Cliente", background_normal='', background_color=(0.0, 0.7, 0.45, 1), bold=True, size_hint_y=0.3)

        box.add_widget(Label(text="Nuevo Cliente", bold=True, font_size='18sp'))
        box.add_widget(input_nombre)
        box.add_widget(btn_guardar)

        popup = Popup(title="Alta de Cliente", content=box, size_hint=(0.85, 0.45))

        def guardar(x):
            if input_nombre.text:
                self.cursor.execute("INSERT INTO clientes (nombre_tienda) VALUES (?)", (input_nombre.text,))
                self.conn.commit()
                self.cargar_clientes()
                self.spinner_clientes.text = input_nombre.text
                popup.dismiss()

        btn_guardar.bind(on_release=guardar)
        popup.open()

    def agregar_producto(self, producto):
        self.carrito.append(producto)
        self.actualizar_vista()

    def eliminar_producto_carrito(self, indice, item):
        if 0 <= indice < len(self.carrito):
            self.carrito.pop(indice)
            self.actualizar_vista()

    def actualizar_vista(self):
        self.grid_ticket.clear_widgets()
        self.total = 0.0

        if not self.carrito:
            lbl_vacio = Label(
                text="Carrito vacío", 
                color=(0.3, 0.35, 0.4, 1),
                font_size='12sp',
                size_hint_y=None,
                height=30
            )
            self.grid_ticket.add_widget(lbl_vacio)
        else:
            for idx, item in enumerate(self.carrito):
                self.total += item['precio']
                renglon = RenglonCarrito(item, idx, self.eliminar_producto_carrito)
                self.grid_ticket.add_widget(renglon)

        self.lbl_total.text = f"Total: ${self.total:.2f}"

    def enviar_a_impresora_bluetooth(self, texto_ticket):
        # 1. SI ESTAMOS EN LA PC DE DESARROLLO (Windows, Mac, Linux)
        if platform != 'android':
            print("--- MODO PC: SIMULANDO IMPRESIÓN ---")
            print(texto_ticket)
            print("------------------------------------")
            return

        # 2. SI ESTAMOS EN EL CELULAR ANDROID (Pyjnius)
        try:
            from jnius import autoclass
            
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            UUID = autoclass('java.util.UUID')
            
            adapter = BluetoothAdapter.getDefaultAdapter()
            
            if not adapter or not adapter.isEnabled():
                print("Error: Bluetooth apagado o no disponible en el celular.")
                return

            # Busca entre los dispositivos que YA vinculaste en los ajustes de tu celular
            dispositivos_emparejados = adapter.getBondedDevices().toArray()
            impresora = None
            
            # Buscará algo que suene a impresora ("printer", "pos", "mtp")
            for device in dispositivos_emparejados:
                nombre_b = device.getName().lower()
                if "printer" in nombre_b or "pos" in nombre_b or "mtp" in nombre_b:
                    impresora = device
                    break
            
            # Si no encuentra por nombre, intenta tomar el primer dispositivo Bluetooth conectado
            if not impresora and len(dispositivos_emparejados) > 0:
                impresora = dispositivos_emparejados[0]

            if impresora:
                print(f"Conectando a impresora: {impresora.getName()}")
                # UUID genérico para impresoras térmicas SPP (Serial Port Profile)
                uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
                
                socket = impresora.createRfcommSocketToServiceRecord(uuid)
                adapter.cancelDiscovery()  # Obligatorio antes de conectar para evitar errores
                socket.connect()
                
                output_stream = socket.getOutputStream()
                
                # Convertimos el texto a bytes y lo mandamos
                output_stream.write(texto_ticket.encode('cp850', errors='replace'))
                
                # Un par de saltos de línea extra para que el papel salga bien
                output_stream.write(b"\n\n\n")
                
                output_stream.flush()
                socket.close()
                print("¡Impresión enviada con éxito desde Android!")
            else:
                print("Error: No se detectó ninguna impresora emparejada en los ajustes de Android.")
                
        except Exception as e:
            print(f"Error grave al intentar imprimir en Android: {str(e)}")

    def generar_ticket(self, instance):
        if not self.carrito:
            return

        cliente = self.spinner_clientes.text
        tipo_pago = "Contado"
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        self.cursor.execute(
            "INSERT INTO ventas (cliente, metodo_pago, total, fecha) VALUES (?, ?, ?, ?)",
            (cliente, tipo_pago, self.total, fecha)
        )
        self.conn.commit()

        ticket_texto = f"====== TICKET DE VENTA ======\n"
        ticket_texto += f"Folio #: {self.folio_actual:04d}\n"
        ticket_texto += f"Fecha: {fecha}\n"
        ticket_texto += f"Cliente: {cliente}\n"
        ticket_texto += f"Pago: {tipo_pago}\n"
        ticket_texto += f"------------------------------------\n"
        for item in self.carrito:
            ticket_texto += f"{item['nombre'][:18]:<18} ${item['precio']:>6.2f}\n"
        ticket_texto += f"------------------------------------\n"
        ticket_texto += f"TOTAL:              ${self.total:>6.2f}\n"
        ticket_texto += f"============================\n"

        # Llamamos a la función que usa Pyjnius
        self.enviar_a_impresora_bluetooth(ticket_texto)

        popup = Popup(
            title="Ticket Generado",
            content=Label(text=ticket_texto, font_size='13sp'),
            size_hint=(0.85, 0.8)
        )
        popup.open()

        self.carrito = []
        self.actualizar_vista()

        self.folio_actual = self.obtener_siguiente_folio()
        self.lbl_folio.text = f"[b]Folio #{self.folio_actual:04d}[/b]"

class MiAppPOS(App):
    def build(self):
        # Permisos nativos requeridos al abrir la app
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
                Permission.BLUETOOTH_SCAN,
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_ADMIN,
                Permission.BLUETOOTH
            ])
            
        self.title = "Sistema POS - Ruta de Distribución"
        inicializar_db()
        return PuntoDeVenta()

if __name__ == '__main__':
    MiAppPOS().run()
