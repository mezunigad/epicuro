#!/usr/bin/env python3
# migrate_db.py - Migración simple

import sqlite3
import os

# Buscar base de datos
db_files = ['database.db', 'sandwich.db', 'app.db', 'epicuro.db']
db_path = None

for path in db_files:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ No se encontró base de datos")
    exit(1)

print(f"📍 Migrando: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Creando tablas de variaciones...")
    
    # Crear tablas de variaciones
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS variation_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            display_name VARCHAR(150) NOT NULL,
            description TEXT,
            icon VARCHAR(10) DEFAULT '⚙️',
            input_type VARCHAR(20) DEFAULT 'radio',
            is_required BOOLEAN DEFAULT 0,
            allow_multiple BOOLEAN DEFAULT 0,
            min_selections INTEGER DEFAULT 0,
            max_selections INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS variation_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variation_group_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            display_name VARCHAR(150) NOT NULL,
            description TEXT,
            price_modifier DECIMAL(10,2) DEFAULT 0,
            color_code VARCHAR(7),
            image_url VARCHAR(255),
            is_default BOOLEAN DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id)
        );
        
        CREATE TABLE IF NOT EXISTS product_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variation_group_id INTEGER NOT NULL,
            is_required BOOLEAN DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id),
            UNIQUE(product_id, variation_group_id)
        );
        
        CREATE TABLE IF NOT EXISTS order_item_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id INTEGER NOT NULL,
            variation_option_id INTEGER NOT NULL,
            option_name VARCHAR(150) NOT NULL,
            group_name VARCHAR(150) NOT NULL,
            price_modifier DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_item_id) REFERENCES order_items (id),
            FOREIGN KEY (variation_option_id) REFERENCES variation_options (id)
        );
    """)
    
    # Verificar si hay grupos existentes
    cursor.execute("SELECT COUNT(*) FROM variation_groups")
    existing = cursor.fetchone()[0]
    
    if existing == 0:
        print("🍖 Configurando proteínas...")
        
        # Grupo: Proteínas (GRATIS)
        cursor.execute("""
            INSERT INTO variation_groups 
            (name, display_name, description, icon, input_type, is_required, sort_order)
            VALUES ('protein_type', 'Tipo de Proteína', 'Elige tu proteína favorita', '🥩', 'radio', 1, 1)
        """)
        protein_id = cursor.lastrowid
        
        # Opciones de proteína (todas gratis)
        proteins = [
            ('churrasco', 'Churrasco', 0, 1),
            ('lomito', 'Lomito', 0, 2),
            ('pollo', 'Pollo', 0, 3)
        ]
        
        for name, display_name, price, order in proteins:
            cursor.execute("""
                INSERT INTO variation_options 
                (variation_group_id, name, display_name, price_modifier, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (protein_id, name, display_name, price, order))
        
        print("➕ Configurando extras...")
        
        # Grupo: Extras (CON COSTO)
        cursor.execute("""
            INSERT INTO variation_groups 
            (name, display_name, description, icon, input_type, is_required, allow_multiple, max_selections, sort_order)
            VALUES ('extras', 'Extras', 'Ingredientes adicionales', '➕', 'checkbox', 0, 1, 5, 2)
        """)
        extras_id = cursor.lastrowid
        
        # Opciones de extras (con costo)
        extras = [
            ('queso', 'Queso', 400, 1),
            ('palta', 'Palta', 500, 2),
            ('tocino', 'Tocino', 600, 3)
        ]
        
        for name, display_name, price, order in extras:
            cursor.execute("""
                INSERT INTO variation_options 
                (variation_group_id, name, display_name, price_modifier, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (extras_id, name, display_name, price, order))
        
        print("🔗 Asignando a productos...")
        
        # Buscar productos tipo sandwich
        cursor.execute("""
            SELECT p.id, p.name FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE (p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%' 
                OR p.name LIKE '%BARROS%' OR p.name LIKE '%ITALIANO%' 
                OR p.name LIKE '%CHACARERO%' OR c.name LIKE '%SANDWICH%')
            AND p.available = 1
        """)
        sandwiches = cursor.fetchall()
        
        for product_id, product_name in sandwiches:
            # Asignar proteína (requerida)
            cursor.execute("""
                INSERT OR IGNORE INTO product_variations 
                (product_id, variation_group_id, is_required, sort_order)
                VALUES (?, ?, 1, 1)
            """, (product_id, protein_id))
            
            # Asignar extras (opcional)
            cursor.execute("""
                INSERT OR IGNORE INTO product_variations 
                (product_id, variation_group_id, is_required, sort_order)
                VALUES (?, ?, 0, 2)
            """, (product_id, extras_id))
            
            print(f"   ✅ {product_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 ¡Migración completada exitosamente!")
    print(f"📊 Base de datos: {db_path}")
    print(f"✅ Tablas de variaciones creadas")
    print(f"✅ Proteínas configuradas SIN COSTO")
    print(f"✅ Productos asignados automáticamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
