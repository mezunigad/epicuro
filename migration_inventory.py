#!/usr/bin/env python3
"""
Migración del sistema de inventario para Epicuro
Ejecutar: python3 migration_inventory.py
"""

import sqlite3
import os
from datetime import datetime

DATABASE = 'data/sandwich.db'

def run_migration():
    """Ejecutar migración del sistema de inventario"""
    print("🔄 Iniciando migración del sistema de inventario...")
    
    if not os.path.exists(DATABASE):
        print("❌ Base de datos no encontrada. Ejecuta app.py primero.")
        return False
    
    # Hacer backup
    backup_name = f"data/backup_before_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.system(f"cp {DATABASE} {backup_name}")
    print(f"✅ Backup creado: {backup_name}")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # 1. Tabla de Proveedores
        print("📦 Creando tabla de proveedores...")
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Tabla de Ingredientes
        print("🥄 Creando tabla de ingredientes...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                unit TEXT NOT NULL DEFAULT 'gr',
                current_stock REAL DEFAULT 0,
                min_stock REAL DEFAULT 0,
                max_stock REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                preferred_supplier_id INTEGER,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (preferred_supplier_id) REFERENCES suppliers (id)
            )
        ''')
        
        # 3. Tabla de Recetas
        print("📋 Creando tabla de recetas...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                name TEXT NOT NULL,
                instructions TEXT,
                yield_quantity REAL DEFAULT 1,
                yield_unit TEXT DEFAULT 'unidad',
                prep_time REAL DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # 4. Tabla de Ingredientes de Recetas
        print("🧾 Creando tabla de ingredientes de recetas...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
            )
        ''')
        
        # 5. Tabla de Compras
        print("🛒 Creando tabla de compras...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                purchase_date DATE NOT NULL,
                expected_date DATE,
                received_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            )
        ''')
        
        # 6. Tabla de Items de Compras
        print("📦 Creando tabla de items de compras...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                ingredient_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                received_quantity REAL DEFAULT 0,
                FOREIGN KEY (purchase_id) REFERENCES purchases (id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
            )
        ''')
        
        # 7. Tabla de Movimientos de Inventario
        print("📊 Creando tabla de movimientos de inventario...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingredient_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_cost REAL,
                reference_type TEXT,
                reference_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients (id)
            )
        ''')
        
        # 8. Insertar datos de ejemplo
        print("🌱 Insertando datos de ejemplo...")
        
        # Proveedores de ejemplo
        sample_suppliers = [
            ('Distribuidora Central', 'Juan Pérez', '+56912345678', 'juan@distcentral.cl', 'Av. Principal 123, Santiago', '12.345.678-9'),
            ('Carnes Premium', 'María González', '+56987654321', 'maria@carnespremium.cl', 'Calle Carnicería 456, Las Condes', '98.765.432-1'),
            ('Verduras Frescas', 'Carlos López', '+56911223344', 'carlos@verdurasfrescas.cl', 'Mercado Central Local 15', '11.223.344-5'),
            ('Panadería San Juan', 'Ana Silva', '+56955667788', 'ana@panaderiasj.cl', 'Av. Panaderos 789, Providencia', '55.667.788-9')
        ]
        
        cursor.executemany('''
            INSERT INTO suppliers (name, contact_person, phone, email, address, tax_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_suppliers)
        
        # Ingredientes de ejemplo
        sample_ingredients = [
            # Carnes
            ('Pechuga de Pollo', 'Pechuga sin hueso', 'kg', 0, 1, 5, 4500, 2),
            ('Carne de Vacuno', 'Lomo liso para churrasco', 'kg', 0, 0.5, 3, 8500, 2),
            ('Jamón', 'Jamón cocido premium', 'kg', 0, 0.3, 2, 6200, 1),
            
            # Vegetales
            ('Palta', 'Palta Hass', 'kg', 0, 2, 10, 2800, 3),
            ('Tomate', 'Tomate redondo', 'kg', 0, 1, 5, 1200, 3),
            ('Lechuga', 'Lechuga criolla', 'unidad', 0, 5, 20, 800, 3),
            ('Porotos Verdes', 'Porotos verdes frescos', 'kg', 0, 0.5, 2, 1800, 3),
            
            # Panes y bases
            ('Pan Hallulla', 'Pan hallulla grande', 'unidad', 0, 20, 100, 350, 4),
            ('Pan Marraqueta', 'Pan marraqueta tradicional', 'unidad', 0, 15, 80, 300, 4),
            
            # Condimentos y salsas
            ('Mayonesa', 'Mayonesa comercial', 'kg', 0, 1, 5, 2200, 1),
            ('Ají Verde', 'Ají verde casero', 'kg', 0, 0.5, 2, 3500, 1),
            ('Aceite', 'Aceite vegetal', 'litro', 0, 1, 5, 1800, 1),
            
            # Bebidas (ingredientes base)
            ('Coca Cola', 'Bebida cola 350ml', 'unidad', 0, 24, 100, 800, 1),
            ('Agua Mineral', 'Agua sin gas 500ml', 'unidad', 0, 24, 100, 600, 1),
            
            # Lácteos
            ('Queso', 'Queso mantecoso', 'kg', 0, 0.5, 3, 5500, 1),
            ('Mantequilla', 'Mantequilla sin sal', 'kg', 0, 0.3, 2, 3200, 1)
        ]
        
        cursor.executemany('''
            INSERT INTO ingredients (name, description, unit, current_stock, min_stock, max_stock, unit_cost, preferred_supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_ingredients)
        
        # Commit cambios
        conn.commit()
        print("✅ Migración completada exitosamente!")
        
        # Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        suppliers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        ingredients_count = cursor.fetchone()[0]
        
        print(f"📊 Estadísticas:")
        print(f"   - Proveedores: {suppliers_count}")
        print(f"   - Ingredientes: {ingredients_count}")
        print(f"   - Tablas creadas: 6")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_migration():
    """Verificar que la migración se ejecutó correctamente"""
    print("\n🔍 Verificando migración...")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    tables_to_check = [
        'suppliers', 'ingredients', 'recipes', 'recipe_ingredients',
        'purchases', 'purchase_items', 'inventory_movements'
    ]
    
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count} registros")
        except Exception as e:
            print(f"❌ {table}: Error - {e}")
    
    conn.close()

if __name__ == "__main__":
    print("🍽️  MIGRACIÓN DEL SISTEMA DE INVENTARIO - EPICURO")
    print("=" * 50)
    
    success = run_migration()
    
    if success:
        verify_migration()
        print("\n🎉 ¡Migración completada! Ahora puedes:")
        print("   1. Reiniciar tu servidor Flask")
        print("   2. Acceder a las nuevas funcionalidades de inventario")
        print("   3. Crear recetas para tus productos")
        print("   4. Gestionar proveedores y compras")
    else:
        print("\n💥 La migración falló. Revisa los errores arriba.")
        print("   Tu base de datos original está respaldada.")
