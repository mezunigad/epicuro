#!/usr/bin/env python3
"""
Script para insertar productos iniciales en el sistema Epicuro
Ejecutar: python insert_products.py
"""

import sqlite3
import os

# Configuración de la base de datos
DATABASE = 'data/sandwich.db'

# Datos de productos (nombre, categoría, precio)
products_data = [
    ('AGUA CON GAS', 'BEBIDAS', 1200),
    ('AGUA MINERAL', 'BEBIDAS', 1200),
    ('COCA COLA', 'BEBIDAS', 1400),
    ('FANTA', 'BEBIDAS', 1400),
    ('KEM PIÑA', 'BEBIDAS', 1400),
    ('LIMON SODA', 'BEBIDAS', 1400),
    ('PEPSI', 'BEBIDAS', 1400),
    ('SPRITE', 'BEBIDAS', 1400),
    
    ('CAFÉ + SÁNDWICH ELECCIÓN', 'CAFETERÍA', 4990),
    ('CAFÉ AMERICANO MEDIANO', 'CAFETERÍA', 2400),
    ('CAFÉ AMERICANO GRANDE', 'CAFETERÍA', 1800),
    ('CAFÉ EXPRESO', 'CAFETERÍA', 1800),
    ('CAPPUCCINO MEDIANO', 'CAFETERÍA', 2400),
    ('CAPPUCCINO GRANDE', 'CAFETERÍA', 2800),
    ('CAPUCCINO VAINILLA MEDIANO', 'CAFETERÍA', 2400),
    ('CAPPUCCINO VAINILLA GRANDE', 'CAFETERÍA', 2800),
    ('CHOCOLATE FUERTE MEDIANO', 'CAFETERÍA', 2400),
    ('CHOCOLATE FUERTE GRANDE', 'CAFETERÍA', 2800),
    ('CORTADO MEDIANO', 'CAFETERÍA', 2400),
    ('CORTADO GRANDE', 'CAFETERÍA', 2800),
    ('LATTE MACCHIATO MEDIANO', 'CAFETERÍA', 2400),
    ('LATTE MACCHIATO GRANDE', 'CAFETERÍA', 2800),
    ('MOCACCINO MEDIANO', 'CAFETERÍA', 2400),
    ('MOCACCINO GRANDE', 'CAFETERÍA', 2800),
    ('TÉ NEGRO', 'CAFETERÍA', 1200),
    ('TÉ VERDE', 'CAFETERÍA', 2400),
    ('VAINILLA FRANCESA MEDIANA', 'CAFETERÍA', 2400),
    ('VAINILLA FRANCESA GRANDE', 'CAFETERÍA', 2800),
    
    ('COMPLETO DINÁMICO', 'COMPLETO', 3990),
    ('COMPLETO EPICURO', 'COMPLETO', 4790),
    ('COMPLETO ITALIANO', 'COMPLETO', 3790),
    
    ('RED BULL ORIGINAL', 'ENERGÉTICA', 1800),
    ('RED BULL SIN AZÚCAR', 'ENERGÉTICA', 1800),
    
    ('DESAYUNO - HUEVO JUGO', 'JUGO', 3500),
    ('DESAYUNO - JAMÓN QUESO JUGO', 'JUGO', 3500),
    ('DESAYUNO - MECHADA QUESO JUGO', 'JUGO', 3500),
    ('DESAYUNO - PASTA DE POLLO Y QUESO CREMA JUGO', 'JUGO', 3500),
    ('WATTS DURAZNO', 'JUGO', 1500),
    ('WATTS FRUTILLA', 'JUGO', 1500),
    ('WATTS NARANJA', 'JUGO', 1500),
    ('WATTS PIÑA', 'JUGO', 1500),
    
    ('CONSOME', 'SOPAS', 1200),
    
    ('ENSALADA CÉSAR', 'SANDWICH', 5990),
    ('ENSALADA EPICURO', 'SANDWICH', 5990),
    ('ENSALADA VEGGIE', 'SANDWICH', 5990),
    ('PAPA CHICA', 'SANDWICH', 1000),
    ('PAPA GRANDE', 'SANDWICH', 5000),
    ('PAPA MEDIANA', 'SANDWICH', 2500),
    ('SANDWICH A LO POBRE', 'SANDWICH', 9990),
    ('SANDWICH CHACARERO', 'SANDWICH', 8790),
    ('SANDWICH COLCHAGUINO', 'SANDWICH', 7990),
    ('SANDWICH EPICURO', 'SANDWICH', 8990),
    ('SANDWICH ITALIANO', 'SANDWICH', 8990),
    ('SANDWICH LUCO DE LUJO', 'SANDWICH', 9990),
    ('SANDWICH PICARO', 'SANDWICH', 8990),
]

def create_connection():
    """Crear conexión a la base de datos"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def insert_categories(conn):
    """Insertar categorías en la base de datos"""
    cursor = conn.cursor()
    
    print("Insertando categorías...")
    
    for category in categories_data:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, description, color, active)
                VALUES (?, ?, ?, 1)
            ''', (category['name'], category['description'], category['color']))
            print(f"✓ Categoría insertada: {category['name']}")
        except Exception as e:
            print(f"✗ Error insertando categoría {category['name']}: {e}")
    
    conn.commit()
    print(f"Total categorías procesadas: {len(categories_data)}\n")

def insert_products(conn):
    """Insertar productos en la base de datos"""
    cursor = conn.cursor()
    
    print("Insertando productos...")
    
    # Obtener IDs de categorías
    cursor.execute('SELECT id, name FROM categories')
    categories_map = {row['name']: row['id'] for row in cursor.fetchall()}
    
    inserted_count = 0
    error_count = 0
    
    for product_name, category_name, price in products_data:
        try:
            category_id = categories_map.get(category_name)
            if not category_id:
                print(f"✗ Categoría no encontrada: {category_name}")
                error_count += 1
                continue
            
            cursor.execute('''
                INSERT OR IGNORE INTO products (name, price, category_id, available)
                VALUES (?, ?, ?, 1)
            ''', (product_name, price, category_id))
            
            if cursor.rowcount > 0:
                print(f"✓ Producto insertado: {product_name} - ${price:,}")
                inserted_count += 1
            else:
                print(f"- Producto ya existe: {product_name}")
                
        except Exception as e:
            print(f"✗ Error insertando producto {product_name}: {e}")
            error_count += 1
    
    conn.commit()
    print(f"\nTotal productos insertados: {inserted_count}")
    print(f"Total errores: {error_count}")

def verify_data(conn):
    """Verificar los datos insertados"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("VERIFICACIÓN DE DATOS INSERTADOS")
    print("="*50)
    
    # Verificar categorías
    cursor.execute('SELECT COUNT(*) as count FROM categories WHERE active = 1')
    categories_count = cursor.fetchone()['count']
    print(f"Categorías activas: {categories_count}")
    
    # Verificar productos por categoría
    cursor.execute('''
        SELECT c.name, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id AND p.available = 1
        WHERE c.active = 1
        GROUP BY c.id, c.name
        ORDER BY c.name
    ''')
    
    print("\nProductos por categoría:")
    total_products = 0
    for row in cursor.fetchall():
        print(f"  {row['name']}: {row['product_count']} productos")
        total_products += row['product_count']
    
    print(f"\nTotal productos: {total_products}")
    
    # Verificar rango de precios
    cursor.execute('''
        SELECT 
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price
        FROM products 
        WHERE available = 1
    ''')
    price_stats = cursor.fetchone()
    print(f"\nEstadísticas de precios:")
    print(f"  Precio mínimo: ${price_stats['min_price']:,}")
    print(f"  Precio máximo: ${price_stats['max_price']:,}")
    print(f"  Precio promedio: ${price_stats['avg_price']:,.0f}")

def main():
    """Función principal"""
    print("INICIANDO CARGA DE DATOS EPICURO")
    print("="*50)
    
    try:
        # Crear conexión
        conn = create_connection()
        
        # Insertar categorías
        insert_categories(conn)
        
        # Insertar productos
        insert_products(conn)
        
        # Verificar datos
        verify_data(conn)
        
        print("\n" + "="*50)
        print("✓ CARGA DE DATOS COMPLETADA EXITOSAMENTE")
        print("="*50)
        print("\nPuedes ahora:")
        print("1. Iniciar tu aplicación Flask: python app.py")
        print("2. Visitar: http://localhost:5002/products")
        print("3. Visitar: http://localhost:5002/categories")
        
    except Exception as e:
        print(f"\n✗ ERROR GENERAL: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()