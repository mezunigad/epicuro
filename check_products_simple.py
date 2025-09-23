import sqlite3
import csv
import os

def check_missing_products_simple(db_path='data/sandwich.db'):
    """
    Verificar productos directamente desde la base de datos y mostrar lo que hay
    """
    print("=== VERIFICANDO PRODUCTOS EN BASE DE DATOS ===")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos {db_path} no encontrada")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener productos existentes
        cursor.execute('''
            SELECT p.id, p.name, p.price, c.name as categoria, p.available
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY c.name, p.name
        ''')
        productos_bd = cursor.fetchall()
        
        # Obtener categorías
        cursor.execute('SELECT id, name, active FROM categories ORDER BY name')
        categorias_bd = cursor.fetchall()
        
        print(f"📊 CATEGORÍAS EN BASE DE DATOS ({len(categorias_bd)}):")
        for cat_id, nombre, activo in categorias_bd:
            status = "✅" if activo else "❌"
            print(f"  {status} {nombre}")
        
        print(f"\n📊 PRODUCTOS EN BASE DE DATOS ({len(productos_bd)}):")
        categoria_actual = None
        productos_activos = 0
        
        for prod_id, nombre, precio, categoria, disponible in productos_bd:
            if categoria != categoria_actual:
                print(f"\n📂 {categoria or 'Sin categoría'}:")
                categoria_actual = categoria
            
            status = "✅" if disponible else "❌"
            if disponible:
                productos_activos += 1
            print(f"  {status} {nombre} - ${precio:,.0f}")
        
        print(f"\n📈 RESUMEN:")
        print(f"  • Total productos: {len(productos_bd)}")
        print(f"  • Productos activos: {productos_activos}")
        print(f"  • Total categorías: {len(categorias_bd)}")
        
        conn.close()
        
        # Mostrar productos del Excel que conocemos
        print(f"\n📋 PRODUCTOS QUE VI EN TU EXCEL:")
        productos_excel_conocidos = [
            ("MOCACCINO GRANDE", "CAFETERÍA", 2800),
            ("TÉ NEGRO", "CAFETERÍA", 1200),
            ("LATTE", "CAFETERÍA", 2400),
            ("PAPA MEDIANA", "SANDWICH", 2500),
            ("SANDWICH CHACARERO", "SANDWICH", 8790),
            ("PAPA CHICA", "SANDWICH", 1000),
            ("SANDWICH EPICURO", "SANDWICH", 8990),
            ("COCA COLA", "BEBIDA", 1400)
        ]
        
        productos_bd_nombres = [p[1].upper() for p in productos_bd if p[4]]  # Solo activos
        
        print("\nComparando con productos del Excel:")
        for nombre, categoria, precio in productos_excel_conocidos:
            if nombre.upper() in productos_bd_nombres:
                print(f"  ✅ {nombre} - ${precio} ({categoria}) - YA EXISTE")
            else:
                print(f"  ❌ {nombre} - ${precio} ({categoria}) - FALTA CREAR")
        
        print(f"\n💡 RECOMENDACIÓN:")
        print("1. Revisa la lista de productos arriba")
        print("2. Crea manualmente los productos que faltan en tu sistema web")
        print("3. O instala pandas y usa el script completo:")
        print("   pip install pandas openpyxl")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def create_sample_products_sql():
    """
    Crear script SQL con los productos básicos que vimos en el Excel
    """
    print("\n=== GENERANDO SCRIPT SQL BÁSICO ===")
    
    sql_script = """-- Script para crear productos básicos del Excel
-- Ejecutar en tu base de datos SQLite

-- Crear categorías si no existen
INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('CAFETERÍA', 'Bebidas calientes y café', '#8B4513', 1);
INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('SANDWICH', 'Sándwiches y comida', '#FF6B35', 1);
INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('BEBIDA', 'Bebidas frías', '#4A90E2', 1);

-- Crear productos básicos
INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('MOCACCINO GRANDE', 'Café mocaccino tamaño grande', 2800, (SELECT id FROM categories WHERE name = 'CAFETERÍA'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('TÉ NEGRO', 'Té negro tradicional', 1200, (SELECT id FROM categories WHERE name = 'CAFETERÍA'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('LATTE', 'Café latte', 2400, (SELECT id FROM categories WHERE name = 'CAFETERÍA'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('PAPA MEDIANA', 'Papa rellena tamaño mediano', 2500, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('SANDWICH CHACARERO', 'Sandwich chacarero tradicional', 8790, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('PAPA CHICA', 'Papa rellena tamaño chico', 1000, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('SANDWICH EPICURO', 'Sandwich especial de la casa', 8990, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('COCA COLA', 'Coca Cola 350ml', 1400, (SELECT id FROM categories WHERE name = 'BEBIDA'), 1);

-- Verificar productos creados
SELECT p.name, p.price, c.name as categoria 
FROM products p 
JOIN categories c ON p.category_id = c.id 
WHERE p.available = 1 
ORDER BY c.name, p.name;
"""
    
    with open('crear_productos_basicos.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    print("💾 Archivo creado: crear_productos_basicos.sql")
    print("   Puedes ejecutar este SQL en tu base de datos")
    print("   O crear los productos manualmente en tu sistema web")

if __name__ == "__main__":
    # Verificar productos actuales
    success = check_missing_products_simple()
    
    if success:
        print(f"\n🔧 ¿Quieres generar un script SQL básico con los productos del Excel? (s/n)")
        try:
            respuesta = input().lower()
            if respuesta in ['s', 'si', 'y', 'yes']:
                create_sample_products_sql()
        except:
            print("Generando script SQL automáticamente...")
            create_sample_products_sql()