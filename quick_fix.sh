#!/bin/bash
# ==========================================
# SCRIPT DE SOLUCIÓN RÁPIDA
# ==========================================

echo "🔧 SOLUCIONANDO PROBLEMAS DE EPICURO..."

# 1. Crear script de migración
cat > migrate_db.py << 'EOF'
import sqlite3
import os

# Buscar base de datos
possible_paths = ['database.db', 'sandwich.db', 'app.db', 'epicuro.db']
db_path = None

for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ No se encontró base de datos")
    exit(1)

print(f"📍 Actualizando: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear tablas de variaciones
print("🔧 Creando tablas...")

cursor.execute("""
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
    )
""")

cursor.execute("""
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
    )
""")

cursor.execute("""
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
    )
""")

cursor.execute("""
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
    )
""")

# Verificar si hay datos
existing = cursor.execute("SELECT COUNT(*) FROM variation_groups").fetchone()[0]

if existing == 0:
    print("🔧 Agregando variaciones de ejemplo...")
    
    # Proteínas
    cursor.execute("""
        INSERT INTO variation_groups 
        (name, display_name, description, icon, input_type, is_required, sort_order)
        VALUES ('protein_type', 'Tipo de Proteína', 'Elige tu proteína favorita', '🥩', 'radio', 1, 1)
    """)
    protein_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order) VALUES (?, 'churrasco', 'Churrasco', 0, 1)", (protein_id,))
    cursor.execute("INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order) VALUES (?, 'lomito', 'Lomito', 0, 2)", (protein_id,))
    cursor.execute("INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order) VALUES (?, 'pollo', 'Pollo', 0, 3)", (protein_id,))
    
    # Extras
    cursor.execute("""
        INSERT INTO variation_groups 
        (name, display_name, description, icon, input_type, is_required, allow_multiple, max_selections, sort_order)
        VALUES ('extras', 'Extras', 'Ingredientes adicionales', '➕', 'checkbox', 0, 1, 5, 2)
    """)
    extras_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order) VALUES (?, 'queso', 'Queso', 400, 1)", (extras_id,))
    cursor.execute("INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order) VALUES (?, 'palta', 'Palta', 500, 2)", (extras_id,))
    cursor.execute("INSERT INTO variation_options (variation_group_id, name, display_name, price_modifier, sort_order) VALUES (?, 'tocino', 'Tocino', 600, 3)", (extras_id,))

conn.commit()
conn.close()

print("✅ Base de datos actualizada exitosamente!")
EOF

# 2. Ejecutar migración
echo "📊 Ejecutando migración de base de datos..."
python3 migrate_db.py

# 3. Modificar puerto en app.py
echo "🔧 Cambiando puerto a 5001..."
sed -i '' 's/port=5000/port=5001/g' app.py

echo ""
echo "✅ PROBLEMAS SOLUCIONADOS:"
echo "  • Base de datos actualizada con tablas de variaciones"
echo "  • Puerto cambiado a 5001"
echo ""
echo "🚀 Ahora ejecuta:"
echo "  python3 app.py"
echo ""
echo "📍 Y ve a: http://localhost:5001"
