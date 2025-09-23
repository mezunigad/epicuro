from flask import Flask, render_template, request, redirect, url_for, g, jsonify, flash
import sqlite3
import datetime
import os
import json
from decimal import Decimal
#from zoneinfo import ZoneInfo  # Para Python 3.9+
from pytz import timezone

# Si tienes Python < 3.9, usa: from pytz import timezone

app = Flask(__name__)
app.secret_key = 'epicuro_secret_key_2024'

# Configurar zona horaria de Chile
#CHILE_TZ = ZoneInfo("America/Santiago")  # Para Python 3.9+
CHILE_TZ = timezone('America/Santiago') # Para Python < 3.9 usar: 

def get_chile_now():
    """Obtener fecha/hora actual en zona horaria de Chile"""
    return datetime.datetime.now(CHILE_TZ)

def get_chile_today():
    """Obtener fecha actual en Chile"""
    return get_chile_now().date()

def get_chile_timestamp():
    """Obtener timestamp en formato SQLite para Chile"""
    return get_chile_now().strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('dateformat')
def dateformat(value, format='%d/%m/%Y'):
    """Filtro para formatear fechas que pueden ser strings o datetime objects"""
    if not value:
        return 'N/A'
    
    if isinstance(value, str):
        try:
            # Intentar convertir string a datetime
            if 'T' in value:
                # Formato ISO con T: 2025-09-16T10:30:00
                dt = datetime.datetime.fromisoformat(value.replace('T', ' '))
            else:
                # Formato normal: 2025-09-16 10:30:00
                dt = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            
            # Si la fecha viene de SQLite (sin zona horaria), convertir a Chile
            if dt.tzinfo is None:
                # Asumir que es UTC y convertir a Chile
                dt = dt.replace(tzinfo=datetime.timezone.utc)
                dt = dt.astimezone(CHILE_TZ)
            
            return dt.strftime(format)
        except:
            # Si falla la conversión, devolver solo la fecha (primeros 10 caracteres)
            return value[:10] if len(value) >= 10 else value
    else:
        # Si ya es datetime, convertir a zona horaria de Chile si es necesario
        if hasattr(value, 'tzinfo'):
            if value.tzinfo is None:
                # Sin zona horaria, asumir UTC
                value = value.replace(tzinfo=datetime.timezone.utc)
            value = value.astimezone(CHILE_TZ)
        return value.strftime(format)

@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convertir saltos de línea en <br> tags"""
    if not text:
        return ''
    return text.replace('\n', '<br>')

# Configuración de la base de datos
DATABASE = 'data/sandwich.db'

def get_db():
    """Obtener conexión a la base de datos"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA table_info(categories)")
    return g.db

def close_db(e=None):
    """Cerrar conexión a la base de datos"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Inicializar la base de datos con estructura limpia"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    # Tabla de categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            color TEXT DEFAULT '#3498db',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    
    # Tabla de productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category_id INTEGER,
            available INTEGER DEFAULT 1,
            image TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    # Tabla de órdenes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            customer_phone TEXT,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT DEFAULT 'efectivo',
            notes TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')

        # Agregar columna order_type si no existe
    try:
        cursor.execute('ALTER TABLE orders ADD COLUMN order_type TEXT DEFAULT "dine_in"')
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    
    # Tabla de detalles de orden
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    # Tablas de inventario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            tax_id TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            unit TEXT DEFAULT 'gr',
            current_stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            max_stock REAL DEFAULT 0,
            unit_cost REAL DEFAULT 0,
            preferred_supplier_id INTEGER,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (preferred_supplier_id) REFERENCES suppliers (id)
        )
    ''')

    # Tabla de recetas actualizada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            servings INTEGER DEFAULT 1,
            prep_time INTEGER,
            cook_time INTEGER,
            instructions TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL NOT NULL,
            unit TEXT,
            notes TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            purchase_date DATE,
            expected_date DATE,
            received_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            ingredient_id INTEGER,
            quantity REAL NOT NULL,
            unit TEXT,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            received_quantity REAL DEFAULT 0,
            FOREIGN KEY (purchase_id) REFERENCES purchases (id),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_id INTEGER,
            movement_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_cost REAL DEFAULT 0,
            reference_type TEXT,
            reference_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
        )
    ''')

    # Tabla de grupos de variaciones (ej: "Proteínas", "Tamaños", "Extras")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS variation_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            description TEXT,
            required INTEGER DEFAULT 0,
            multiple_selection INTEGER DEFAULT 0,
            min_selections INTEGER DEFAULT 1,
            max_selections INTEGER,
            sort_order INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    # Tabla de opciones de variación (ej: "Pollo", "Carne", "Vegetariano")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS variation_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variation_group_id INTEGER,
            name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            price_modifier REAL DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id)
        )
    ''')

    # Tabla que conecta productos con grupos de variaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            variation_group_id INTEGER,
            required INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id)
        )
    ''')

    # Tabla para guardar variaciones seleccionadas en cada item de orden
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_item_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id INTEGER,
            variation_option_id INTEGER,
            price_modifier REAL DEFAULT 0,
            FOREIGN KEY (order_item_id) REFERENCES order_items (id),
            FOREIGN KEY (variation_option_id) REFERENCES variation_options (id)
        )
    ''')
    
    # Solo crear estructuras básicas, sin datos iniciales
    db.commit()
    db.close()

# ===== FUNCIONES AUXILIARES =====

def get_all_ingredients(active_only=False):
    """Obtener todos los ingredientes"""
    db = get_db()
    
    query = "SELECT * FROM ingredients"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY name"
    
    ingredients = db.execute(query).fetchall()
    return ingredients

def get_ingredient_by_id(ingredient_id):
    """Función auxiliar para obtener un ingrediente por ID"""
    db = get_db()
    return db.execute('SELECT * FROM ingredients WHERE id = ?', (ingredient_id,)).fetchone()

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_appcontext
def close_db(error):
    """Cerrar conexión a la base de datos"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ===== RUTAS PRINCIPALES =====

@app.route('/')
def index():
    """Dashboard principal con estadísticas"""
    db = get_db()
    
    # Estadísticas del día usando fecha local
    today = get_chile_today()
    stats = {
        'orders_today': db.execute(
            'SELECT COUNT(*) FROM orders WHERE date(created_at) = date(?)', 
            (today,)
        ).fetchone()[0],
        'revenue_today': db.execute(
            'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE date(created_at) = date(?)', 
            (today,)
        ).fetchone()[0],
        'total_orders': db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],
        'total_products': db.execute('SELECT COUNT(*) FROM products WHERE available = 1').fetchone()[0],
        'total_categories': db.execute('SELECT COUNT(*) FROM categories WHERE active = 1').fetchone()[0]
    }
    
    # Órdenes recientes
    recent_orders = db.execute('''
        SELECT id, order_number, customer_name, total_amount, status, created_at
        FROM orders 
        ORDER BY created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    return render_template('index.html', stats=stats, recent_orders=recent_orders)

@app.route('/orders/new')
def new_order():
    """Página para crear nueva comanda"""
    db = get_db()
    
    # Obtener categorías activas
    categories = db.execute('''
        SELECT * FROM categories 
        WHERE active = 1 
        ORDER BY name
    ''').fetchall()
    
    # Obtener productos por categoría con información de categoría
    products_by_category = {}
    for category in categories:
        products = db.execute('''
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.category_id = ? AND p.available = 1 
            ORDER BY p.name
        ''', (category['id'],)).fetchall()
        products_by_category[category['id']] = products
    
    return render_template('new_order.html', 
                         categories=categories, 
                         products_by_category=products_by_category)

@app.route('/orders/create', methods=['POST'])
def create_order():
    """Crear nueva orden con variaciones y notas"""
    try:
        db = get_db()
        
        # Datos básicos de la orden del formulario
        customer_name = request.form.get('customer_name', '')
        customer_phone = request.form.get('customer_phone', '')
        payment_method = request.form.get('payment_method', 'efectivo')
        notes = request.form.get('notes', '')
        order_type = request.form.get('order_type', 'dine_in')  # Nuevo campo
        
        # Items del carrito enviados como JSON desde el frontend
        cart_items_raw = request.form.get('cart_items', '[]')
        cart_items = json.loads(cart_items_raw)
        
        # Validar que hay productos en el carrito
        if not cart_items:
            flash('No hay productos en el carrito', 'error')
            return redirect(url_for('new_order'))
        
        # Generar número único de orden con timestamp de Chile
        chile_now = get_chile_now()
        order_number = f"ORD-{chile_now.strftime('%Y%m%d%H%M%S')}"
        
        # Calcular totales de la orden
        subtotal = sum(item['quantity'] * item['price'] for item in cart_items)
        discount = 0  # Implementar lógica de descuentos si es necesario
        total_amount = subtotal - discount
        
        # Insertar la orden principal en la base de datos
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO orders (order_number, customer_name, customer_phone, 
                              subtotal, discount, total_amount, payment_method, 
                              notes, order_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_number, customer_name, customer_phone, 
              subtotal, discount, total_amount, payment_method, 
              notes, order_type, get_chile_timestamp()))
        
        order_id = cursor.lastrowid
        
        # Insertar cada producto del carrito
        for item in cart_items:
            # Datos básicos del producto
            product_id = item.get('id')
            product_name = item.get('name', '')
            quantity = item.get('quantity', 1)
            unit_price = item.get('price', 0)
            total_price = quantity * unit_price
            item_notes = item.get('notes', '')  # Notas específicas del producto
            
            # Insertar el item en order_items
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, product_name, 
                                       quantity, unit_price, total_price, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, product_id, product_name, quantity, 
                  unit_price, total_price, item_notes))
            
            # Obtener el ID del item recién insertado
            item_id = cursor.lastrowid
            
            # NUEVA SECCIÓN: Guardar variaciones del producto (proteínas, tamaños, etc.)
            if 'variations' in item and item['variations']:
                for variation in item['variations']:
                    # Cada variación tiene: option_id, price_modifier, name
                    option_id = variation.get('option_id')
                    price_modifier = variation.get('price_modifier', 0)
                    
                    # Solo insertar si tenemos un option_id válido
                    if option_id:
                        cursor.execute('''
                            INSERT INTO order_item_variations (order_item_id, variation_option_id, price_modifier)
                            VALUES (?, ?, ?)
                        ''', (item_id, option_id, price_modifier))
        
        # Confirmar todas las transacciones
        db.commit()
        
        # Mensaje de éxito y redirección
        flash(f'Orden {order_number} creada exitosamente', 'success')
        return redirect(url_for('view_order', order_id=order_id))
        
    except json.JSONDecodeError as e:
        # Error específico al decodificar el JSON del carrito
        db.rollback() if 'db' in locals() else None
        flash(f'Error en los datos del carrito: {str(e)}', 'error')
        return redirect(url_for('new_order'))
        
    except Exception as e:
        # Error general - deshacer cambios y mostrar error
        db.rollback() if 'db' in locals() else None
        flash(f'Error al crear la orden: {str(e)}', 'error')
        return redirect(url_for('new_order'))

@app.route('/orders')
def list_orders():
    """Lista de todas las órdenes"""
    db = get_db()
    
    # Filtros
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    
    query = 'SELECT * FROM orders WHERE 1=1'
    params = []
    
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
    
    if date_filter:
        query += ' AND DATE(created_at) = ?'
        params.append(date_filter)
    
    query += ' ORDER BY created_at DESC'
    
    orders = db.execute(query, params).fetchall()
    
    return render_template('orders_list.html', orders=orders, 
                         status_filter=status_filter, date_filter=date_filter)

@app.route('/orders/<int:order_id>')
def view_order(order_id):
    """Ver detalle de una orden específica"""
    db = get_db()
    
    # Obtener orden
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        flash('Orden no encontrada', 'error')
        return redirect(url_for('list_orders'))
    
    # Obtener items de la orden
    order_items = db.execute('''
        SELECT * FROM order_items 
        WHERE order_id = ? 
        ORDER BY id
    ''', (order_id,)).fetchall()
    
    return render_template('order_detail.html', order=order, order_items=order_items)

@app.route('/orders/<int:order_id>/update_status', methods=['POST'])
def update_order_status(order_id):
    """Actualizar estado de una orden"""
    db = get_db()
    new_status = request.form.get('status')
    
    db.execute('''
        UPDATE orders 
        SET status = ?, updated_at = ?
        WHERE id = ?
    ''', (new_status, get_chile_timestamp(), order_id))
    db.commit()
    
    flash('Estado actualizado correctamente', 'success')
    return redirect(url_for('view_order', order_id=order_id))

# Agregar estas rutas después de tus rutas existentes de órdenes en app.py

@app.route('/orders/<int:order_id>/edit')
def edit_order(order_id):
    """Formulario para editar una orden"""
    db = get_db()
    
    # Obtener orden
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        flash('Orden no encontrada', 'error')
        return redirect(url_for('list_orders'))
    
    # Obtener items de la orden con variaciones
    order_items = db.execute('''
        SELECT oi.*, 
               GROUP_CONCAT(vo.display_name, ', ') as variations
        FROM order_items oi
        LEFT JOIN order_item_variations oiv ON oi.id = oiv.order_item_id
        LEFT JOIN variation_options vo ON oiv.variation_option_id = vo.id
        WHERE oi.order_id = ?
        GROUP BY oi.id
        ORDER BY oi.id
    ''', (order_id,)).fetchall()
    
    # Obtener categorías y productos para el formulario
    categories = db.execute('''
        SELECT * FROM categories 
        WHERE active = 1 
        ORDER BY name
    ''').fetchall()
    
    products_by_category = {}
    for category in categories:
        products = db.execute('''
            SELECT * FROM products 
            WHERE category_id = ? AND available = 1 
            ORDER BY name
        ''', (category['id'],)).fetchall()
        products_by_category[category['id']] = products
    
    return render_template('edit_order.html', 
                         order=order, 
                         order_items=order_items,
                         categories=categories, 
                         products_by_category=products_by_category)

@app.route('/orders/<int:order_id>/update', methods=['POST'])
def update_order(order_id):
    """Actualizar una orden existente"""
    try:
        db = get_db()
        
        # Verificar que la orden existe
        order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            flash('Orden no encontrada', 'error')
            return redirect(url_for('list_orders'))
        
        # Datos de la orden
        customer_name = request.form.get('customer_name', '')
        customer_phone = request.form.get('customer_phone', '')
        payment_method = request.form.get('payment_method', 'efectivo')
        notes = request.form.get('notes', '')
        status = request.form.get('status', order['status'])
        
        # Items del carrito (JSON)
        cart_items = json.loads(request.form.get('cart_items', '[]'))
        
        if not cart_items:
            flash('Debe haber al menos un producto en la orden', 'error')
            return redirect(url_for('edit_order', order_id=order_id))
        
        # Calcular totales
        subtotal = sum(item['quantity'] * item['price'] for item in cart_items)
        discount = 0  # Mantener descuento existente o implementar lógica
        total_amount = subtotal - discount
        
        # Actualizar orden
        db.execute('''
            UPDATE orders 
            SET customer_name = ?, customer_phone = ?, payment_method = ?, 
                notes = ?, status = ?, subtotal = ?, total_amount = ?, updated_at = ?
            WHERE id = ?
        ''', (customer_name, customer_phone, payment_method, notes, status, 
              subtotal, total_amount, get_chile_timestamp(), order_id))
        
        # Eliminar items existentes y sus variaciones
        existing_items = db.execute('SELECT id FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
        for item in existing_items:
            db.execute('DELETE FROM order_item_variations WHERE order_item_id = ?', (item['id'],))
        db.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
        
        # Insertar nuevos items
        cursor = db.cursor()
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, product_name, 
                                       quantity, unit_price, total_price, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, item['id'], item['name'], item['quantity'], 
                  item['price'], item['quantity'] * item['price'], item.get('notes', '')))
            
            item_id = cursor.lastrowid
            
            # Insertar variaciones si las hay
            if 'variations' in item:
                for variation in item['variations']:
                    cursor.execute('''
                        INSERT INTO order_item_variations (order_item_id, variation_option_id, price_modifier)
                        VALUES (?, ?, ?)
                    ''', (item_id, variation['option_id'], variation['price_modifier']))
        
        db.commit()
        flash('Orden actualizada exitosamente', 'success')
        return redirect(url_for('view_order', order_id=order_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar la orden: {str(e)}', 'error')
        return redirect(url_for('edit_order', order_id=order_id))

@app.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    """Eliminar una orden"""
    try:
        db = get_db()
        
        # Verificar que la orden existe
        order = db.execute('SELECT order_number FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            flash('Orden no encontrada', 'error')
            return redirect(url_for('list_orders'))
        
        # Eliminar variaciones de items
        db.execute('''
            DELETE FROM order_item_variations 
            WHERE order_item_id IN (
                SELECT id FROM order_items WHERE order_id = ?
            )
        ''', (order_id,))
        
        # Eliminar items de la orden
        db.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
        
        # Eliminar la orden
        db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        
        db.commit()
        flash(f'Orden {order["order_number"]} eliminada exitosamente', 'success')
        return redirect(url_for('list_orders'))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al eliminar la orden: {str(e)}', 'error')
        return redirect(url_for('view_order', order_id=order_id))

@app.route('/orders/<int:order_id>/print')
def print_order(order_id):
    """Generar impresión térmica de la orden"""
    db = get_db()
    
    # Obtener orden
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        flash('Orden no encontrada', 'error')
        return redirect(url_for('list_orders'))
    
    # Obtener items con variaciones
    order_items = db.execute('''
        SELECT oi.*, 
               GROUP_CONCAT(vo.display_name, ', ') as variations
        FROM order_items oi
        LEFT JOIN order_item_variations oiv ON oi.id = oiv.order_item_id
        LEFT JOIN variation_options vo ON oiv.variation_option_id = vo.id
        WHERE oi.order_id = ?
        GROUP BY oi.id
        ORDER BY oi.id
    ''', (order_id,)).fetchall()
    
    # Generar contenido para impresión térmica
    return render_template('print_order.html', order=order, order_items=order_items)

def auto_print_kitchen_ticket(order_id):
    """Impresión automática para cocina al crear orden"""
    try:
        import webbrowser
        import threading
        from urllib.parse import urljoin
        from flask import request
        
        def print_async():
            # Usar la URL base de tu aplicación
            base_url = request.url_root if request else 'http://localhost:5000/'
            print_url = urljoin(base_url, f'kitchen-ticket/{order_id}')
            webbrowser.open(print_url)
        
        # Ejecutar en hilo separado
        threading.Thread(target=print_async, daemon=True).start()
        
    except Exception as e:
        print(f"Error en impresión automática: {e}")

# ===== GESTIÓN DE PRODUCTOS =====

@app.route('/products')
def list_products():
    """Lista de productos"""
    db = get_db()
    
    products = db.execute('''
        SELECT p.*, c.name as category_name, c.color as category_color
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY c.name, p.name
    ''').fetchall()
    
    return render_template('products_list.html', products=products)

@app.route('/products/new')
def new_product():
    """Formulario para nuevo producto"""
    db = get_db()
    categories = db.execute('SELECT * FROM categories WHERE active = 1 ORDER BY name').fetchall()
    return render_template('product_form.html', categories=categories)

@app.route('/products/create', methods=['POST'])
def create_product():
    """Crear nuevo producto"""
    try:
        db = get_db()
        cursor = db.cursor()  # Usar cursor para obtener lastrowid
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = float(request.form.get('price'))
        category_id = request.form.get('category_id')
        
        # Insertar producto
        cursor.execute('''
            INSERT INTO products (name, description, price, category_id)
            VALUES (?, ?, ?, ?)
        ''', (name, description, price, category_id))
        
        product_id = cursor.lastrowid
        
        # Manejar variaciones
        variation_groups = request.form.getlist('variation_groups[]')
        required_groups = request.form.getlist('required_groups[]')
        if variation_groups:
            save_product_variations(product_id, variation_groups, required_groups)
        
        db.commit()
        
        flash('Producto creado exitosamente', 'success')
        return redirect(url_for('list_products'))
        
    except Exception as e:
        flash(f'Error al crear producto: {str(e)}', 'error')
        return redirect(url_for('new_product'))

@app.route('/products/<int:product_id>/edit')
def edit_product(product_id):
    """Formulario para editar producto"""
    db = get_db()
    
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Producto no encontrado', 'error')
        return redirect(url_for('list_products'))
    
    categories = db.execute('SELECT * FROM categories WHERE active = 1 ORDER BY name').fetchall()
    return render_template('product_form.html', product=product, categories=categories)

@app.route('/products/<int:product_id>/update', methods=['POST'])
def update_product(product_id):
    """Actualizar producto"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = float(request.form.get('price'))
        category_id = request.form.get('category_id')
        available = 1 if request.form.get('available') else 0
        
        db.execute('''
            UPDATE products 
            SET name = ?, description = ?, price = ?, category_id = ?, available = ?
            WHERE id = ?
        ''', (name, description, price, category_id, available, product_id))
         # Manejar variaciones
        variation_groups = request.form.getlist('variation_groups[]')
        required_groups = request.form.getlist('required_groups[]')
        save_product_variations(product_id, variation_groups, required_groups)
        
        db.commit()

        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('list_products'))
        
    except Exception as e:
        flash(f'Error al actualizar producto: {str(e)}', 'error')
        return redirect(url_for('edit_product', product_id=product_id))

@app.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Eliminar producto (soft delete)"""
    db = get_db()
    
    db.execute('UPDATE products SET available = 0 WHERE id = ?', (product_id,))
    db.commit()
    
    flash('Producto desactivado correctamente', 'success')
    return redirect(url_for('list_products'))

# ===== GESTIÓN DE CATEGORÍAS =====

@app.route('/categories')
def list_categories():
    """Lista de categorías"""
    db = get_db()
    
    categories = db.execute('''
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id AND p.available = 1
        GROUP BY c.id
        ORDER BY c.name
    ''').fetchall()
    
    return render_template('categories_list.html', categories=categories)

@app.route('/categories/new')
def new_category():
    """Formulario para nueva categoría"""
    return render_template('category_form.html')

@app.route('/categories/create', methods=['POST'])
def create_category():
    """Crear nueva categoría"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        color = request.form.get('color', '#3498db')
        
        db.execute('''
            INSERT INTO categories (name, description, color)
            VALUES (?, ?, ?)
        ''', (name, description, color))
        db.commit()
        
        flash('Categoría creada exitosamente', 'success')
        return redirect(url_for('list_categories'))
        
    except Exception as e:
        flash(f'Error al crear categoría: {str(e)}', 'error')
        return redirect(url_for('new_category'))

@app.route('/categories/<int:category_id>/edit')
def edit_category(category_id):
    """Formulario para editar categoría"""
    db = get_db()
    
    category = db.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
    if not category:
        flash('Categoría no encontrada', 'error')
        return redirect(url_for('list_categories'))
    
    return render_template('category_form.html', category=category)

@app.route('/categories/<int:category_id>/update', methods=['POST'])
def update_category(category_id):
    """Actualizar categoría"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        color = request.form.get('color', '#3498db')
        active = 1 if request.form.get('active') else 0
        
        db.execute('''
            UPDATE categories 
            SET name = ?, description = ?, color = ?, active = ?
            WHERE id = ?
        ''', (name, description, color, active, category_id))
        db.commit()
        
        flash('Categoría actualizada exitosamente', 'success')
        return redirect(url_for('list_categories'))
        
    except Exception as e:
        flash(f'Error al actualizar categoría: {str(e)}', 'error')
        return redirect(url_for('edit_category', category_id=category_id))

# ===== API ENDPOINTS =====

@app.route('/api/products')
def api_products():
    """API para obtener productos"""
    db = get_db()
    category_id = request.args.get('category_id')
    
    query = '''
        SELECT p.*, c.name as category_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.available = 1
    '''
    params = []
    
    if category_id:
        query += ' AND p.category_id = ?'
        params.append(category_id)
    
    query += ' ORDER BY p.name'
    
    products = db.execute(query, params).fetchall()
    
    return jsonify([dict(product) for product in products])

@app.route('/api/categories')
def api_categories():
    """API para obtener categorías"""
    db = get_db()
    
    categories = db.execute('''
        SELECT * FROM categories 
        WHERE active = 1 
        ORDER BY name
    ''').fetchall()
    
    return jsonify([dict(category) for category in categories])

# ===== REPORTES =====

@app.route('/reports')
def reports():
    """Página de reportes"""
    db = get_db()
    
    # Estadísticas para los últimos 7 días usando fechas locales
    today = get_chile_today()
    week_ago = today - datetime.timedelta(days=7)
    
    # Ventas reales de los últimos 7 días
    stats = {
        'today_sales': db.execute(
            'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = ?',
            (today,)
        ).fetchone()[0],
        'week_sales': db.execute(
            'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) >= ?',
            (week_ago,)
        ).fetchone()[0],
        'month_sales': db.execute(
            'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) >= ?',
            (today - datetime.timedelta(days=30),)
        ).fetchone()[0],
        'total_orders': db.execute(
            'SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= ?',
            (week_ago,)
        ).fetchone()[0]
    }
    
    # Productos más vendidos (últimos 7 días)
    top_products_raw = db.execute('''
        SELECT oi.product_name, SUM(oi.quantity) as total_quantity, SUM(oi.total_price) as total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) >= ?
        GROUP BY oi.product_name
        ORDER BY total_quantity DESC
        LIMIT 10
    ''', (week_ago,)).fetchall()

    # Convertir a diccionarios y manejar caso sin datos
    top_products = [dict(row) for row in top_products_raw] if top_products_raw else []
    
    # Ventas por categoría (últimos 7 días)
    category_sales = db.execute('''
        SELECT c.name as category_name, c.color, COALESCE(SUM(oi.total_price), 0) as total_sales
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        LEFT JOIN order_items oi ON p.id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.id AND DATE(o.created_at) >= ?
        WHERE c.active = 1
        GROUP BY c.id, c.name, c.color
        ORDER BY total_sales DESC
    ''', (week_ago,)).fetchall()
    
    # Ventas por hora (últimos 7 días)
    hourly_sales = db.execute('''
        SELECT strftime('%H', created_at) as hour, COUNT(*) as order_count
        FROM orders 
        WHERE DATE(created_at) >= ?
        GROUP BY strftime('%H', created_at)
        ORDER BY hour
    ''', (week_ago,)).fetchall()
    
    return render_template('reports.html', 
                         stats=stats, 
                         top_products=top_products,
                         category_sales=[dict(row) for row in category_sales],
                         hourly_sales=[dict(row) for row in hourly_sales])

# ===== RUTAS DEL SISTEMA DE INVENTARIO =====

# ===== GESTIÓN DE INGREDIENTES =====

@app.route('/inventory/ingredients')
def list_ingredients():
    """Lista de ingredientes con stock"""
    db = get_db()
    
    ingredients = db.execute('''
        SELECT i.*, s.name as supplier_name
        FROM ingredients i
        LEFT JOIN suppliers s ON i.preferred_supplier_id = s.id
        ORDER BY i.name
    ''').fetchall()
    
    # Ingredientes con stock bajo
    low_stock = db.execute('''
        SELECT * FROM ingredients 
        WHERE current_stock <= min_stock AND active = 1
        ORDER BY name
    ''').fetchall()
    
    return render_template('inventory/ingredients_list.html', 
                         ingredients=ingredients, low_stock=low_stock)

@app.route('/inventory/ingredients/new')
def new_ingredient():
    """Formulario para nuevo ingrediente"""
    db = get_db()
    suppliers = db.execute('SELECT * FROM suppliers WHERE active = 1 ORDER BY name').fetchall()
    return render_template('inventory/ingredient_form.html', suppliers=suppliers)

@app.route('/inventory/ingredients/create', methods=['POST'])
def create_ingredient():
    """Crear nuevo ingrediente"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        unit = request.form.get('unit', 'gr')
        min_stock = float(request.form.get('min_stock', 0))
        max_stock = float(request.form.get('max_stock', 0))
        unit_cost = float(request.form.get('unit_cost', 0))
        supplier_id = request.form.get('supplier_id') or None
        
        db.execute('''
            INSERT INTO ingredients (name, description, unit, min_stock, max_stock, unit_cost, preferred_supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, unit, min_stock, max_stock, unit_cost, supplier_id))
        db.commit()
        
        flash('Ingrediente creado exitosamente', 'success')
        return redirect(url_for('list_ingredients'))
        
    except Exception as e:
        flash(f'Error al crear ingrediente: {str(e)}', 'error')
        return redirect(url_for('new_ingredient'))

@app.route('/inventory/ingredients/<int:ingredient_id>/edit')
def edit_ingredient(ingredient_id):
    """Formulario para editar ingrediente"""
    db = get_db()
    
    ingredient = get_ingredient_by_id(ingredient_id)
    if not ingredient:
        flash('Ingrediente no encontrado', 'error')
        return redirect(url_for('list_ingredients'))
    
    suppliers = db.execute('SELECT * FROM suppliers WHERE active = 1 ORDER BY name').fetchall()
    return render_template('inventory/ingredient_form.html', ingredient=ingredient, suppliers=suppliers)

@app.route('/inventory/ingredients/<int:ingredient_id>/update', methods=['POST'])
def update_ingredient(ingredient_id):
    """Actualizar ingrediente"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        unit = request.form.get('unit', 'gr')
        min_stock = float(request.form.get('min_stock', 0))
        max_stock = float(request.form.get('max_stock', 0))
        unit_cost = float(request.form.get('unit_cost', 0))
        supplier_id = request.form.get('supplier_id') or None
        active = 1 if request.form.get('active') else 0
        
        db.execute('''
            UPDATE ingredients 
            SET name = ?, description = ?, unit = ?, min_stock = ?, max_stock = ?, 
                unit_cost = ?, preferred_supplier_id = ?, active = ?, updated_at = ?
            WHERE id = ?
        ''', (name, description, unit, min_stock, max_stock, unit_cost, supplier_id, active, get_chile_timestamp(), ingredient_id))
        db.commit()
        
        flash('Ingrediente actualizado exitosamente', 'success')
        return redirect(url_for('list_ingredients'))
        
    except Exception as e:
        flash(f'Error al actualizar ingrediente: {str(e)}', 'error')
        return redirect(url_for('edit_ingredient', ingredient_id=ingredient_id))

@app.route('/inventory/ingredients/adjust-stock', methods=['POST'])
def adjust_ingredient_stock():
    """Ajustar stock de ingrediente manualmente"""
    try:
        db = get_db()
        
        ingredient_id = request.form.get('ingredient_id')
        adjustment = float(request.form.get('adjustment'))
        notes = request.form.get('notes', '')
        
        # Obtener stock actual
        current = db.execute(
            'SELECT current_stock, unit_cost FROM ingredients WHERE id = ?', 
            (ingredient_id,)
        ).fetchone()
        
        if not current:
            flash('Ingrediente no encontrado', 'error')
            return redirect(url_for('list_ingredients'))
        
        new_stock = current['current_stock'] + adjustment
        
        # Actualizar stock
        db.execute(
            'UPDATE ingredients SET current_stock = ?, updated_at = ? WHERE id = ?',
            (new_stock, get_chile_timestamp(), ingredient_id)
        )
        
        # Registrar movimiento
        movement_type = 'adjustment'
        db.execute('''
            INSERT INTO inventory_movements 
            (ingredient_id, movement_type, quantity, unit_cost, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ingredient_id, movement_type, adjustment, current['unit_cost'], notes, get_chile_timestamp()))
        
        db.commit()
        flash('Stock ajustado correctamente', 'success')
        
    except Exception as e:
        flash(f'Error al ajustar stock: {str(e)}', 'error')
    
    return redirect(url_for('list_ingredients'))

# ===== GESTIÓN DE PROVEEDORES =====

@app.route('/inventory/suppliers')
def list_suppliers():
    """Lista de proveedores"""
    db = get_db()
    
    suppliers = db.execute('''
        SELECT s.*, COUNT(i.id) as ingredients_count
        FROM suppliers s
        LEFT JOIN ingredients i ON s.id = i.preferred_supplier_id
        GROUP BY s.id
        ORDER BY s.name
    ''').fetchall()
    
    return render_template('inventory/suppliers_list.html', suppliers=suppliers)

@app.route('/inventory/suppliers/new')
def new_supplier():
    """Formulario para nuevo proveedor"""
    return render_template('inventory/supplier_form.html')

@app.route('/inventory/suppliers/create', methods=['POST'])
def create_supplier():
    """Crear nuevo proveedor"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        contact_person = request.form.get('contact_person', '')
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        address = request.form.get('address', '')
        tax_id = request.form.get('tax_id', '')
        
        db.execute('''
            INSERT INTO suppliers (name, contact_person, phone, email, address, tax_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, contact_person, phone, email, address, tax_id))
        db.commit()
        
        flash('Proveedor creado exitosamente', 'success')
        return redirect(url_for('list_suppliers'))
        
    except Exception as e:
        flash(f'Error al crear proveedor: {str(e)}', 'error')
        return redirect(url_for('new_supplier'))

@app.route('/inventory/suppliers/<int:supplier_id>/edit')
def edit_supplier(supplier_id):
    """Formulario para editar proveedor"""
    db = get_db()
    
    supplier = db.execute('SELECT * FROM suppliers WHERE id = ?', (supplier_id,)).fetchone()
    if not supplier:
        flash('Proveedor no encontrado', 'error')
        return redirect(url_for('list_suppliers'))
    
    return render_template('inventory/supplier_form.html', supplier=supplier)

@app.route('/inventory/suppliers/<int:supplier_id>/update', methods=['POST'])
def update_supplier(supplier_id):
    """Actualizar proveedor"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        contact_person = request.form.get('contact_person', '')
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        address = request.form.get('address', '')
        tax_id = request.form.get('tax_id', '')
        active = 1 if request.form.get('active') else 0
        
        db.execute('''
            UPDATE suppliers 
            SET name = ?, contact_person = ?, phone = ?, email = ?, address = ?, tax_id = ?, active = ?, updated_at = ?
            WHERE id = ?
        ''', (name, contact_person, phone, email, address, tax_id, active, get_chile_timestamp(), supplier_id))
        db.commit()
        
        flash('Proveedor actualizado exitosamente', 'success')
        return redirect(url_for('list_suppliers'))
        
    except Exception as e:
        flash(f'Error al actualizar proveedor: {str(e)}', 'error')
        return redirect(url_for('edit_supplier', supplier_id=supplier_id))

# ============================================================================
# GESTIÓN DE RECETAS - RUTAS ACTUALIZADAS PARA SQLITE
# ============================================================================

@app.route('/inventory/recipes')
def list_recipes():
    """Lista de recetas"""
    db = get_db()
    
    recipes = db.execute('''
        SELECT r.*,
               COUNT(ri.ingredient_id) as ingredient_count,
               COALESCE(SUM(ri.quantity * i.unit_cost), 0) as estimated_cost
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        LEFT JOIN ingredients i ON ri.ingredient_id = i.id
        GROUP BY r.id
        ORDER BY r.name
    ''').fetchall()
    
    # Calcular costo por porción para cada receta
    recipes_with_cost = []
    for recipe in recipes:
        recipe_dict = dict(recipe)
        if recipe['estimated_cost'] and recipe['servings']:
            recipe_dict['cost_per_serving'] = recipe['estimated_cost'] / recipe['servings']
        else:
            recipe_dict['cost_per_serving'] = 0
        recipes_with_cost.append(recipe_dict)
    
    return render_template('inventory/recipes_list.html', recipes=recipes_with_cost)

@app.route('/inventory/recipes/new')
def new_recipe():
    """Mostrar formulario para crear nueva receta"""
    try:
        # Obtener todos los ingredientes activos para el formulario
        ingredients = get_all_ingredients(active_only=True)
        return render_template('inventory/recipe_form.html', 
                             recipe=None, 
                             ingredients=ingredients)
    except Exception as e:
        flash(f'Error al cargar formulario de receta: {str(e)}', 'error')
        return redirect(url_for('list_recipes'))

@app.route('/inventory/recipes/create', methods=['POST'])
def create_recipe():
    """Crear nueva receta"""
    try:
        db = get_db()
        
        # Datos básicos de la receta
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        servings = int(request.form.get('servings', 1))
        prep_time = request.form.get('prep_time')
        cook_time = request.form.get('cook_time')
        instructions = request.form.get('instructions', '').strip()
        active = 1 if 'active' in request.form else 0
        
        # Validaciones
        if not name:
            flash('El nombre de la receta es obligatorio', 'error')
            return redirect(url_for('new_recipe'))
        
        if servings <= 0:
            flash('El número de porciones debe ser mayor a 0', 'error')
            return redirect(url_for('new_recipe'))
        
        # Convertir tiempos a enteros si están presentes
        prep_time = int(prep_time) if prep_time else None
        cook_time = int(cook_time) if cook_time else None
        
        # Crear la receta
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO recipes (name, description, category, servings, prep_time, cook_time, instructions, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, category, servings, prep_time, cook_time, instructions, active, get_chile_timestamp()))
        
        recipe_id = cursor.lastrowid
        
        # Procesar ingredientes de la receta
        ingredient_ids = request.form.getlist('ingredient_id[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for i, ingredient_id in enumerate(ingredient_ids):
            if ingredient_id and i < len(quantities) and quantities[i]:
                quantity = float(quantities[i])
                unit = units[i] if i < len(units) else ''
                
                cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                    VALUES (?, ?, ?, ?)
                ''', (recipe_id, ingredient_id, quantity, unit))
        
        db.commit()
        
        flash('Receta creada exitosamente', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al crear receta: {str(e)}', 'error')
        return redirect(url_for('new_recipe'))

@app.route('/inventory/recipes/<int:recipe_id>')
def view_recipe(recipe_id):
    """Ver detalles de una receta"""
    try:
        db = get_db()
        
        # Obtener datos de la receta
        recipe = db.execute('''
            SELECT r.*, 
                   COUNT(ri.ingredient_id) as ingredient_count,
                   COALESCE(SUM(ri.quantity * i.unit_cost), 0) as estimated_cost
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE r.id = ?
            GROUP BY r.id
        ''', (recipe_id,)).fetchone()
        
        if not recipe:
            flash('Receta no encontrada', 'error')
            return redirect(url_for('list_recipes'))
        
        # Convertir a diccionario y calcular costo por porción
        recipe_dict = dict(recipe)
        if recipe['estimated_cost'] and recipe['servings']:
            recipe_dict['cost_per_serving'] = recipe['estimated_cost'] / recipe['servings']
        else:
            recipe_dict['cost_per_serving'] = 0
        
        # Obtener ingredientes de la receta
        recipe_ingredients = db.execute('''
            SELECT ri.*, i.name as ingredient_name, i.unit as ingredient_unit, i.unit_cost,
                   (ri.quantity * i.unit_cost) as ingredient_cost
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
            ORDER BY i.name
        ''', (recipe_id,)).fetchall()
        
        return render_template('inventory/recipe_view.html', 
                             recipe=recipe_dict, 
                             recipe_ingredients=recipe_ingredients)
        
    except Exception as e:
        flash(f'Error al cargar receta: {str(e)}', 'error')
        return redirect(url_for('list_recipes'))

@app.route('/inventory/recipes/<int:recipe_id>/edit')
def edit_recipe(recipe_id):
    """Mostrar formulario para editar receta"""
    try:
        db = get_db()
        
        # Obtener datos de la receta
        recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        
        if not recipe:
            flash('Receta no encontrada', 'error')
            return redirect(url_for('list_recipes'))
        
        # Obtener ingredientes de la receta
        recipe_ingredients = db.execute('''
            SELECT ri.*, i.name as ingredient_name, i.unit as ingredient_unit
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
            ORDER BY i.name
        ''', (recipe_id,)).fetchall()
        
        # Obtener todos los ingredientes disponibles
        ingredients = get_all_ingredients(active_only=True)
        
        return render_template('inventory/recipe_form.html', 
                             recipe=recipe, 
                             recipe_ingredients=recipe_ingredients,
                             ingredients=ingredients)
        
    except Exception as e:
        flash(f'Error al cargar receta: {str(e)}', 'error')
        return redirect(url_for('list_recipes'))

@app.route('/inventory/recipes/<int:recipe_id>/update', methods=['POST'])
def update_recipe(recipe_id):
    """Actualizar receta existente"""
    try:
        db = get_db()
        
        # Verificar que la receta existe
        recipe = db.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        if not recipe:
            flash('Receta no encontrada', 'error')
            return redirect(url_for('list_recipes'))
        
        # Datos básicos de la receta
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        servings = int(request.form.get('servings', 1))
        prep_time = request.form.get('prep_time')
        cook_time = request.form.get('cook_time')
        instructions = request.form.get('instructions', '').strip()
        active = 1 if 'active' in request.form else 0
        
        # Validaciones
        if not name:
            flash('El nombre de la receta es obligatorio', 'error')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))
        
        if servings <= 0:
            flash('El número de porciones debe ser mayor a 0', 'error')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))
        
        # Convertir tiempos a enteros si están presentes
        prep_time = int(prep_time) if prep_time else None
        cook_time = int(cook_time) if cook_time else None
        
        # Actualizar la receta
        db.execute('''
            UPDATE recipes 
            SET name = ?, description = ?, category = ?, servings = ?, 
                prep_time = ?, cook_time = ?, instructions = ?, active = ?, updated_at = ?
            WHERE id = ?
        ''', (name, description, category, servings, prep_time, cook_time, instructions, active, get_chile_timestamp(), recipe_id))
        
        # Eliminar ingredientes existentes
        db.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
        
        # Agregar ingredientes actualizados
        ingredient_ids = request.form.getlist('ingredient_id[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for i, ingredient_id in enumerate(ingredient_ids):
            if ingredient_id and i < len(quantities) and quantities[i]:
                quantity = float(quantities[i])
                unit = units[i] if i < len(units) else ''
                
                db.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                    VALUES (?, ?, ?, ?)
                ''', (recipe_id, ingredient_id, quantity, unit))
        
        db.commit()
        
        flash('Receta actualizada exitosamente', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar receta: {str(e)}', 'error')
        return redirect(url_for('edit_recipe', recipe_id=recipe_id))

@app.route('/inventory/recipes/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    """Eliminar receta"""
    try:
        db = get_db()
        
        # Verificar que la receta existe
        recipe = db.execute("SELECT name FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        
        if not recipe:
            flash('Receta no encontrada', 'error')
            return redirect(url_for('list_recipes'))
        
        # Eliminar ingredientes de la receta
        db.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
        
        # Eliminar la receta
        db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        
        db.commit()
        
        flash(f'Receta "{recipe[0]}" eliminada exitosamente', 'success')
        return redirect(url_for('list_recipes'))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al eliminar receta: {str(e)}', 'error')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))

# ============================================================================
# APIs DE RECETAS
# ============================================================================

@app.route('/api/recipes/<int:recipe_id>/calculate-cost')
def api_calculate_recipe_cost(recipe_id):
    """API para calcular el costo de una receta"""
    try:
        db = get_db()
        
        # Obtener datos de la receta
        recipe = db.execute("SELECT name, servings FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        
        if not recipe:
            return jsonify({'success': False, 'message': 'Receta no encontrada'})
        
        # Obtener ingredientes y calcular costos
        ingredients = db.execute('''
            SELECT ri.quantity, ri.unit, i.name, i.unit_cost, i.unit as ingredient_unit,
                   (ri.quantity * i.unit_cost) as cost
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        ''', (recipe_id,)).fetchall()
        
        total_cost = sum(ingredient['cost'] or 0 for ingredient in ingredients)
        cost_per_serving = total_cost / recipe['servings'] if recipe['servings'] > 0 else 0
        
        ingredients_cost = [
            {
                'name': ing['name'],
                'quantity': ing['quantity'],
                'unit': ing['unit'] or ing['ingredient_unit'],
                'cost': ing['cost'] or 0
            }
            for ing in ingredients
        ]
        
        return jsonify({
            'success': True,
            'total_cost': total_cost,
            'cost_per_serving': cost_per_serving,
            'ingredients_cost': ingredients_cost
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/recipes/<int:recipe_id>/duplicate', methods=['POST'])
def api_duplicate_recipe(recipe_id):
    """API para duplicar una receta"""
    try:
        db = get_db()
        
        # Obtener datos de la receta original
        recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        
        if not recipe:
            return jsonify({'success': False, 'message': 'Receta no encontrada'})
        
        # Crear nueva receta con nombre modificado
        new_name = f"Copia de {recipe['name']}"
        
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO recipes (name, description, category, servings, prep_time, cook_time, instructions, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_name, recipe['description'], recipe['category'], recipe['servings'],
            recipe['prep_time'], recipe['cook_time'], recipe['instructions'], recipe['active'], get_chile_timestamp()
        ))
        
        new_recipe_id = cursor.lastrowid
        
        # Copiar ingredientes de la receta
        db.execute('''
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
            SELECT ?, ingredient_id, quantity, unit
            FROM recipe_ingredients
            WHERE recipe_id = ?
        ''', (new_recipe_id, recipe_id))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'new_recipe_id': new_recipe_id,
            'message': 'Receta duplicada exitosamente'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)})

# ===== GESTIÓN DE COMPRAS =====

@app.route('/inventory/purchases')
def list_purchases():
    """Lista de compras"""
    db = get_db()
    
    purchases = db.execute('''
        SELECT p.*, s.name as supplier_name
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    return render_template('inventory/purchases_list.html', purchases=purchases)

@app.route('/inventory/purchases/new')
def new_purchase():
    """Formulario para nueva compra"""
    db = get_db()
    suppliers = db.execute('SELECT * FROM suppliers WHERE active = 1 ORDER BY name').fetchall()
    ingredients = db.execute('SELECT * FROM ingredients WHERE active = 1 ORDER BY name').fetchall()
    return render_template('inventory/purchase_form.html', suppliers=suppliers, ingredients=ingredients)

@app.route('/inventory/purchases/create', methods=['POST'])
def create_purchase():
    """Crear nueva compra"""
    try:
        db = get_db()
        
        supplier_id = request.form.get('supplier_id')
        purchase_date = request.form.get('purchase_date')
        expected_date = request.form.get('expected_date') or None
        notes = request.form.get('notes', '')
        
        # Generar número de compra
        chile_now = get_chile_now()
        purchase_number = f"PUR-{chile_now.strftime('%Y%m%d%H%M%S')}"
        
        # Calcular total
        ingredient_ids = request.form.getlist('ingredient_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        
        total_amount = sum(
            float(q) * float(p) for q, p in zip(quantities, unit_prices)
            if q and p
        )
        
        # Crear compra
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO purchases (purchase_number, supplier_id, total_amount, purchase_date, expected_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (purchase_number, supplier_id, total_amount, purchase_date, expected_date, notes, get_chile_timestamp()))
        
        purchase_id = cursor.lastrowid
        
        # Agregar items
        for i, ingredient_id in enumerate(ingredient_ids):
            if ingredient_id and quantities[i] and unit_prices[i]:
                quantity = float(quantities[i])
                unit_price = float(unit_prices[i])
                total_price = quantity * unit_price
                
                cursor.execute('''
                    INSERT INTO purchase_items (purchase_id, ingredient_id, quantity, unit, unit_price, total_price)
                    VALUES (?, ?, ?, 'kg', ?, ?)
                ''', (purchase_id, ingredient_id, quantity, unit_price, total_price))
        
        db.commit()
        flash(f'Compra {purchase_number} creada exitosamente', 'success')
        return redirect(url_for('list_purchases'))
        
    except Exception as e:
        flash(f'Error al crear compra: {str(e)}', 'error')
        return redirect(url_for('new_purchase'))

@app.route('/inventory/purchases/<int:purchase_id>')
def view_purchase(purchase_id):
    """Ver detalle de compra"""
    db = get_db()
    
    purchase = db.execute('''
        SELECT p.*, s.name as supplier_name
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.id = ?
    ''', (purchase_id,)).fetchone()
    
    if not purchase:
        flash('Compra no encontrada', 'error')
        return redirect(url_for('list_purchases'))
    
    items = db.execute('''
        SELECT pi.*, i.name as ingredient_name
        FROM purchase_items pi
        JOIN ingredients i ON pi.ingredient_id = i.id
        WHERE pi.purchase_id = ?
        ORDER BY i.name
    ''', (purchase_id,)).fetchall()
    
    return render_template('inventory/purchase_detail.html', purchase=purchase, items=items)

@app.route('/inventory/purchases/<int:purchase_id>/receive', methods=['POST'])
def receive_purchase(purchase_id):
    """Recibir compra y actualizar inventario"""
    try:
        db = get_db()
        
        # Obtener items de la compra
        items = db.execute('''
            SELECT pi.*, i.name as ingredient_name
            FROM purchase_items pi
            JOIN ingredients i ON pi.ingredient_id = i.id
            WHERE pi.purchase_id = ?
        ''', (purchase_id,)).fetchall()
        
        cursor = db.cursor()
        
        # Procesar cada item
        for item in items:
            received_qty = float(request.form.get(f'received_{item["id"]}', item['quantity']))
            
            # Actualizar cantidad recibida
            cursor.execute('''
                UPDATE purchase_items 
                SET received_quantity = ? 
                WHERE id = ?
            ''', (received_qty, item['id']))
            
            # Actualizar stock del ingrediente
            cursor.execute('''
                UPDATE ingredients 
                SET current_stock = current_stock + ?, 
                    unit_cost = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (received_qty, item['unit_price'], get_chile_timestamp(), item['ingredient_id']))
            
            # Registrar movimiento de inventario
            cursor.execute('''
                INSERT INTO inventory_movements 
                (ingredient_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes, created_at)
                VALUES (?, 'purchase', ?, ?, 'purchase', ?, ?, ?)
            ''', (item['ingredient_id'], received_qty, item['unit_price'], purchase_id, f'Compra recibida: {item["ingredient_name"]}', get_chile_timestamp()))
        
        # Actualizar estado de la compra
        cursor.execute('''
            UPDATE purchases 
            SET status = 'received', received_date = date('now', 'localtime')
            WHERE id = ?
        ''', (purchase_id,))
        
        db.commit()
        flash('Compra recibida y stock actualizado', 'success')
        
    except Exception as e:
        flash(f'Error al recibir compra: {str(e)}', 'error')
    
    return redirect(url_for('view_purchase', purchase_id=purchase_id))

# ===== CONSUMO DE RECETAS =====

def consume_recipe_ingredients(recipe_id, quantity=1):
    """Consumir ingredientes de una receta (llamar al vender un producto)"""
    db = get_db()
    
    try:
        # Obtener ingredientes de la receta
        ingredients = db.execute('''
            SELECT ri.*, i.name as ingredient_name, i.current_stock
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        ''', (recipe_id,)).fetchall()
        
        cursor = db.cursor()
        
        # Verificar stock suficiente
        insufficient_stock = []
        for ingredient in ingredients:
            needed = ingredient['quantity'] * quantity
            if ingredient['current_stock'] < needed:
                insufficient_stock.append({
                    'name': ingredient['ingredient_name'],
                    'needed': needed,
                    'available': ingredient['current_stock']
                })
        
        if insufficient_stock:
            return False, insufficient_stock
        
        # Consumir ingredientes
        for ingredient in ingredients:
            consumed = ingredient['quantity'] * quantity
            
            # Actualizar stock
            cursor.execute('''
                UPDATE ingredients 
                SET current_stock = current_stock - ?,
                    updated_at = ?
                WHERE id = ?
            ''', (consumed, get_chile_timestamp(), ingredient['ingredient_id']))
            
            # Registrar movimiento
            cursor.execute('''
                INSERT INTO inventory_movements 
                (ingredient_id, movement_type, quantity, reference_type, reference_id, notes, created_at)
                VALUES (?, 'consumption', ?, 'recipe', ?, ?, ?)
            ''', (ingredient['ingredient_id'], -consumed, recipe_id, f'Consumo por receta: {ingredient["ingredient_name"]}', get_chile_timestamp()))
        
        db.commit()
        return True, None
        
    except Exception as e:
        db.rollback()
        return False, str(e)

# ===== API ENDPOINTS PARA INVENTARIO =====

@app.route('/api/inventory/low-stock')
def api_low_stock():
    """API para obtener ingredientes con stock bajo"""
    db = get_db()
    
    low_stock = db.execute('''
        SELECT id, name, current_stock, min_stock, unit
        FROM ingredients 
        WHERE current_stock <= min_stock AND active = 1
        ORDER BY (current_stock/min_stock) ASC
    ''').fetchall()
    
    return jsonify([dict(item) for item in low_stock])

@app.route('/api/inventory/movements/<int:ingredient_id>')
def api_ingredient_movements(ingredient_id):
    """API para obtener movimientos de un ingrediente"""
    db = get_db()
    
    movements = db.execute('''
        SELECT * FROM inventory_movements 
        WHERE ingredient_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (ingredient_id,)).fetchall()
    
    return jsonify([dict(movement) for movement in movements])

@app.route('/api/inventory/recipe-cost/<int:recipe_id>')
def api_recipe_cost(recipe_id):
    """API para calcular costo de una receta"""
    db = get_db()
    
    ingredients = db.execute('''
        SELECT ri.quantity, ri.unit, i.unit_cost, i.name
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
    ''', (recipe_id,)).fetchall()
    
    total_cost = 0
    details = []
    
    for ingredient in ingredients:
        cost = ingredient['quantity'] * ingredient['unit_cost']
        total_cost += cost
        details.append({
            'name': ingredient['name'],
            'quantity': ingredient['quantity'],
            'unit': ingredient['unit'],
            'unit_cost': ingredient['unit_cost'],
            'total_cost': cost
        })
    
    return jsonify({
        'total_cost': total_cost,
        'details': details
    })

# ===== REPORTES DE INVENTARIO =====

@app.route('/inventory/reports')
def inventory_reports():
    """Reportes de inventario"""
    db = get_db()
    
    # Stock bajo
    low_stock = db.execute('''
        SELECT name, current_stock, min_stock, unit
        FROM ingredients 
        WHERE current_stock <= min_stock AND active = 1
        ORDER BY name
    ''').fetchall()
    
    # Valor total del inventario
    total_value = db.execute('''
        SELECT SUM(current_stock * unit_cost) as total
        FROM ingredients 
        WHERE active = 1
    ''').fetchone()['total'] or 0
    
    # Movimientos recientes
    recent_movements = db.execute('''
        SELECT im.*, i.name as ingredient_name
        FROM inventory_movements im
        JOIN ingredients i ON im.ingredient_id = i.id
        ORDER BY im.created_at DESC
        LIMIT 20
    ''').fetchall()
    
    # Top ingredientes más consumidos
    top_consumed = db.execute('''
        SELECT i.name, SUM(ABS(im.quantity)) as total_consumed
        FROM inventory_movements im
        JOIN ingredients i ON im.ingredient_id = i.id
        WHERE im.movement_type = 'consumption'
        AND date(im.created_at) >= date('now', '-30 days', 'localtime')
        GROUP BY i.id, i.name
        ORDER BY total_consumed DESC
        LIMIT 10
    ''').fetchall()
    
    stats = {
        'total_ingredients': db.execute('SELECT COUNT(*) FROM ingredients WHERE active = 1').fetchone()[0],
        'low_stock_count': len(low_stock),
        'total_value': total_value,
        'suppliers_count': db.execute('SELECT COUNT(*) FROM suppliers WHERE active = 1').fetchone()[0]
    }
    
    return render_template('inventory/reports.html', 
                         stats=stats, 
                         low_stock=low_stock,
                         recent_movements=recent_movements,
                         top_consumed=top_consumed)

# ===== DASHBOARD DE INVENTARIO =====

@app.route('/inventory')
def inventory_dashboard():
    """Dashboard principal del inventario"""
    db = get_db()
    
    # Estadísticas generales
    stats = {
        'total_ingredients': db.execute('SELECT COUNT(*) FROM ingredients WHERE active = 1').fetchone()[0],
        'low_stock_count': db.execute('SELECT COUNT(*) FROM ingredients WHERE current_stock <= min_stock AND active = 1').fetchone()[0],
        'total_recipes': db.execute('SELECT COUNT(*) FROM recipes WHERE active = 1').fetchone()[0],
        'pending_purchases': db.execute('SELECT COUNT(*) FROM purchases WHERE status = "pending"').fetchone()[0],
        'total_suppliers': db.execute('SELECT COUNT(*) FROM suppliers WHERE active = 1').fetchone()[0]
    }
    
    # Valor total del inventario
    total_value = db.execute('''
        SELECT SUM(current_stock * unit_cost) as total
        FROM ingredients WHERE active = 1
    ''').fetchone()['total'] or 0
    
    stats['inventory_value'] = total_value
    
    # Alertas de stock bajo
    low_stock_alerts = db.execute('''
        SELECT name, current_stock, min_stock, unit
        FROM ingredients 
        WHERE current_stock <= min_stock AND active = 1
        ORDER BY (current_stock/min_stock) ASC
        LIMIT 5
    ''').fetchall()
    
    # Compras pendientes
    pending_purchases = db.execute('''
        SELECT p.*, s.name as supplier_name
        FROM purchases p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.status = 'pending'
        ORDER BY p.expected_date ASC
        LIMIT 5
    ''').fetchall()
    
    # Movimientos recientes
    recent_movements = db.execute('''
        SELECT im.*, i.name as ingredient_name
        FROM inventory_movements im
        JOIN ingredients i ON im.ingredient_id = i.id
        ORDER BY im.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    return render_template('inventory/dashboard.html',
                         stats=stats,
                         low_stock_alerts=low_stock_alerts,
                         pending_purchases=pending_purchases,
                         recent_movements=recent_movements)

# ===== FUNCIONES AUXILIARES PARA VARIACIONES =====

@app.route('/api/variation-groups')
def get_variation_groups():
    """API para obtener todos los grupos de variación"""
    db = get_db()
    
    groups = db.execute('''
        SELECT id, name, display_name, description, required, multiple_selection
        FROM variation_groups 
        WHERE active = 1 
        ORDER BY name
    ''').fetchall()
    
    return jsonify([dict(group) for group in groups])

def save_product_variations(product_id, variation_groups, required_groups):
    """Guardar variaciones asignadas a un producto"""
    db = get_db()
    cursor = db.cursor()
    
    # Eliminar variaciones existentes
    cursor.execute('DELETE FROM product_variations WHERE product_id = ?', (product_id,))
    
    # Insertar nuevas variaciones
    if variation_groups:
        for group_id in variation_groups:
            required = 1 if str(group_id) in required_groups else 0
            cursor.execute('''
                INSERT INTO product_variations (product_id, variation_group_id, required)
                VALUES (?, ?, ?)
            ''', (product_id, group_id, required))
    
    db.commit()

@app.route('/api/product-variations/<int:product_id>')
def get_product_variations(product_id):
    """API para obtener variaciones de un producto"""
    db = get_db()

    # DEBUG: Verificar si existen relaciones
    debug_query = db.execute('''
        SELECT pv.*, vg.name, vg.display_name 
        FROM product_variations pv
        JOIN variation_groups vg ON pv.variation_group_id = vg.id
        WHERE pv.product_id = ?
    ''', (product_id,)).fetchall()
    
    print(f"DEBUG product_id {product_id}: {len(debug_query)} variaciones encontradas")
    for row in debug_query:
        print(f"  - Grupo: {row['name']}, Required: {row['required']}")
    
    variations = db.execute('''
        SELECT 
            vg.id as group_id,
            vg.name as group_name,
            vg.display_name as group_display,
            vg.description as group_description,
            vg.required as group_required,
            vg.multiple_selection,
            vg.min_selections,
            vg.max_selections,
            vo.id as option_id,
            vo.name as option_name,
            vo.display_name as option_display,
            vo.price_modifier,
            vo.sort_order,
            pv.required as variation_required
        FROM product_variations pv
        JOIN variation_groups vg ON pv.variation_group_id = vg.id
        JOIN variation_options vo ON vg.id = vo.variation_group_id
        WHERE pv.product_id = ? AND vg.active = 1 AND vo.active = 1
        ORDER BY pv.sort_order, vg.id, vo.sort_order
    ''', (product_id,)).fetchall()
    
    # Agrupar por grupos de variación
    grouped_variations = {}
    for row in variations:
        group_id = row['group_id']
        if group_id not in grouped_variations:
            grouped_variations[group_id] = {
                'id': row['group_id'],
                'name': row['group_name'],
                'display_name': row['group_display'],
                'description': row['group_description'],
                'required': bool(row['group_required']) or bool(row['variation_required']),
                'multiple_selection': bool(row['multiple_selection']),
                'min_selections': row['min_selections'],
                'max_selections': row['max_selections'],
                'options': []
            }
        
        grouped_variations[group_id]['options'].append({
            'id': row['option_id'],
            'name': row['option_name'],
            'display_name': row['option_display'],
            'price_modifier': row['price_modifier'],
            'sort_order': row['sort_order']
        })
    
    return jsonify(list(grouped_variations.values()))

# ===== REPORTES Y EXPORTACIÓN DE DATOS =====

# Flask example
@app.route('/api/reports/export-data')
def export_data():
    # Parámetros disponibles:
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date') 
    period = request.args.get('period')
    include_charts = request.args.get('include_charts')
    include_details = request.args.get('include_details')
    template = request.args.get('template')
    
    # Tu lógica aquí...
    return jsonify(response_data)

@app.route('/api/reports/send-email', methods=['POST'])
def send_email():
    # Para envío por email
    pass

@app.route('/api/reports/schedule', methods=['POST']) 
def schedule_report():
    # Para programación automática
    pass

@app.route('/api/reports/templates', methods=['GET', 'POST'])
def manage_templates():
    # Para guardar/cargar templates
    pass

@app.route('/api/reports/export-data')
def get_report_export_data():
    """API para obtener datos de exportación"""
    try:
        db = get_db()
        
        # Reutilizar la lógica de la función reports()
        today = get_chile_today()
        week_ago = today - datetime.timedelta(days=7)
        month_ago = today - datetime.timedelta(days=30)
        
        stats = {
            'today_sales': db.execute(
                'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = ?',
                (today,)
            ).fetchone()[0],
            'week_sales': db.execute(
                'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) >= ?',
                (week_ago,)
            ).fetchone()[0],
            'month_sales': db.execute(
                'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) >= ?',
                (month_ago,)
            ).fetchone()[0],
            'total_orders': db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        }
        
        top_products_raw = db.execute('''
            SELECT product_name, SUM(quantity) as total_quantity, SUM(total_price) as total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) >= ?
            GROUP BY product_name
            ORDER BY total_quantity DESC
            LIMIT 10
        ''', (week_ago,)).fetchall()
        
        top_products = [dict(row) for row in top_products_raw]
        
        # Estructura de respuesta para la exportación
        response_data = {
            'fecha_generacion': datetime.datetime.now().strftime('%d/%m/%Y'),
            'hora_generacion': datetime.datetime.now().strftime('%H:%M:%S'),
            'periodo': 'week',
            'estadisticas': {
                'ventas_hoy': float(stats['today_sales']),
                'ventas_semana': float(stats['week_sales']),
                'ventas_mes': float(stats['month_sales']),
                'total_ordenes': stats['total_orders'],
                'promedio_diario': float(stats['month_sales']) / 30 if stats['month_sales'] > 0 else 0,
                'ordenes_promedio_dia': stats['total_orders'] / 30 if stats['total_orders'] > 0 else 0,
                'ticket_promedio': float(stats['month_sales']) / stats['total_orders'] if stats['total_orders'] > 0 else 0
            },
            'top_productos': top_products
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# ===== IMPRESIÓN DE TICKETS =====
@app.route('/kitchen-ticket/<int:order_id>')
def print_kitchen_ticket(order_id):
    """Imprimir ticket para cocina"""
    from datetime import datetime
    
    db = get_db()
    
    # Obtener orden
    order = db.execute(
        'SELECT * FROM orders WHERE id = ?', (order_id,)
    ).fetchone()
    
    if not order:
        flash('Orden no encontrada', 'error')
        return redirect(url_for('list_orders'))
    
    # Convertir Row a dict para poder modificar
    order = dict(order)
    
    # Convertir created_at de string a datetime si es necesario
    if order.get('created_at'):
        try:
            if isinstance(order['created_at'], str):
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y'
                ]
                
                for fmt in formats:
                    try:
                        order['created_at'] = datetime.strptime(order['created_at'], fmt)
                        break
                    except ValueError:
                        continue
                        
        except (ValueError, TypeError):
            pass
    
    # Convertir updated_at si existe
    if order.get('updated_at'):
        try:
            if isinstance(order['updated_at'], str):
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y'
                ]
                
                for fmt in formats:
                    try:
                        order['updated_at'] = datetime.strptime(order['updated_at'], fmt)
                        break
                    except ValueError:
                        continue
                        
        except (ValueError, TypeError):
            pass
    
    # Obtener items con sus variaciones Y NOTAS
    order_items = db.execute('''
    SELECT oi.*, p.name as product_name, p.description,
           oi.notes as item_notes,
           GROUP_CONCAT(
               CASE WHEN vo.name IS NOT NULL 
               THEN vg.display_name || ': ' || vo.display_name 
               END, ' | '
           ) as selected_variations
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    LEFT JOIN order_item_variations oiv ON oi.id = oiv.order_item_id
    LEFT JOIN variation_options vo ON oiv.variation_option_id = vo.id
    LEFT JOIN variation_groups vg ON vo.variation_group_id = vg.id
    WHERE oi.order_id = ?
    GROUP BY oi.id
    ORDER BY oi.id
''', (order_id,)).fetchall()
    
    # Fecha actual para el template
    current_time = get_chile_now()
    
    return render_template('kitchen_ticket.html', 
                         order=order, 
                         order_items=order_items,
                         current_time=current_time)

@app.route('/customer-bill/<int:order_id>')
def print_customer_bill(order_id):
    """Imprimir cuenta para cliente"""
    from datetime import datetime
    
    db = get_db()
    
    # Obtener orden
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        flash('Orden no encontrada', 'error')
        return redirect(url_for('list_orders'))
    
    # Convertir Row a dict para poder modificar
    order = dict(order)
    
    # Convertir created_at de string a datetime si es necesario
    if order.get('created_at'):
        try:
            if isinstance(order['created_at'], str):
                # Intentar varios formatos comunes
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y'
                ]
                
                for fmt in formats:
                    try:
                        order['created_at'] = datetime.strptime(order['created_at'], fmt)
                        break
                    except ValueError:
                        continue
                        
        except (ValueError, TypeError):
            # Si no se puede convertir, mantener como string
            pass
    
    # Convertir updated_at si existe
    if order.get('updated_at'):
        try:
            if isinstance(order['updated_at'], str):
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%d',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y'
                ]
                
                for fmt in formats:
                    try:
                        order['updated_at'] = datetime.strptime(order['updated_at'], fmt)
                        break
                    except ValueError:
                        continue
                        
        except (ValueError, TypeError):
            pass
    
    # Obtener items para facturación (sin variaciones internas)
    order_items = db.execute('''
        SELECT oi.*, 
               p.name as product_name,
               GROUP_CONCAT(
                   CASE 
                       WHEN vo.display_name IS NOT NULL 
                       THEN vo.display_name 
                       ELSE NULL 
                   END, ', '
               ) as variations
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN order_item_variations oiv ON oi.id = oiv.order_item_id
        LEFT JOIN variation_options vo ON oiv.variation_option_id = vo.id
        WHERE oi.order_id = ?
        GROUP BY oi.id
        ORDER BY oi.id
    ''', (order_id,)).fetchall()
    
    # Convertir order_items a lista de diccionarios para facilitar el manejo
    items_list = []
    for item in order_items:
        item_dict = dict(item)
        # Limpiar variaciones vacías
        if item_dict['variations']:
            item_dict['variations'] = item_dict['variations'].replace('None, ', '').replace(', None', '').strip(', ')
            if item_dict['variations'] == 'None':
                item_dict['variations'] = None
        items_list.append(item_dict)
    
    # Calcular totales
    subtotal = sum(item['total_price'] for item in items_list)
    tip_suggested = subtotal * 0.10  # 10% propina sugerida
    total_with_tip = subtotal + tip_suggested
    
    # AGREGAR ESTAS LÍNEAS:
    current_time = get_chile_now()
    
    return render_template('customer_bill.html',
                         order=order, 
                         order_items=items_list,
                         subtotal=subtotal,
                         tip_suggested=tip_suggested,
                         total_with_tip=total_with_tip,
                         current_time=current_time)  # ← LÍNEA AGREGADA

@app.route('/api/products/save-variations', methods=['POST'])
def api_save_product_variations():
    """API para guardar variaciones de producto"""
    try:
        data = request.json
        product_id = data['product_id']
        variation_groups = data['variation_groups']
        
        db = get_db()
        cursor = db.cursor()
        
        # Eliminar variaciones existentes
        cursor.execute("DELETE FROM product_variations WHERE product_id = ?", (product_id,))
        
        # Asignar nuevos grupos
        for group_id in variation_groups:
            cursor.execute("""
                INSERT INTO product_variations (product_id, variation_group_id, required, sort_order)
                VALUES (?, ?, 1, 0)
            """, (product_id, group_id))
        
        db.commit()
        return jsonify({
            'success': True, 
            'product_id': product_id, 
            'variation_groups': variation_groups
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/products/<int:product_id>/available-variations', methods=['GET'])
def get_available_variations(product_id):
    """Obtener variaciones configuradas para un producto"""
    try:
        db = get_db()
        
        results = db.execute("""
            SELECT vg.*, vo.id as option_id, vo.name as option_name, 
                   vo.display_name as option_display_name, vo.price_modifier
            FROM variation_groups vg
            JOIN product_variations pv ON vg.id = pv.variation_group_id
            JOIN variation_options vo ON vg.id = vo.variation_group_id
            WHERE pv.product_id = ? AND vg.active = 1 AND vo.active = 1
            ORDER BY pv.sort_order, vo.sort_order
        """, (product_id,)).fetchall()
        
        # Agrupar por grupo de variación
        variations = {}
        for row in results:
            group_id = row['id']
            if group_id not in variations:
                variations[group_id] = {
                    'id': group_id,
                    'name': row['name'],
                    'display_name': row['display_name'],
                    'description': row['description'],
                    'required': row['required'],
                    'multiple_selection': row['multiple_selection'],
                    'options': []
                }
            
            variations[group_id]['options'].append({
                'id': row['option_id'],
                'name': row['option_name'],
                'display_name': row['option_display_name'],
                'price_modifier': row['price_modifier']
            })
        
        return jsonify(list(variations.values()))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    # ===== GESTIÓN DE VARIACIONES =====

@app.route('/variations')
def list_variations():
    """Lista de grupos de variación"""
    db = get_db()
    
    groups = db.execute('''
        SELECT vg.*, COUNT(vo.id) as options_count
        FROM variation_groups vg
        LEFT JOIN variation_options vo ON vg.id = vo.variation_group_id
        GROUP BY vg.id
        ORDER BY vg.name
    ''').fetchall()
    
    return render_template('variations/groups_list.html', groups=groups)

@app.route('/variations/new')
def new_variation_group():
    """Formulario para nuevo grupo de variación"""
    return render_template('variations/group_form.html')

@app.route('/variations/create', methods=['POST'])
def create_variation_group():
    """Crear nuevo grupo de variación"""
    try:
        db = get_db()
        
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        description = request.form.get('description', '')
        required = 1 if request.form.get('required') else 0
        multiple_selection = 1 if request.form.get('multiple_selection') else 0
        min_selections = int(request.form.get('min_selections', 1))
        max_selections = request.form.get('max_selections')
        max_selections = int(max_selections) if max_selections else None
        
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO variation_groups (name, display_name, description, required, 
                                        multiple_selection, min_selections, max_selections)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, display_name, description, required, multiple_selection, min_selections, max_selections))
        
        group_id = cursor.lastrowid
        
        # Agregar opciones si se enviaron
        option_names = request.form.getlist('option_names[]')
        option_displays = request.form.getlist('option_displays[]')
        option_prices = request.form.getlist('option_prices[]')
        
        for i, option_name in enumerate(option_names):
            if option_name.strip():
                display = option_displays[i] if i < len(option_displays) else option_name
                price = float(option_prices[i]) if i < len(option_prices) and option_prices[i] else 0
                
                cursor.execute('''
                    INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier)
                    VALUES (?, ?, ?, ?)
                ''', (group_id, option_name.strip(), display.strip(), price))
        
        db.commit()
        flash('Grupo de variación creado exitosamente', 'success')
        return redirect(url_for('list_variations'))
        
    except Exception as e:
        flash(f'Error al crear grupo de variación: {str(e)}', 'error')
        return redirect(url_for('new_variation_group'))

@app.route('/variations/<int:group_id>')
def view_variation_group(group_id):
    """Ver detalles de un grupo de variación"""
    db = get_db()
    
    group = db.execute('SELECT * FROM variation_groups WHERE id = ?', (group_id,)).fetchone()
    if not group:
        flash('Grupo de variación no encontrado', 'error')
        return redirect(url_for('list_variations'))
    
    options = db.execute('''
        SELECT * FROM variation_options 
        WHERE variation_group_id = ? 
        ORDER BY sort_order, name
    ''', (group_id,)).fetchall()
    
    return render_template('variations/group_detail.html', group=group, options=options)

def save_product_variations(product_id, variation_groups, required_groups):
    """Guardar variaciones asignadas a un producto"""
    db = get_db()
    cursor = db.cursor()
    
    # Eliminar variaciones existentes
    cursor.execute('DELETE FROM product_variations WHERE product_id = ?', (product_id,))
    
    # Insertar nuevas variaciones
    if variation_groups:
        for group_id in variation_groups:
            required = 1 if str(group_id) in required_groups else 0
            cursor.execute('''
                INSERT INTO product_variations (product_id, variation_group_id, required)
                VALUES (?, ?, ?)
            ''', (product_id, group_id, required))
    
    db.commit()  

@app.route('/variations/<int:group_id>/edit')
def edit_variation_group(group_id):
    """Formulario para editar grupo de variación"""
    db = get_db()
    
    group = db.execute('SELECT * FROM variation_groups WHERE id = ?', (group_id,)).fetchone()
    if not group:
        flash('Grupo de variación no encontrado', 'error')
        return redirect(url_for('list_variations'))
    
    # Obtener opciones del grupo
    options = db.execute('''
        SELECT * FROM variation_options 
        WHERE variation_group_id = ? 
        ORDER BY sort_order, name
    ''', (group_id,)).fetchall()
    
    # Convertir a diccionario para el template
    group_dict = dict(group)
    group_dict['options'] = [dict(option) for option in options]
    
    return render_template('variations/group_form.html', group=group_dict)

@app.route('/variations/<int:group_id>/update', methods=['POST'])
def update_variation_group(group_id):
    """Actualizar grupo de variación"""
    try:
        db = get_db()
        
        # Verificar que el grupo existe
        group = db.execute('SELECT * FROM variation_groups WHERE id = ?', (group_id,)).fetchone()
        if not group:
            flash('Grupo de variación no encontrado', 'error')
            return redirect(url_for('list_variations'))
        
        # Datos del formulario
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        description = request.form.get('description', '')
        required = 1 if request.form.get('required') else 0
        multiple_selection = 1 if request.form.get('multiple_selection') else 0
        min_selections = int(request.form.get('min_selections', 1))
        max_selections = request.form.get('max_selections')
        max_selections = int(max_selections) if max_selections else None
        active = 1 if request.form.get('active') else 0
        
        # Actualizar grupo
        db.execute('''
            UPDATE variation_groups 
            SET name = ?, display_name = ?, description = ?, required = ?, 
                multiple_selection = ?, min_selections = ?, max_selections = ?, 
                active = ?, updated_at = ?
            WHERE id = ?
        ''', (name, display_name, description, required, multiple_selection, 
              min_selections, max_selections, active, get_chile_timestamp(), group_id))
        
        # Eliminar opciones existentes
        db.execute('DELETE FROM variation_options WHERE variation_group_id = ?', (group_id,))
        
        # Agregar opciones actualizadas
        option_names = request.form.getlist('option_names[]')
        option_displays = request.form.getlist('option_displays[]')
        option_prices = request.form.getlist('option_prices[]')
        
        cursor = db.cursor()
        for i, option_name in enumerate(option_names):
            if option_name.strip():
                display = option_displays[i] if i < len(option_displays) else option_name
                price = float(option_prices[i]) if i < len(option_prices) and option_prices[i] else 0
                
                cursor.execute('''
                    INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order)
                    VALUES (?, ?, ?, ?, ?)
                ''', (group_id, option_name.strip(), display.strip(), price, i))
        
        db.commit()
        flash('Grupo de variación actualizado exitosamente', 'success')
        return redirect(url_for('view_variation_group', group_id=group_id))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar grupo de variación: {str(e)}', 'error')
        return redirect(url_for('edit_variation_group', group_id=group_id))

@app.route('/variations/<int:group_id>/delete', methods=['POST'])
def delete_variation_group(group_id):
    """Eliminar grupo de variación"""
    try:
        db = get_db()
        
        # Verificar que el grupo existe
        group = db.execute('SELECT name FROM variation_groups WHERE id = ?', (group_id,)).fetchone()
        if not group:
            flash('Grupo de variación no encontrado', 'error')
            return redirect(url_for('list_variations'))
        
        # Eliminar opciones del grupo
        db.execute('DELETE FROM variation_options WHERE variation_group_id = ?', (group_id,))
        
        # Eliminar asociaciones con productos
        db.execute('DELETE FROM product_variations WHERE variation_group_id = ?', (group_id,))
        
        # Eliminar el grupo
        db.execute('DELETE FROM variation_groups WHERE id = ?', (group_id,))
        
        db.commit()
        flash(f'Grupo de variación "{group["name"]}" eliminado exitosamente', 'success')
        return redirect(url_for('list_variations'))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al eliminar grupo de variación: {str(e)}', 'error')
        return redirect(url_for('view_variation_group', group_id=group_id))

@app.route('/variations/options/<int:option_id>/edit')
def edit_variation_option(option_id):
    """Editar opción individual (implementación futura)"""
    flash('Funcionalidad en desarrollo', 'info')
    return redirect(url_for('list_variations'))

@app.route('/variations/options/<int:option_id>/delete', methods=['POST'])
def delete_variation_option(option_id):
    """Eliminar opción individual"""
    try:
        db = get_db()
        
        # Obtener información de la opción
        option = db.execute('''
            SELECT vo.*, vg.id as group_id 
            FROM variation_options vo
            JOIN variation_groups vg ON vo.variation_group_id = vg.id
            WHERE vo.id = ?
        ''', (option_id,)).fetchone()
        
        if not option:
            flash('Opción no encontrada', 'error')
            return redirect(url_for('list_variations'))
        
        # Eliminar la opción
        db.execute('DELETE FROM variation_options WHERE id = ?', (option_id,))
        db.commit()
        
        flash('Opción eliminada exitosamente', 'success')
        return redirect(url_for('view_variation_group', group_id=option['group_id']))
        
    except Exception as e:
        db.rollback()
        flash(f'Error al eliminar opción: {str(e)}', 'error')
        return redirect(url_for('list_variations'))

@app.route('/variations/<int:group_id>/options/new')
def new_variation_option(group_id):
    """Nueva opción para un grupo (implementación futura)"""
    flash('Funcionalidad en desarrollo', 'info')
    return redirect(url_for('view_variation_group', group_id=group_id))        

# ===== INICIALIZACIÓN =====

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)