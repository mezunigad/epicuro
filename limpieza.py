#!/usr/bin/env python3
"""
Script para limpiar productos insertados incorrectamente en el sistema Epicuro
Ejecutar: python cleanup_products.py
"""

import sqlite3
import os

# Configuración de la base de datos
DATABASE = 'data/sandwich.db'

# Lista de productos que se insertaron (para eliminación selectiva)
products_to_remove = [
    'AGUA CON GAS', 'AGUA MINERAL', 'COCA COLA', 'FANTA', 'SPRITE', 'KEM PIÑA', 
    'LIMON SODA', 'PEPSI', 'CAFÉ + SÁNDWICH ELECCIÓN', 'CAFÉ AMERICANO MEDIANO',
    'CAFÉ AMERICANO GRANDE', 'CAFÉ EXPRESO', 'CAPPUCCINO MEDIANO', 'CAPPUCCINO GRANDE',
    'CAPUCCINO VAINILLA MEDIANO', 'CAPPUCCINO VAINILLA GRANDE', 'CHOCOLATE FUERTE MEDIANO',
    'CHOCOLATE FUERTE GRANDE', 'CORTADO MEDIANO', 'CORTADO GRANDE', 'LATTE MACCHIATO MEDIANO',
    'LATTE MACCHIATO GRANDE', 'MOCACCINO MEDIANO', 'MOCACCINO GRANDE', 'VAINILLA FRANCESA MEDIANA',
    'VAINILLA FRANCESA GRANDE', 'TÉ NEGRO', 'TÉ VERDE', 'COMPLETO DINÁMICO',
    'COMPLETO EPICURO', 'COMPLETO ITALIANO', 'RED BULL ORIGINAL', 'RED BULL SIN AZÚCAR',
    'WATTS DURAZNO', 'WATTS FRUTILLA', 'WATTS NARANJA', 'WATTS PIÑA',
    'DESAYUNO - MIGA HUEVO MAYO', 'DESAYUNO - JAMÓN QUESO', 'DESAYUNO - MECHADA QUESO',
    'DESAYUNO - PASTA DE POLLO Y QUESO CREMA', 'CONSOME', 'SANDWICH A LO POBRE',
    'SANDWICH CHACARERO', 'SANDWICH COLCHAGUINO', 'SANDWICH EPICURO', 'SANDWICH ITALIANO',
    'SANDWICH LUCO DE LUJO', 'SANDWICH PICARO', 'PAPA CHICA', 'PAPA MEDIANA', 'PAPA GRANDE',
    'ENSALADA CÉSAR', 'ENSALADA EPICURO', 'ENSALADA VEGGIE'
]

def create_connection():
    """Crear conexión a la base de datos"""
    if not os.path.exists(DATABASE):
        print("Error: La base de datos no existe")
        return None
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def backup_database():
    """Crear respaldo de la base de datos antes de limpiar"""
    try:
        import shutil
        backup_name = f"data/sandwich_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DATABASE, backup_name)
        print(f"✓ Respaldo creado: {backup_name}")
        return True
    except Exception as e:
        print(f"✗ Error creando respaldo: {e}")
        return False

def option_1_delete_specific_products(conn):
    """Opción 1: Eliminar solo los productos específicos que insertamos"""
    cursor = conn.cursor()
    
    print("OPCIÓN 1: Eliminando productos específicos...")
    print("="*50)
    
    deleted_count = 0
    
    for product_name in products_to_remove:
        try:
            cursor.execute('DELETE FROM products WHERE name = ?', (product_name,))
            if cursor.rowcount > 0:
                print(f"✓ Eliminado: {product_name}")
                deleted_count += 1
            else:
                print(f"- No encontrado: {product_name}")
        except Exception as e:
            print(f"✗ Error eliminando {product_name}: {e}")
    
    conn.commit()
    print(f"\nTotal productos eliminados: {deleted_count}")

def option_2_delete_all_products(conn):
    """Opción 2: Eliminar TODOS los productos"""
    cursor = conn.cursor()
    
    print("OPCIÓN 2: Eliminando TODOS los productos...")
    print("="*50)
    
    try:
        # Contar productos antes
        count_before = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        print(f"Productos antes de limpiar: {count_before}")
        
        # Eliminar todos los productos
        cursor.execute('DELETE FROM products')
        
        # Reiniciar el contador de ID
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="products"')
        
        conn.commit()
        
        # Verificar
        count_after = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        print(f"Productos después de limpiar: {count_after}")
        print("✓ Todos los productos han sido eliminados")
        
    except Exception as e:
        print(f"✗ Error eliminando productos: {e}")

def option_3_delete_recent_products(conn):
    """Opción 3: Eliminar productos creados hoy"""
    cursor = conn.cursor()
    
    print("OPCIÓN 3: Eliminando productos creados hoy...")
    print("="*50)
    
    try:
        # Contar productos de hoy
        count_today = cursor.execute('''
            SELECT COUNT(*) FROM products 
            WHERE DATE(created_at) = DATE('now')
        ''').fetchone()[0]
        
        print(f"Productos creados hoy: {count_today}")
        
        if count_today > 0:
            # Mostrar productos que se van a eliminar
            products_today = cursor.execute('''
                SELECT name FROM products 
                WHERE DATE(created_at) = DATE('now')
            ''').fetchall()
            
            print("Productos que se eliminarán:")
            for product in products_today:
                print(f"  - {product['name']}")
            
            # Eliminar
            cursor.execute('''
                DELETE FROM products 
                WHERE DATE(created_at) = DATE('now')
            ''')
            
            conn.commit()
            print(f"✓ {count_today} productos eliminados")
        else:
            print("No hay productos creados hoy para eliminar")
            
    except Exception as e:
        print(f"✗ Error eliminando productos de hoy: {e}")

def show_current_status(conn):
    """Mostrar estado actual de la base de datos"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("ESTADO ACTUAL DE LA BASE DE DATOS")
    print("="*50)
    
    # Total de productos
    total_products = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    print(f"Total productos: {total_products}")
    
    # Productos por categoría
    cursor.execute('''
        SELECT c.name, COUNT(p.id) as count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id
        GROUP BY c.id, c.name
        ORDER BY c.name
    ''')
    
    print("\nProductos por categoría:")
    for row in cursor.fetchall():
        print(f"  {row['name']}: {row['count']} productos")

def main():
    """Función principal con menú de opciones"""
    print("SCRIPT DE LIMPIEZA - EPICURO")
    print("="*50)
    print("ADVERTENCIA: Este script eliminará datos de tu base de datos")
    print("="*50)
    
    # Conectar a la base de datos
    conn = create_connection()
    if not conn:
        return
    
    # Mostrar estado actual
    show_current_status(conn)
    
    print("\nOPCIONES DE LIMPIEZA:")
    print("1. Eliminar solo los productos específicos que insertamos")
    print("2. Eliminar TODOS los productos (cuidado!)")
    print("3. Eliminar solo productos creados hoy")
    print("4. Solo mostrar estado actual (no eliminar nada)")
    print("5. Salir sin hacer nada")
    
    try:
        choice = input("\nSelecciona una opción (1-5): ").strip()
        
        if choice == '1':
            confirm = input("¿Confirmas eliminar los productos específicos? (sí/no): ").lower()
            if confirm in ['sí', 'si', 'yes', 'y']:
                option_1_delete_specific_products(conn)
                show_current_status(conn)
            else:
                print("Operación cancelada")
                
        elif choice == '2':
            print("\n⚠️  ADVERTENCIA: Esto eliminará TODOS los productos")
            confirm = input("Escribe 'ELIMINAR TODO' para confirmar: ")
            if confirm == 'ELIMINAR TODO':
                option_2_delete_all_products(conn)
                show_current_status(conn)
            else:
                print("Operación cancelada (confirmación incorrecta)")
                
        elif choice == '3':
            confirm = input("¿Confirmas eliminar productos creados hoy? (sí/no): ").lower()
            if confirm in ['sí', 'si', 'yes', 'y']:
                option_3_delete_recent_products(conn)
                show_current_status(conn)
            else:
                print("Operación cancelada")
                
        elif choice == '4':
            print("Estado mostrado arriba. No se realizaron cambios.")
            
        elif choice == '5':
            print("Saliendo sin realizar cambios")
            
        else:
            print("Opción inválida")
            
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
