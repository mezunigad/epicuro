#!/usr/bin/env python3
"""
Migración del sistema de variaciones de productos para Epicuro
Ejecutar: python3 migration_variations.py
"""

import sqlite3
import os
from datetime import datetime

DATABASE = 'data/sandwich.db'

def run_variations_migration():
    """Ejecutar migración del sistema de variaciones"""
    print("Iniciando migración del sistema de variaciones...")
    
    if not os.path.exists(DATABASE):
        print("Base de datos no encontrada. Ejecuta app.py primero.")
        return False
    
    # Hacer backup
    backup_name = f"data/backup_before_variations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.system(f"cp {DATABASE} {backup_name}")
    print(f"Backup creado: {backup_name}")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # 1. Tabla de Grupos de Variaciones
        print("Creando tabla de grupos de variaciones...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variation_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT,
                required INTEGER DEFAULT 0,
                multiple_selection INTEGER DEFAULT 0,
                min_selections INTEGER DEFAULT 0,
                max_selections INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Tabla de Opciones de Variaciones
        print("Creando tabla de opciones de variaciones...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variation_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variation_group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                price_modifier REAL DEFAULT 0,
                ingredient_id INTEGER,
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
            )
        ''')
        
        # 3. Tabla de Relación Producto-Variaciones
        print("Creando tabla de relación producto-variaciones...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_variations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                variation_group_id INTEGER NOT NULL,
                required INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id),
                UNIQUE(product_id, variation_group_id)
            )
        ''')
        
        # 4. Tabla de Variaciones en Órdenes
        print("Creando tabla de variaciones en órdenes...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_item_variations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_item_id INTEGER NOT NULL,
                variation_option_id INTEGER NOT NULL,
                price_modifier REAL DEFAULT 0,
                option_name TEXT NOT NULL,
                FOREIGN KEY (order_item_id) REFERENCES order_items (id),
                FOREIGN KEY (variation_option_id) REFERENCES variation_options (id)
            )
        ''')
        
        # 5. Insertar datos de ejemplo
        print("Insertando grupos de variaciones de ejemplo...")
        
        # Grupo: Tipo de Proteína
        cursor.execute('''
            INSERT OR IGNORE INTO variation_groups 
            (name, display_name, description, required, multiple_selection, max_selections)
            VALUES 
            ('protein_type', 'Tipo de Proteína', 'Elige tu proteína favorita', 1, 0, 1)
        ''')
        
        protein_group_id = cursor.execute(
            'SELECT id FROM variation_groups WHERE name = "protein_type"'
        ).fetchone()[0]
        
        # Opciones de proteínas
        protein_options = [
            ('churrasco', 'Churrasco', 0),
            ('lomito', 'Lomito', 500),
            ('pollo', 'Pollo', -200),
        ]
        
        for i, (name, display_name, price_modifier) in enumerate(protein_options):
            cursor.execute('''
                INSERT OR IGNORE INTO variation_options 
                (variation_group_id, name, display_name, price_modifier, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (protein_group_id, name, display_name, price_modifier, i + 1))
        
        # Grupo: Tamaño
        cursor.execute('''
            INSERT OR IGNORE INTO variation_groups 
            (name, display_name, description, required, multiple_selection, max_selections)
            VALUES 
            ('size', 'Tamaño', 'Elige el tamaño de tu sandwich', 0, 0, 1)
        ''')
        
        size_group_id = cursor.execute(
            'SELECT id FROM variation_groups WHERE name = "size"'
        ).fetchone()[0]
        
        size_options = [
            ('normal', 'Normal', 0),
            ('grande', 'Grande', 800),
            ('familiar', 'Familiar', 1500),
        ]
        
        for i, (name, display_name, price_modifier) in enumerate(size_options):
            cursor.execute('''
                INSERT OR IGNORE INTO variation_options 
                (variation_group_id, name, display_name, price_modifier, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (size_group_id, name, display_name, price_modifier, i + 1))
        
        # 6. Asignar variaciones a productos existentes
        print("Asignando variaciones a productos...")
        
        # Obtener productos que pueden tener proteínas
        cursor.execute('''
            SELECT p.id, p.name 
            FROM products p 
            JOIN categories c ON p.category_id = c.id 
            WHERE c.name IN ('SANDWICH', 'COMPLETOS') AND p.available = 1
        ''')
        sandwich_products = cursor.fetchall()
        
        for product_id, product_name in sandwich_products:
            # Asignar grupo de proteínas (requerido)
            cursor.execute('''
                INSERT OR IGNORE INTO product_variations 
                (product_id, variation_group_id, required, sort_order)
                VALUES (?, ?, 1, 1)
            ''', (product_id, protein_group_id))
            
            # Asignar grupo de tamaño (opcional)
            cursor.execute('''
                INSERT OR IGNORE INTO product_variations 
                (product_id, variation_group_id, required, sort_order)
                VALUES (?, ?, 0, 2)
            ''', (product_id, size_group_id))
            
            print(f"   Configurado: {product_name}")
        
        conn.commit()
        print("Migración completada exitosamente!")
        
        # Estadísticas
        cursor.execute("SELECT COUNT(*) FROM variation_groups WHERE active = 1")
        groups_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM variation_options WHERE active = 1")
        options_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_variations")
        assignments_count = cursor.fetchone()[0]
        
        print(f"Estadísticas:")
        print(f"   - Grupos de variación: {groups_count}")
        print(f"   - Opciones totales: {options_count}")
        print(f"   - Productos configurados: {len(sandwich_products)}")
        print(f"   - Asignaciones: {assignments_count}")
        
        return True
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("MIGRACIÓN DE VARIACIONES DE PRODUCTOS - EPICURO")
    print("=" * 50)
    
    success = run_variations_migration()
    
    if success:
        print("\nMigración completada! Ahora:")
        print("   1. Agrega las rutas al app.py")
        print("   2. Reinicia el servidor")
        print("   3. Prueba las variaciones en Nueva Comanda")
    else:
        print("\nLa migración falló. Revisa los errores.")