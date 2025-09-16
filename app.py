from flask import Flask, render_template, request, redirect, url_for, g, jsonify, flash
import sqlite3
import datetime
import os
import json
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'epicuro_secret_key_2024'

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    
    # Solo crear estructuras básicas, sin datos iniciales
    db.commit()
    db.close()

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
    
    # Estadísticas del día
    today = datetime.date.today()
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
    
    # Obtener productos por categoría
    products_by_category = {}
    for category in categories:
        products = db.execute('''
            SELECT * FROM products 
            WHERE category_id = ? AND available = 1 
            ORDER BY name
        ''', (category['id'],)).fetchall()
        products_by_category[category['id']] = products
    
    return render_template('new_order.html', 
                         categories=categories, 
                         products_by_category=products_by_category)

@app.route('/orders/create', methods=['POST'])
def create_order():
    """Crear nueva orden"""
    try:
        db = get_db()
        
        # Datos de la orden
        customer_name = request.form.get('customer_name', '')
        customer_phone = request.form.get('customer_phone', '')
        payment_method = request.form.get('payment_method', 'efectivo')
        notes = request.form.get('notes', '')
        
        # Items del carrito (JSON)
        cart_items = json.loads(request.form.get('cart_items', '[]'))
        
        if not cart_items:
            flash('No hay productos en el carrito', 'error')
            return redirect(url_for('new_order'))
        
        # Generar número de orden
        order_number = f"ORD-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calcular totales
        subtotal = sum(item['quantity'] * item['price'] for item in cart_items)
        discount = 0  # Implementar lógica de descuentos si es necesario
        total_amount = subtotal - discount
        
        # Insertar orden
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO orders (order_number, customer_name, customer_phone, 
                              subtotal, discount, total_amount, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_number, customer_name, customer_phone, 
              subtotal, discount, total_amount, payment_method, notes))
        
        order_id = cursor.lastrowid
        
        # Insertar items de la orden
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, product_name, 
                                       quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, item['id'], item['name'], item['quantity'], 
                  item['price'], item['quantity'] * item['price']))
        
        db.commit()
        flash(f'Orden {order_number} creada exitosamente', 'success')
        return redirect(url_for('view_order', order_id=order_id))
        
    except Exception as e:
        db.rollback()
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
        SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (new_status, order_id))
    db.commit()
    
    flash('Estado actualizado correctamente', 'success')
    return redirect(url_for('view_order', order_id=order_id))

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
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = float(request.form.get('price'))
        category_id = request.form.get('category_id')
        
        db.execute('''
            INSERT INTO products (name, description, price, category_id)
            VALUES (?, ?, ?, ?)
        ''', (name, description, price, category_id))
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
    
    # Estadísticas generales
    today = datetime.date.today()
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
    
    # Productos más vendidos
    top_products = db.execute('''
        SELECT product_name, SUM(quantity) as total_quantity, SUM(total_price) as total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) >= ?
        GROUP BY product_name
        ORDER BY total_quantity DESC
        LIMIT 10
    ''', (week_ago,)).fetchall()
    
    return render_template('reports.html', stats=stats, top_products=top_products)
# ===== RUTAS DEL SISTEMA DE INVENTARIO =====
# Agregar estas rutas a tu app.py después de las rutas existentes

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

@app.route('/inventory/ingredients/<int:ingredient_id>/adjust', methods=['POST'])
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
            'UPDATE ingredients SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_stock, ingredient_id)
        )
        
        # Registrar movimiento
        movement_type = 'adjustment'
        db.execute('''
            INSERT INTO inventory_movements 
            (ingredient_id, movement_type, quantity, unit_cost, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (ingredient_id, movement_type, adjustment, current['unit_cost'], notes))
        
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

# ===== GESTIÓN DE RECETAS =====

@app.route('/inventory/recipes')
def list_recipes():
    """Lista de recetas"""
    db = get_db()
    
    recipes = db.execute('''
        SELECT r.*, p.name as product_name
        FROM recipes r
        LEFT JOIN products p ON r.product_id = p.id
        ORDER BY r.name
    ''').fetchall()
    
    return render_template('inventory/recipes_list.html', recipes=recipes)

@app.route('/inventory/recipes/new')
def new_recipe():
    """Formulario para nueva receta"""
    db = get_db()
    products = db.execute('SELECT * FROM products WHERE available = 1 ORDER BY name').fetchall()
    ingredients = db.execute('SELECT * FROM ingredients WHERE active = 1 ORDER BY name').fetchall()
    return render_template('inventory/recipe_form.html', products=products, ingredients=ingredients)

@app.route('/inventory/recipes/create', methods=['POST'])
def create_recipe():
    """Crear nueva receta"""
    try:
        db = get_db()
        
        product_id = request.form.get('product_id')
        name = request.form.get('name')
        instructions = request.form.get('instructions', '')
        yield_quantity = float(request.form.get('yield_quantity', 1))
        yield_unit = request.form.get('yield_unit', 'unidad')
        prep_time = float(request.form.get('prep_time', 0))
        
        # Crear receta
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO recipes (product_id, name, instructions, yield_quantity, yield_unit, prep_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product_id, name, instructions, yield_quantity, yield_unit, prep_time))
        
        recipe_id = cursor.lastrowid
        
        # Agregar ingredientes de la receta
        ingredient_ids = request.form.getlist('ingredient_id[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for i, ingredient_id in enumerate(ingredient_ids):
            if ingredient_id and quantities[i]:
                cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                    VALUES (?, ?, ?, ?)
                ''', (recipe_id, ingredient_id, float(quantities[i]), units[i]))
        
        db.commit()
        flash('Receta creada exitosamente', 'success')
        return redirect(url_for('list_recipes'))
        
    except Exception as e:
        flash(f'Error al crear receta: {str(e)}', 'error')
        return redirect(url_for('new_recipe'))

@app.route('/inventory/recipes/<int:recipe_id>')
def view_recipe(recipe_id):
    """Ver detalle de receta"""
    db = get_db()
    
    recipe = db.execute('''
        SELECT r.*, p.name as product_name
        FROM recipes r
        LEFT JOIN products p ON r.product_id = p.id
        WHERE r.id = ?
    ''', (recipe_id,)).fetchone()
    
    if not recipe:
        flash('Receta no encontrada', 'error')
        return redirect(url_for('list_recipes'))
    
    ingredients = db.execute('''
        SELECT ri.*, i.name as ingredient_name, i.current_stock, i.unit as stock_unit
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
        ORDER BY i.name
    ''', (recipe_id,)).fetchall()
    
    return render_template('inventory/recipe_detail.html', recipe=recipe, ingredients=ingredients)

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
        purchase_number = f"PUR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
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
            INSERT INTO purchases (purchase_number, supplier_id, total_amount, purchase_date, expected_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (purchase_number, supplier_id, total_amount, purchase_date, expected_date, notes))
        
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
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (received_qty, item['unit_price'], item['ingredient_id']))
            
            # Registrar movimiento de inventario
            cursor.execute('''
                INSERT INTO inventory_movements 
                (ingredient_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes)
                VALUES (?, 'purchase', ?, ?, 'purchase', ?, ?)
            ''', (item['ingredient_id'], received_qty, item['unit_price'], purchase_id, f'Compra recibida: {item["ingredient_name"]}'))
        
        # Actualizar estado de la compra
        cursor.execute('''
            UPDATE purchases 
            SET status = 'received', received_date = date('now')
            WHERE id = ?
        ''', (purchase_id,))
        
        db.commit()
        flash('Compra recibida y stock actualizado', 'success')
        
    except Exception as e:
        flash(f'Error al recibir compra: {str(e)}', 'error')
    
    return redirect(url_for('list_purchases'))

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
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (consumed, ingredient['ingredient_id']))
            
            # Registrar movimiento
            cursor.execute('''
                INSERT INTO inventory_movements 
                (ingredient_id, movement_type, quantity, reference_type, reference_id, notes)
                VALUES (?, 'consumption', ?, 'recipe', ?, ?)
            ''', (ingredient['ingredient_id'], -consumed, recipe_id, f'Consumo por receta: {ingredient["ingredient_name"]}'))
        
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

# ===== MODIFICACIÓN DE RUTAS EXISTENTES =====

# Modificar la función create_order para consumir ingredientes
def create_order_with_inventory():
    """Versión modificada de create_order que consume inventario"""
    try:
        db = get_db()
        
        # ... código existente para crear orden ...
        
        # Después de crear la orden, consumir ingredientes
        for item in cart_items:
            # Buscar si el producto tiene receta
            recipe = db.execute('''
                SELECT id FROM recipes 
                WHERE product_id = ? AND active = 1
                LIMIT 1
            ''', (item['id'],)).fetchone()
            
            if recipe:
                success, error = consume_recipe_ingredients(recipe['id'], item['quantity'])
                if not success:
                    # Si no hay stock suficiente, alertar pero continuar
                    flash(f'Advertencia: Stock insuficiente para {item["name"]}', 'warning')
        
        # ... resto del código existente ...
        
    except Exception as e:
        # ... manejo de errores existente ...
        pass

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
        AND date(im.created_at) >= date('now', '-30 days')
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


# ===== INICIALIZACIÓN =====

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)
