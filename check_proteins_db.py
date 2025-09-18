#!/usr/bin/env python3
# ==========================================
# SCRIPT PARA VER Y CONFIGURAR PROTEÍNAS
# ==========================================

import sqlite3
import os

def find_database():
    """Buscar el archivo de base de datos"""
    possible_paths = [
        'database.db',
        'app.db', 
        'sandwich.db',
        'instance/database.db',
        'epicuro.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📍 Base de datos encontrada: {path}")
            return path
    
    print("❌ No se encontró archivo de base de datos")
    return None

def check_database_structure(db_path):
    """Verificar si existen las tablas de variaciones"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar qué tablas existen
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n📊 TABLAS EXISTENTES:")
    print("=" * 30)
    for table in tables:
        print(f"  ✅ {table}")
    
    # Verificar si existen las tablas de variaciones
    required_tables = ['variation_groups', 'variation_options', 'product_variations']
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        print(f"\n❌ FALTAN TABLAS: {', '.join(missing_tables)}")
        return False, conn
    else:
        print(f"\n✅ Todas las tablas de variaciones existen")
        return True, conn

def show_current_proteins(conn):
    """Mostrar las proteínas actuales y sus precios"""
    cursor = conn.cursor()
    
    print("\n🍖 PROTEÍNAS CONFIGURADAS:")
    print("=" * 50)
    
    try:
        # Obtener proteínas del grupo 'protein'
        cursor.execute("""
            SELECT 
                vo.id,
                vo.name,
                vo.display_name,
                vo.price_modifier,
                vo.active,
                vg.display_name as group_name
            FROM variation_options vo
            JOIN variation_groups vg ON vo.variation_group_id = vg.id
            WHERE vg.name IN ('protein', 'protein_type', 'proteina')
            ORDER BY vo.sort_order, vo.name
        """)
        
        proteins = cursor.fetchall()
        
        if proteins:
            print("ID | Nombre      | Precio | Estado")
            print("---|-------------|--------|--------")
            for protein in proteins:
                status = "✅ ACTIVA" if protein[4] else "❌ INACTIVA"
                price = f"${protein[3]}" if protein[3] != 0 else "GRATIS"
                print(f"{protein[0]:2} | {protein[1]:11} | {price:6} | {status}")
        else:
            print("❌ No hay proteínas configuradas")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Probablemente las tablas de variaciones no existen aún")

def show_all_variations(conn):
    """Mostrar todas las variaciones existentes"""
    cursor = conn.cursor()
    
    print("\n🔧 TODAS LAS VARIACIONES:")
    print("=" * 60)
    
    try:
        cursor.execute("""
            SELECT 
                vg.name as group_name,
                vg.display_name as group_display,
                vo.name as option_name,
                vo.display_name as option_display,
                vo.price_modifier,
                vo.active
            FROM variation_groups vg
            LEFT JOIN variation_options vo ON vg.id = vo.variation_group_id
            ORDER BY vg.name, vo.sort_order, vo.name
        """)
        
        variations = cursor.fetchall()
        current_group = None
        
        for variation in variations:
            if variation[0] != current_group:
                current_group = variation[0]
                print(f"\n📂 GRUPO: {variation[1]} ({variation[0]})")
                print("   " + "-" * 40)
            
            if variation[2]:  # Si tiene opciones
                status = "✅" if variation[5] else "❌"
                price = f"${variation[4]}" if variation[4] != 0 else "GRATIS"
                print(f"   {status} {variation[3]:15} | {price}")
            else:
                print("   (Sin opciones configuradas)")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def create_protein_tables(conn):
    """Crear las tablas de variaciones si no existen"""
    cursor = conn.cursor()
    
    print("\n🛠️ CREANDO TABLAS DE VARIACIONES...")
    
    # Tabla de grupos de variación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variation_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            display_name VARCHAR(100) NOT NULL,
            description TEXT,
            required BOOLEAN DEFAULT 0,
            multiple_selection BOOLEAN DEFAULT 0,
            min_selections INTEGER DEFAULT 0,
            max_selections INTEGER DEFAULT 1,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de opciones de variación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variation_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variation_group_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            description TEXT,
            price_modifier DECIMAL(10,2) DEFAULT 0,
            active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id)
        )
    """)
    
    # Tabla de relación producto-variaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variation_group_id INTEGER NOT NULL,
            required BOOLEAN DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
            FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id),
            UNIQUE(product_id, variation_group_id)
        )
    """)
    
    # Tabla de variaciones en órdenes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_item_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id INTEGER NOT NULL,
            variation_option_id INTEGER NOT NULL,
            option_name VARCHAR(100) NOT NULL,
            group_name VARCHAR(100) NOT NULL,
            price_modifier DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_item_id) REFERENCES order_items (id) ON DELETE CASCADE,
            FOREIGN KEY (variation_option_id) REFERENCES variation_options (id)
        )
    """)
    
    conn.commit()
    print("✅ Tablas creadas exitosamente")

def setup_basic_proteins(conn):
    """Configurar las proteínas básicas SIN COSTO"""
    cursor = conn.cursor()
    
    print("\n🥩 CONFIGURANDO PROTEÍNAS BÁSICAS...")
    
    # 1. Crear grupo de proteínas
    cursor.execute("""
        INSERT OR REPLACE INTO variation_groups 
        (id, name, display_name, description, required, multiple_selection, max_selections)
        VALUES (1, 'protein', 'Proteína', 'Tipo de proteína (sin costo adicional)', 1, 0, 1)
    """)
    
    # 2. Configurar proteínas con precio 0 (GRATIS)
    proteins = [
        (1, 'Churrasco', 'Churrasco a la plancha'),
        (2, 'Lomito', 'Lomito de cerdo'),
        (3, 'Pollo', 'Pechuga de pollo'),
    ]
    
    for sort_order, name, description in proteins:
        cursor.execute("""
            INSERT OR REPLACE INTO variation_options 
            (variation_group_id, name, display_name, description, price_modifier, active, sort_order)
            VALUES (1, ?, ?, ?, 0, 1, ?)
        """, (name, name, description, sort_order))
        
        print(f"   ✅ {name}: $0 (GRATIS)")
    
    # 3. Opcional: Crear grupo de extras CON COSTO
    cursor.execute("""
        INSERT OR REPLACE INTO variation_groups 
        (id, name, display_name, description, required, multiple_selection, max_selections)
        VALUES (2, 'extras', 'Extras', 'Ingredientes adicionales opcionales', 0, 1, 5)
    """)
    
    extras = [
        ('Queso', 'Queso cheddar', 300),
        ('Palta', 'Palta fresca', 400),
        ('Tocino', 'Tocino crocante', 500),
        ('Tomate', 'Tomate fresco', 200),
        ('Lechuga', 'Lechuga crispy', 100),
    ]
    
    for sort_order, (name, description, price) in enumerate(extras, 1):
        cursor.execute("""
            INSERT OR REPLACE INTO variation_options 
            (variation_group_id, name, display_name, description, price_modifier, active, sort_order)
            VALUES (2, ?, ?, ?, ?, 1, ?)
        """, (name, name, description, price, sort_order))
        
        print(f"   💰 {name}: +${price}")
    
    conn.commit()
    print("✅ Proteínas y extras configurados")

def assign_proteins_to_sandwiches(conn):
    """Asignar proteínas a productos tipo sandwich"""
    cursor = conn.cursor()
    
    print("\n🔗 ASIGNANDO PROTEÍNAS A SANDWICHES...")
    
    try:
        # Buscar productos que podrían ser sandwiches
        cursor.execute("""
            SELECT p.id, p.name, c.name as category
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE (c.name LIKE '%SANDWICH%' OR c.name LIKE '%COMPLETO%' 
                   OR p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%')
            AND p.is_active = 1
        """)
        
        sandwich_products = cursor.fetchall()
        
        if sandwich_products:
            for product in sandwich_products:
                # Asignar grupo de proteínas (requerido)
                cursor.execute("""
                    INSERT OR IGNORE INTO product_variations 
                    (product_id, variation_group_id, required, sort_order)
                    VALUES (?, 1, 1, 1)
                """, (product[0],))
                
                # Asignar grupo de extras (opcional)
                cursor.execute("""
                    INSERT OR IGNORE INTO product_variations 
                    (product_id, variation_group_id, required, sort_order)
                    VALUES (?, 2, 0, 2)
                """, (product[0],))
                
                print(f"   ✅ {product[1]} ({product[2]})")
            
            conn.commit()
            print(f"✅ {len(sandwich_products)} productos configurados con proteínas")
        else:
            print("⚠️  No se encontraron productos tipo sandwich")
            print("💡 Verifica que tengas productos en categorías SANDWICH o COMPLETO")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def interactive_menu(conn):
    """Menú interactivo para gestionar proteínas"""
    while True:
        print("\n" + "="*50)
        print("🍖 GESTIÓN DE PROTEÍNAS - MENÚ PRINCIPAL")
        print("="*50)
        print("1. 👀 Ver proteínas actuales")
        print("2. 🔧 Ver todas las variaciones")
        print("3. 🛠️  Configurar proteínas básicas (GRATIS)")
        print("4. 🔗 Asignar proteínas a sandwiches")
        print("5. 💰 Cambiar precio de una proteína")
        print("6. ➕ Agregar nueva proteína")
        print("7. 🔄 Reiniciar configuración completa")
        print("8. 🚪 Salir")
        print("="*50)
        
        choice = input("Selecciona una opción (1-8): ").strip()
        
        if choice == '1':
            show_current_proteins(conn)
        elif choice == '2':
            show_all_variations(conn)
        elif choice == '3':
            setup_basic_proteins(conn)
        elif choice == '4':
            assign_proteins_to_sandwiches(conn)
        elif choice == '5':
            change_protein_price(conn)
        elif choice == '6':
            add_new_protein(conn)
        elif choice == '7':
            reset_all_configuration(conn)
        elif choice == '8':
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")
        
        input("\nPresiona ENTER para continuar...")

def change_protein_price(conn):
    """Cambiar el precio de una proteína específica"""
    cursor = conn.cursor()
    
    # Mostrar proteínas disponibles
    cursor.execute("""
        SELECT vo.id, vo.name, vo.price_modifier
        FROM variation_options vo
        JOIN variation_groups vg ON vo.variation_group_id = vg.id
        WHERE vg.name = 'protein'
    """)
    
    proteins = cursor.fetchall()
    
    if not proteins:
        print("❌ No hay proteínas configuradas")
        return
    
    print("\n🍖 PROTEÍNAS DISPONIBLES:")
    for protein in proteins:
        current_price = f"${protein[2]}" if protein[2] != 0 else "GRATIS"
        print(f"  {protein[0]}. {protein[1]} (actual: {current_price})")
    
    try:
        protein_id = int(input("\nID de la proteína a modificar: "))
        new_price = float(input("Nuevo precio (0 para gratis): "))
        
        cursor.execute("""
            UPDATE variation_options 
            SET price_modifier = ? 
            WHERE id = ?
        """, (new_price, protein_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            price_text = f"${new_price}" if new_price != 0 else "GRATIS"
            print(f"✅ Precio actualizado a {price_text}")
        else:
            print("❌ Proteína no encontrada")
            
    except ValueError:
        print("❌ Valores inválidos")
    except Exception as e:
        print(f"❌ Error: {e}")

def add_new_protein(conn):
    """Agregar una nueva proteína"""
    cursor = conn.cursor()
    
    try:
        name = input("Nombre de la nueva proteína: ").strip()
        if not name:
            print("❌ El nombre no puede estar vacío")
            return
        
        price = float(input("Precio (0 para gratis): "))
        
        cursor.execute("""
            INSERT INTO variation_options 
            (variation_group_id, name, display_name, price_modifier, active, sort_order)
            VALUES (1, ?, ?, ?, 1, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM variation_options WHERE variation_group_id = 1))
        """, (name, name, price))
        
        conn.commit()
        price_text = f"${price}" if price != 0 else "GRATIS"
        print(f"✅ Proteína '{name}' agregada con precio {price_text}")
        
    except ValueError:
        print("❌ Precio inválido")
    except Exception as e:
        print(f"❌ Error: {e}")

def reset_all_configuration(conn):
    """Reiniciar toda la configuración de variaciones"""
    confirm = input("⚠️  ¿Estás seguro? Esto eliminará TODAS las variaciones (s/N): ")
    
    if confirm.lower() == 's':
        cursor = conn.cursor()
        
        # Eliminar todo
        cursor.execute("DELETE FROM order_item_variations")
        cursor.execute("DELETE FROM product_variations") 
        cursor.execute("DELETE FROM variation_options")
        cursor.execute("DELETE FROM variation_groups")
        
        conn.commit()
        print("🗑️  Configuración eliminada")
        
        # Reconfigurar desde cero
        setup_basic_proteins(conn)
        assign_proteins_to_sandwiches(conn)
        
        print("✅ Configuración reiniciada")
    else:
        print("❌ Operación cancelada")

# ==========================================
# SCRIPT PRINCIPAL
# ==========================================

def main():
    print("🍖 GESTOR DE PROTEÍNAS - SISTEMA EPICURO")
    print("=" * 60)
    
    # 1. Encontrar base de datos
    db_path = find_database()
    if not db_path:
        print("💡 Crea una base de datos primero ejecutando tu aplicación Flask")
        return
    
    # 2. Verificar estructura
    has_tables, conn = check_database_structure(db_path)
    
    if not has_tables:
        print("\n🛠️  Las tablas de variaciones no existen")
        create_choice = input("¿Crear las tablas necesarias? (s/N): ")
        if create_choice.lower() == 's':
            create_protein_tables(conn)
            setup_basic_proteins(conn)
            assign_proteins_to_sandwiches(conn)
        else:
            print("❌ No se pueden gestionar proteínas sin las tablas")
            conn.close()
            return
    
    # 3. Mostrar estado actual
    show_current_proteins(conn)
    show_all_variations(conn)
    
    # 4. Menú interactivo
    interactive_menu(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
