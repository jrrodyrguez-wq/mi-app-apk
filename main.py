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

# --- Lógica de Base de Datos ---
def inicializar_db():
    conn = sqlite3.connect("ruta.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, precio REAL NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_tienda TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (folio INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, total REAL, fecha TEXT)''')
    
    # Datos iniciales si está vacía
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO productos (nombre, precio) VALUES (?, ?)", [
            ("Tutsi Pop C/24", 68.00), ("Mazapan C/30", 110.00), ("Pelon Pelo Rico C/12", 85.00),
            ("Galletas Marias 170g", 18.50), ("Aceite 1L", 42.00), ("Harina 1kl", 75.00)
        ])
    conn.commit()
    conn.close()

# --- Componentes de la Interfaz ---
class RenglonCarrito(BoxLayout):
    def __init__(self, item, indice, callback_eliminar, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=40, spacing=5, **kwargs)
        self.add_widget(Label(text=f"{item['nombre']} (${item['precio']:.2f})", font_size='12sp', halign='left'))
        btn_borrar = Button(text="X", size_hint_x=0.2, background_color=(0.9, 0.2, 0.2, 1))
        btn_borrar.bind(on_release=lambda x: callback_eliminar(indice))
        self.add_widget(btn_borrar)

class PuntoDeVenta(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', padding=10, spacing=10, **kwargs)
        self.carrito = []
        self.inicializar_ui()
        self.cargar_productos()

    def inicializar_ui(self):
        # Panel Izquierdo: Catálogo
        self.grid_cat = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid_cat.bind(minimum_height=self.grid_cat.setter('height'))
        scroll_cat = ScrollView(size_hint=(0.6, 1))
        scroll_cat.add_widget(self.grid_cat)
        self.add_widget(scroll_cat)

        # Panel Derecho: Ticket
        panel_der = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=10)
        self.grid_ticket = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.grid_ticket.bind(minimum_height=self.grid_ticket.setter('height'))
        panel_der.add_widget(ScrollView(size_hint=(1, 0.7)))
        panel_der.children[0].add_widget(self.grid_ticket)
        
        btn_imprimir = Button(text="IMPRIMIR", size_hint_y=0.15, background_color=(0, 0.7, 0.3, 1))
        btn_imprimir.bind(on_release=self.generar_ticket)
        panel_der.add_widget(btn_imprimir)
        self.add_widget(panel_der)

    def cargar_productos(self):
        conn = sqlite3.connect("ruta.db")
        prods = conn.execute("SELECT id, nombre, precio FROM productos").fetchall()
        for p in prods:
            btn = Button(text=f"{p[1]} - ${p[2]}", size_hint_y=None, height=50)
            btn.bind(on_release=lambda x, p=p: self.agregar_al_carrito({"id":p[0], "nombre":p[1], "precio":p[2]}))
            self.grid_cat.add_widget(btn)
        conn.close()

    def agregar_al_carrito(self, prod):
        self.carrito.append(prod)
        self.actualizar_ticket()

    def eliminar_del_carrito(self, indice):
        self.carrito.pop(indice)
        self.actualizar_ticket()

    def actualizar_ticket(self):
        self.grid_ticket.clear_widgets()
        for i, item in enumerate(self.carrito):
            self.grid_ticket.add_widget(RenglonCarrito(item, i, self.eliminar_del_carrito))

    def generar_ticket(self, *args):
        texto = "TICKET DE VENTA\n" + "-"*20 + "\n"
        total = 0
        for item in self.carrito:
            texto += f"{item['nombre']} ${item['precio']}\n"
            total += item['precio']
        texto += f"TOTAL: ${total}\n"
        
        if platform == 'android':
            self.enviar_bluetooth(texto)
        else:
            print(texto)

    def enviar_bluetooth(self, texto):
        from jnius import autoclass
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        UUID = autoclass('java.util.UUID')
        adapter = BluetoothAdapter.getDefaultAdapter()
        dispositivos = adapter.getBondedDevices().toArray()
        
        for dev in dispositivos:
            if "printer" in dev.getName().lower():
                socket = dev.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                socket.connect()
                socket.getOutputStream().write(texto.encode('utf-8'))
                socket.close()
                break

class MiApp(App):
    def build(self):
        inicializar_db()
        return PuntoDeVenta()

if __name__ == '__main__':
    MiApp().run()
