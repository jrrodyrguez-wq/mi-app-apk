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
from kivy.clock import Clock
from kivy.utils import platform
import sqlite3
import datetime
import socket

# Solicitar permisos automáticamente si corre en Android (Bluetooth y Ubicación)
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.ACCESS_FINE_LOCATION,
        Permission.ACCESS_COARSE_LOCATION,
        Permission.BLUETOOTH_SCAN,
        Permission.BLUETOOTH_CONNECT
    ])

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
        super().__init__(orientation='horizontal', size_hint_y=None, height=42, **kwargs)
        self.item = item
        self.indice = indice
        self.callback_eliminar = callback_eliminar
        self._touch_ev = None

        lbl_item = Label(
            text=f"• {item['nombre']}  —  ${item['precio']:.2f}",
            color=(0.2, 0.2, 0.2, 1),
            font_size='15sp',
            halign='left',
            valign='middle'
        )
        lbl_item.bind(size=lbl_item.setter('text_size'))
        self.add_widget(lbl_item)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_ev = Clock.schedule_once(self.activar_eliminacion, 0.6)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._touch_ev:
            self._touch_ev.cancel()
        return super().on_touch_up(touch)

    def activar_eliminacion(self, dt):
        self.callback_eliminar(self.indice, self.item)

class TarjetaProducto(BoxLayout):
    def __init__(self, producto, callback_agregar, callback_editar, **kwargs):
        super().__init__(orientation='horizontal', padding=12, spacing=10, **kwargs)
        self.size_hint_y = None
        self.height = 90
        self.producto = producto
        self.callback_agregar = callback_agregar
        self.callback_editar = callback_editar

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.actualizar_canvas, size=self.actualizar_canvas)

        box_info = BoxLayout(orientation='vertical', spacing=4)
        lbl_nombre = Label(
            text=f"[b]{producto['nombre']}[/b]", 
            markup=True, 
            color=(0.15, 0.2, 0.25, 1), 
            font_size='16sp',
            halign='left', 
            valign='middle'
        )
        lbl_nombre.bind(size=lbl_nombre.setter('text_size'))

        lbl_precio = Label(
            text=f"${producto['precio']:.2f}", 
            color=(0.0, 0.6, 0.4, 1), 
            bold=True, 
            font_size='17sp',
            halign='left', 
            valign='middle'
        )
        lbl_precio.bind(size=lbl_precio.setter('text_size'))

        box_info.add_widget(lbl_nombre)
        box_info.add_widget(lbl_precio)

        btn_editar = Button(
            text="Editar",
            size_hint=(0.28, 0.8),
            pos_hint={'center_y': 0.5},
            background_normal='',
            background_color=(0.9, 0.5, 0.1, 1),
            bold=True,
            font_size='14sp'
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
        super().__init__(orientation='horizontal', padding=15, spacing=18, **kwargs)
        self.carrito = []
        self.total = 0.0

        self.conn = sqlite3.connect("ruta.db")
        self.cursor = self.conn.cursor()
        
        self.folio_actual = self.obtener_siguiente_folio()

        # PANEL IZQUIERDO: CATÁLOGO
        seccion_catalogo = BoxLayout(orientation='vertical', size_hint=(0.55, 1), spacing=12)
        
        header_cat = BoxLayout(orientation='horizontal', size_hint_y=0.09, spacing=10)
        lbl_titulo = Label(text="Catálogo de Productos", font_size='21sp', bold=True, color=(0.1, 0.15, 0.2, 1), halign='left')
        lbl_titulo.bind(size=lbl_titulo.setter('text_size'))
        
        btn_nuevo_prod = Button(
            text="+ Producto", 
            size_hint_x=0.38, 
            background_normal='', 
            background_color=(0.0, 0.5, 0.9, 1), 
            bold=True,
            font_size='14sp'
        )
        btn_nuevo_prod.bind(on_release=self.modal_agregar_producto)
        
        header_cat.add_widget(lbl_titulo)
        header_cat.add_widget(btn_nuevo_prod)
        seccion_catalogo.add_widget(header_cat)
        
        self.scroll_cat = ScrollView(size_hint=(1, 0.91))
        self.grid_cat = GridLayout(cols=1, spacing=12, size_hint_y=None)
        self.grid_cat.bind(minimum_height=self.grid_cat.setter('height'))

        self.scroll_cat.add_widget(self.grid_cat)
        seccion_catalogo.add_widget(self.scroll_cat)

        # PANEL DERECHO: TICKET Y CLIENTE
        seccion_ticket = BoxLayout(orientation='vertical', size_hint=(0.45, 1), spacing=10)
        
        panel_derecho = BoxLayout(orientation='vertical', padding=18, spacing=12)
        with panel_derecho.canvas.before:
            Color(1, 1, 1, 1)
            self.rect_panel = RoundedRectangle(pos=panel_derecho.pos, size=panel_derecho.size, radius=[14])
        panel_derecho.bind(pos=self._actualizar_panel, size=self._actualizar_panel)

        self.lbl_folio = Label(
            text=f"[b]Nota / Folio #: {self.folio_actual:04d}[/b]",
            markup=True,
            font_size='18sp',
            color=(0.1, 0.5, 0.8, 1),
            size_hint_y=0.06,
            halign='left'
        )
        self.lbl_folio.bind(size=self.lbl_folio.setter('text_size'))
        panel_derecho.add_widget(self.lbl_folio)

        header_cliente = BoxLayout(orientation='horizontal', size_hint_y=0.07, spacing=8)
        lbl_cli = Label(text="Cliente / Tienda:", bold=True, color=(0.2, 0.25, 0.3, 1), halign='left', font_size='14sp')
        lbl_cli.bind(size=lbl_cli.setter('text_size'))
        
        btn_nuevo_cliente = Button(
            text="+ Cliente", 
            size_hint_x=0.4, 
            background_normal='', 
            background_color=(0.0, 0.5, 0.9, 1),
            bold=True,
            font_size='13sp'
        )
        btn_nuevo_cliente.bind(on_release=self.modal_agregar_cliente)
        header_cliente.add_widget(lbl_cli)
        header_cliente.add_widget(btn_nuevo_cliente)
        panel_derecho.add_widget(header_cliente)

        self.spinner_clientes = Spinner(
            text="Seleccionar", 
            size_hint_y=0.08,
            background_normal='',
            background_color=(0.92, 0.94, 0.96, 1),
            color=(0.1, 0.1, 0.1, 1),
            font_size='14sp'
        )
        panel_derecho.add_widget(self.spinner_clientes)

        lbl_pago = Label(text="Método de Pago:", bold=True, color=(0.2, 0.25, 0.3, 1), size_hint_y=0.05, halign='left', font_size='14sp')
        lbl_pago.bind(size=lbl_pago.setter('text_size'))
        panel_derecho.add_widget(lbl_pago)

        self.spinner_pago = Spinner(
            text="Contado",
            values=("Contado", "Crédito / Fiado"),
            size_hint_y=0.08,
            background_normal='',
            background_color=(0.92, 0.94, 0.96, 1),
            color=(0.1, 0.1, 0.1, 1),
            font_size='14sp'
        )
        panel_derecho.add_widget(self.spinner_pago)

        panel_derecho.add_widget(Label(text="Resumen (Mantén presionado para borrar):", bold=True, color=(0.2, 0.25, 0.3, 1), size_hint_y=0.05, halign='left', font_size='13sp'))
        
        self.scroll_ticket = ScrollView(size_hint=(1, 0.34))
        self.grid_ticket = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.grid_ticket.bind(minimum_height=self.grid_ticket.setter('height'))
        self.scroll_ticket.add_widget(self.grid_ticket)
        panel_derecho.add_widget(self.scroll_ticket)

        self.lbl_total = Label(
            text="Total: $0.00", 
            font_size='22sp', 
            bold=True, 
            color=(0.0, 0.6, 0.4, 1), 
            size_hint_y=0.08,
            halign='right'
        )
        self.lbl_total.bind(size=self.lbl_total.setter('text_size'))
        panel_derecho.add_widget(self.lbl_total)

        btn_imprimir = Button(
            text="GENERAR TICKET", 
            size_hint_y=0.13, 
            background_normal='', 
            background_color=(0.0, 0.7, 0.45, 1), 
            bold=True,
            font_size='16sp'
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

        popup = Popup(title="Alta de Producto", content=box, size_hint=(0.7, 0.5))

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
        btn_guardar = Button(text="Actualizar Producto", background_normal='', background_color=(0.9, 0.5, 0.1, 1), bold=True, size_hint_y=0.3)

        box.add_widget(Label(text=f"Modificar Producto (ID: {producto['id']})", bold=True, font_size='18sp'))
        box.add_widget(input_nombre)
        box.add_widget(input_precio)
        box.add_widget(btn_guardar)

        popup = Popup(title="Editar Producto / Precio", content=box, size_hint=(0.7, 0.5))

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

        popup = Popup(title="Alta de Cliente", content=box, size_hint=(0.7, 0.45))

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

    def modal_confirmar_eliminar(self, indice, item):
        box = BoxLayout(orientation='vertical', padding=15, spacing=12)
        lbl_msg = Label(
            text=f"¿Quitar [b]{item['nombre']}[/b] del carrito?",
            markup=True,
            font_size='16sp',
            halign='center'
        )
        btn_borrar = Button(
            text="Sí, Eliminar",
            background_normal='',
            background_color=(0.9, 0.2, 0.2, 1),
            bold=True,
            size_hint_y=0.4
        )

        box.add_widget(lbl_msg)
        box.add_widget(btn_borrar)

        popup = Popup(title="Eliminar Producto", content=box, size_hint=(0.7, 0.4))

        def borrar(x):
            self.carrito.pop(indice)
            self.actualizar_vista()
            popup.dismiss()

        btn_borrar.bind(on_release=borrar)
        popup.open()

    def actualizar_vista(self):
        self.grid_ticket.clear_widgets()
        self.total = 0.0

        if not self.carrito:
            lbl_vacio = Label(
                text="Sin productos en el carrito", 
                color=(0.3, 0.35, 0.4, 1),
                font_size='14sp',
                size_hint_y=None,
                height=35
            )
            self.grid_ticket.add_widget(lbl_vacio)
        else:
            for idx, item in enumerate(self.carrito):
                self.total += item['precio']
                renglon = RenglonCarrito(item, idx, self.modal_confirmar_eliminar)
                self.grid_ticket.add_widget(renglon)

        self.lbl_total.text = f"Total: ${self.total:.2f}"

    def enviar_a_impresora_bluetooth(self, texto_ticket):
        # CAMBIA 'XX:XX:XX:XX:XX:XX' POR LA MAC REAL DE TU IMPRESORA MP210
        mac_impressora = 'XX:XX:XX:XX:XX:XX' 
        port = 1
        
        try:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            s.connect((mac_impressora, port))
            s.send(texto_ticket.encode('utf-8'))
            s.send(b"\n\n\x1d\x56\x42\x00") 
            s.close()
            print("Ticket enviado correctamente.")
        except Exception as e:
            print(f"Error al conectar con la impresora Bluetooth: {e}")

    def generar_ticket(self, instance):
        if not self.carrito:
            return

        cliente = self.spinner_clientes.text
        tipo_pago = self.spinner_pago.text
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
            ticket_texto += f"{item['nombre'][:20]:<20} ${item['precio']:>6.2f}\n"
        ticket_texto += f"------------------------------------\n"
        ticket_texto += f"TOTAL:              ${self.total:>6.2f}\n"
        ticket_texto += f"============================\n\n\n"

        self.enviar_a_impresora_bluetooth(ticket_texto)

        popup = Popup(
            title="Ticket Generado",
            content=Label(text=ticket_texto, font_size='14sp'),
            size_hint=(0.75, 0.75)
        )
        popup.open()

        self.carrito = []
        self.actualizar_vista()

        self.folio_actual = self.obtener_siguiente_folio()
        self.lbl_folio.text = f"[b]Nota / Folio #: {self.folio_actual:04d}[/b]"

class MiAppPOS(App):
    def build(self):
        self.title = "Sistema POS - Ruta de Distribución"
        inicializar_db()
        return PuntoDeVenta()

if __name__ == '__main__':
    MiAppPOS().run()
