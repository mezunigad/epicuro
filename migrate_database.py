#!/usr/bin/env python3
"""
Script de migración para agregar nuevas funcionalidades:
- Variaciones de productos
- Edición de comandas
- Impresión térmica
"""

import sqlite3
import os

def migrate_database():
    """Ejecutar migraciones en la base de datos existente"""
    
    DATABASE = 'data/sandwich.db'
    
    if not os.path.exists(DATABASE):
        print("❌ Base de datos no encontrada. Ejecuta la aplicación primero para crearla.")
        return False
    
    print("🔄 Iniciando migración de base de datos...")
    
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        
        print("📝 Creando tablas de variaciones...")
        
        # Tabla de grupos de variación
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variation_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                required INTEGER DEFAULT 0,
                multiple_selection INTEGER DEFAULT 0,
                min_selections INTEGER DEFAULT 1,
                max_selections INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        
        # Tabla de opciones de variación
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variation_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variation_group_id INTEGER,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                price_modifier REAL DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id)
            )
        ''')
        
        # Tabla de variaciones por producto
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
        
        # Tabla para guardar selecciones de variaciones en órdenes
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
        
        print("🥩 Insertando datos de proteínas...")
        
        # Insertar grupo de proteínas
        cursor.execute('''
            INSERT OR IGNORE INTO variation_groups (id, name, display_name, description, required)
            VALUES (1, 'protein', 'Proteína Base', 'Selecciona la proteína para tu sandwich', 1)
        ''')
        
        # Insertar opciones de proteínas
        cursor.execute('''
            INSERT OR IGNORE INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order)
            VALUES 
            (1, 'churrasco', 'Churrasco', 0, 1),
            (1, 'lomito', 'Lomito', 500, 2),
            (1, 'pollo', 'Pollo', -300, 3)
        ''')
        
        # Asignar grupo de proteínas a productos que contengan "sandwich" en el nombre
        print("🥪 Asignando proteínas a sandwiches existentes...")
        
        cursor.execute('''
            INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required)
            SELECT id, 1, 1 
            FROM products 
            WHERE LOWER(name) LIKE '%sandwich%' 
               OR LOWER(name) LIKE '%completo%'
               OR LOWER(name) LIKE '%hamburguesa%'
        ''')
        
        # Verificar que la columna notes existe en order_items
        cursor.execute("PRAGMA table_info(order_items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notes' not in columns:
            print("📝 Agregando columna 'notes' a order_items...")
            cursor.execute('ALTER TABLE order_items ADD COLUMN notes TEXT')
        
        db.commit()
        
        print("✅ Migración completada exitosamente!")
        print("\n📊 Resumen:")
        
        # Mostrar estadísticas
        total_groups = cursor.execute('SELECT COUNT(*) FROM variation_groups').fetchone()[0]
        total_options = cursor.execute('SELECT COUNT(*) FROM variation_options').fetchone()[0]
        products_with_variations = cursor.execute('SELECT COUNT(DISTINCT product_id) FROM product_variations').fetchone()[0]
        
        print(f"   • Grupos de variación: {total_groups}")
        print(f"   • Opciones de variación: {total_options}")
        print(f"   • Productos con variaciones: {products_with_variations}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        db.rollback()
        db.close()
        return False

if __name__ == '__main__':
    print("🍴 EPICURO - Migración de Base de Datos")
    print("=" * 40)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 ¡Migración completada!")
        print("\n📝 Próximos pasos:")
        print("   1. Actualiza tu app.py con el código proporcionado")
        print("   2. Crea los templates nuevos (edit_order.html, print_order.html)")
        print("   3. Actualiza los templates existentes")
        print("   4. Reinicia tu aplicación")
        print("\n🚀 ¡Tu sistema estará listo con las nuevas funcionalidades!")
    else:
        print("\n💥 La migración falló. Revisa los errores arriba.")
        
    input("\nPresiona Enter para salir...")
