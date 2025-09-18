#!/usr/bin/env python3
"""
Script para insertar productos con precios y costos en el sistema Epicuro
Ejecutar: python insert_products_with_costs.py
"""

import sqlite3
import os

# Configuración de la base de datos
DATABASE = 'data/sandwich.db'

# Datos de productos (nombre, categoría, precio, costo)
products_data = [
    # BEBIDAS
    ('AGUA CON GAS', 'BEBIDAS', 1200, 360),
    ('AGUA MINERAL', 'BEBIDAS', 1200, 360),
    ('COCA COLA', 'BEBIDAS', 1400, 360),
    ('FANTA', 'BEBIDAS', 1400, 360),
    ('KEM PIÑA', 'BEBIDAS', 1400, 700),
    ('LIMON SODA', 'BEBIDAS', 1400, 700),
    ('PEPSI', 'BEBIDAS', 1400, 360),
    ('SPRITE', 'BEBIDAS', 1400, 360),
    
    # CAFETERIA
    ('CAFÉ + SÁNDWICH ELECCIÓN', 'CAFETERIA', 4990, 3000),
    ('CAFÉ AMERICANO MEDIANO', 'CAFETERIA', 2400, 750),
    ('CAFÉ AMERICANO GRANDE', 'CAFETERIA', 1800, 490),
    ('CAFÉ EXPRESO', 'CAFETERIA', 1800, 490),
    ('CAPPUCCINO MEDIANO', 'CAFETERIA', 2400, 750),
    ('CAPPUCCINO GRANDE', 'CAFETERIA', 2800, 1000),
    ('CAPUCCINO VAINILLA MEDIANO', 'CAFETERIA', 2400, 800),
    ('CAPPUCCINO VAINILLA GRANDE', 'CAFETERIA', 2800, 1000),
    ('CHOCOLATE FUERTE MEDIANO', 'CAFETERIA', 2400, 750),
    ('CHOCOLATE FUERTE GRANDE', 'CAFETERIA', 2800, 1000),
    ('CORTADO MEDIANO', 'CAFETERIA', 2400, 800),
    ('CORTADO GRANDE', 'CAFETERIA', 2800, 1000),
    ('LATTE MACCHIATO MEDIANO', 'CAFETERIA', 2400, 750),
    ('LATTE MACCHIATO GRANDE', 'CAFETERIA', 2800, 1000),
    ('MOCACCINO MEDIANO', 'CAFETERIA', 2400, 750),
    ('MOCACCINO GRANDE', 'CAFETERIA', 2800, 0),  # Costo 0 como en tu lista
    ('TÉ NEGRO', 'CAFETERIA', 1200, 750),
    ('TÉ VERDE', 'CAFETERIA', 2400, 720),
    ('VAINILLA FRANCESA MEDIANA', 'CAFETERIA', 2400, 800),
    ('VAINILLA FRANCESA GRANDE', 'CAFETERIA', 2800, 1000),
    
    # COMPLETOS
    ('COMPLETO DINÁMICO', 'COMPLETOS', 3990, 2400),
    ('COMPLETO EPICURO', 'COMPLETOS', 4790, 2400),
    ('COMPLETO ITALIANO', 'COMPLETOS', 3790, 2400),
    
    # ENERGETICAS
    ('RED BULL ORIGINAL', 'ENERGETICAS', 1800, 600),
    ('RED BULL SIN AZÚCAR', 'ENERGETICAS', 1800, 600),
    
    # DESAYUNOS (nombres corregidos)
    ('DESAYUNO - HUEVO', 'DESAYUNOS', 3500, 1000),
    ('DESAYUNO - JAMÓN QUESO', 'DESAYUNOS', 3500, 1000),
    ('DESAYUNO - MECHADA QUESO', 'DESAYUNOS', 3500, 1000),
    ('DESAYUNO - PASTA DE POLLO Y QUESO CREMA', 'DESAYUNOS', 3500, 1000),
    
    # JUGOS
    ('WATTS DURAZNO', 'JUGOS', 1500, 450),
    ('WATTS FRUTILLA', 'JUGOS', 1500, 450),
    ('WATTS NARANJA', 'JUGOS', 1500, 450),
    ('WATTS PIÑA', 'JUGOS', 1500, 450),
    
    # SOPAS
    ('CONSOME', 'SOPAS', 1200, 1200),
    
    # ENSALADAS
    ('ENSALADA CÉSAR', 'ENSALADAS', 5990, 3000),
    ('ENSALADA EPICURO', 'ENSALADAS', 5990, 3000),
    ('ENSALADA VEGGIE', 'ENSALADAS', 5990, 3000),
    
    # PAPAS FRITAS
    ('PAPA CHICA', 'PAPAS FRITAS', 1000, 500),
    ('PAPA GRANDE', 'PAPAS FRITAS', 5000, 5000),
    ('PAPA MEDIANA', 'PAPAS FRITAS', 2500, 3000),
    
    # SANDWICH
    ('SANDWICH A LO POBRE', 'SANDWICH', 9990, 3000),
    ('SANDWICH CHACARERO', 'SANDWICH', 8790, 3000),
    ('SANDWICH COLCHAGUINO', 'SANDWICH', 7990, 3000),
    ('SANDWICH EPICURO', 'SANDWICH', 8990, 3000),
    ('SANDWICH ITALIANO', 'SANDWICH', 8990, 3000),
    ('SANDWICH LUCO DE LUJO', 'SANDWICH', 9990, 3000),
    ('SANDWICH PICARO', 'SANDWICH', 8990, 3000),
]

def create_connection():
    """Crear conexión a la base de datos"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def check_and_add_cost_column(conn):
    """Verificar si existe la columna de costo y agregarla si no existe"""
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna 'cost' existe
        cursor.execute("PRAGMA table_info(products)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cost' not in columns:
            print("Agregando columna 'cost' a la tabla products...")
            cursor.execute('ALTER TABLE products ADD COLUMN cost REAL DEFAULT 0')
            conn.commit()
            print("✓ Columna 'cost' agregada exitosamente")
        else:
            print("✓ Columna 'cost' ya existe")
            
        return True
        
    except Exception as e:
        print(f"✗ Error verificando/agregando columna cost: {e}")
        return False

def insert_products_with_costs(conn):
    """Insertar productos con precios y costos"""
    cursor = conn.cursor()
    
    print("Insertando productos con precios y costos...")
    print("="*50)
    
    # Obtener IDs de categorías
    cursor.execute('SELECT id, name FROM categories')
    categories_map = {row['name']: row['id'] for row in cursor.fetchall()}
    
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    for product_name, category_name, price, cost in products_data:
        try:
            category_id = categories_map.get(category_name)
            if not category_id:
                print(f"✗ Categoría no encontrada: {category_name}")
                error_count += 1
                continue
            
            # Verificar si el producto ya existe
            existing = cursor.execute(
                'SELECT id FROM products WHERE name = ?', 
                (product_name,)
            ).fetchone()
            
            if existing:
                # Actualizar producto existente
                cursor.execute('''
                    UPDATE products 
                    SET price = ?, cost = ?, category_id = ?, available = 1
                    WHERE name = ?
                ''', (price, cost, category_id, product_name))
                print(f"↻ Actualizado: {product_name} - ${price:,} (costo: ${cost:,})")
                updated_count += 1
            else:
                # Insertar nuevo producto
                cursor.execute('''
                    INSERT INTO products (name, price, cost, category_id, available)
                    VALUES (?, ?, ?, ?, 1)
                ''', (product_name, price, cost, category_id))
                print(f"✓ Insertado: {product_name} - ${price:,} (costo: ${cost:,})")
                inserted_count += 1
                
        except Exception as e:
            print(f"✗ Error con producto {product_name}: {e}")
            error_count += 1
    
    conn.commit()
    
    print("\n" + "="*50)
    print("RESUMEN DE LA IMPORTACIÓN")
    print("="*50)
    print(f"Productos nuevos insertados: {inserted_count}")
    print(f"Productos actualizados: {updated_count}")
    print(f"Errores: {error_count}")
    print(f"Total procesado: {len(products_data)}")

def calculate_margins(conn):
    """Calcular y mostrar márgenes de ganancia"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("ANÁLISIS DE MÁRGENES")
    print("="*50)
    
    cursor.execute('''
        SELECT 
            name, 
            price, 
            cost,
            CASE 
                WHEN cost > 0 THEN ROUND(((price - cost) * 100.0 / price), 1)
                ELSE 100.0
            END as margin_percent,
            price - cost as profit
        FROM products 
        WHERE available = 1 AND price > 0
        ORDER BY margin_percent ASC
    ''')
    
    products = cursor.fetchall()
    
    print(f"{'Producto':<35} {'Precio':<8} {'Costo':<8} {'Margen %':<8} {'Ganancia':<8}")
    print("-" * 75)
    
    total_revenue = 0
    total_cost = 0
    low_margin_count = 0
    
    for product in products:
        margin_color = ""
        if product['margin_percent'] < 30:
            margin_color = "⚠️ "
            low_margin_count += 1
        elif product['margin_percent'] > 70:
            margin_color = "💰 "
        
        print(f"{product['name'][:34]:<35} ${product['price']:<7,} ${product['cost']:<7,} {margin_color}{product['margin_percent']:<6}% ${product['profit']:<7,}")
        
        total_revenue += product['price']
        total_cost += product['cost']
    
    if total_revenue > 0:
        overall_margin = ((total_revenue - total_cost) / total_revenue) * 100
        print("-" * 75)
        print(f"MARGEN PROMEDIO GENERAL: {overall_margin:.1f}%")
        print(f"Productos con margen bajo (<30%): {low_margin_count}")

def verify_data(conn):
    """Verificar los datos insertados"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("VERIFICACIÓN DE DATOS")
    print("="*50)
    
    # Productos por categoría
    cursor.execute('''
        SELECT c.name, COUNT(p.id) as product_count, 
               COALESCE(SUM(p.price), 0) as total_revenue,
               COALESCE(SUM(p.cost), 0) as total_cost
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id AND p.available = 1
        GROUP BY c.id, c.name
        ORDER BY c.name
    ''')
    
    print(f"{'Categoría':<15} {'Productos':<10} {'Revenue':<12} {'Costo':<12} {'Margen %':<8}")
    print("-" * 65)
    
    total_products = 0
    grand_revenue = 0
    grand_cost = 0
    
    for row in cursor.fetchall():
        total_products += row['product_count']
        grand_revenue += row['total_revenue']
        grand_cost += row['total_cost']
        
        margin = 0
        if row['total_revenue'] > 0:
            margin = ((row['total_revenue'] - row['total_cost']) / row['total_revenue']) * 100
        
        print(f"{row['name']:<15} {row['product_count']:<10} ${row['total_revenue']:<11,} ${row['total_cost']:<11,} {margin:<6.1f}%")
    
    print("-" * 65)
    print(f"{'TOTAL':<15} {total_products:<10} ${grand_revenue:<11,} ${grand_cost:<11,}")
    
    if grand_revenue > 0:
        grand_margin = ((grand_revenue - grand_cost) / grand_revenue) * 100
        print(f"MARGEN GENERAL: {grand_margin:.1f}%")

def main():
    """Función principal"""
    print("IMPORTACIÓN DE PRODUCTOS CON COSTOS - EPICURO")
    print("="*60)
    
    try:
        # Crear conexión
        conn = create_connection()
        
        # Verificar y agregar columna de costo
        if not check_and_add_cost_column(conn):
            print("Error configurando la tabla. Abortando.")
            return
        
        # Insertar productos
        insert_products_with_costs(conn)
        
        # Calcular márgenes
        calculate_margins(conn)
        
        # Verificar datos
        verify_data(conn)
        
        print("\n" + "="*60)
        print("✓ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("Puedes ahora:")
        print("1. Iniciar tu aplicación: python app.py")
        print("2. Revisar productos: http://localhost:5002/products")
        print("3. Crear órdenes con los nuevos productos")
        
    except Exception as e:
        print(f"\n✗ ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()