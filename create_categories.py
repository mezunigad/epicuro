#!/usr/bin/env python3
"""
Script para crear las categorías específicas de Epicuro
Ejecutar: python3 create_categories.py
"""

import sqlite3
import os

DATABASE = 'data/sandwich.db'

def create_categories():
    """Crear las categorías específicas del negocio"""
    print("🏷️  Creando categorías de productos para Epicuro...")
    
    if not os.path.exists(DATABASE):
        print("❌ Base de datos no encontrada. Ejecuta app.py primero.")
        return False
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Definir las categorías con colores específicos
        categories = [
            ('SANDWICH', 'Sándwiches clásicos y gourmet', '#e74c3c'),        # Rojo
            ('COMPLETOS', 'Completos italianos y especiales', '#f39c12'),    # Naranja
            ('ENSALADAS', 'Ensaladas frescas y saludables', '#27ae60'),      # Verde
            ('PAPAS FRITAS', 'Papas fritas y acompañamientos', '#f1c40f'),   # Amarillo
            ('BEBIDAS', 'Bebidas frías y refrescos', '#3498db'),             # Azul
            ('ENERGETICAS', 'Bebidas energéticas y deportivas', '#9b59b6'),  # Púrpura
            ('CAFETERIA', 'Café, té y bebidas calientes', '#8b4513'),        # Café/Marrón
            ('DESAYUNOS', 'Opciones para el desayuno', '#ff6b35'),           # Naranja claro
        ]
        
        # Verificar si ya existen categorías
        cursor.execute('SELECT COUNT(*) FROM categories')
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"⚠️  Ya existen {existing_count} categorías.")
            response = input("¿Quieres eliminar todas y crear las nuevas? (s/N): ")
            if response.lower() == 's':
                cursor.execute('DELETE FROM categories')
                print("🗑️  Categorías anteriores eliminadas.")
            else:
                print("ℹ️  Agregando solo las categorías que no existan...")
        
        # Insertar categorías
        categories_added = 0
        for name, description, color in categories:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (name, description, color, active)
                    VALUES (?, ?, ?, 1)
                ''', (name, description, color))
                
                if cursor.rowcount > 0:
                    categories_added += 1
                    print(f"✅ Creada: {name} ({color})")
                else:
                    print(f"ℹ️  Ya existe: {name}")
                    
            except Exception as e:
                print(f"❌ Error creando {name}: {e}")
        
        conn.commit()
        
        # Mostrar resultado
        cursor.execute('SELECT COUNT(*) FROM categories WHERE active = 1')
        total_categories = cursor.fetchone()[0]
        
        print(f"\n🎉 ¡Completado!")
        print(f"📊 Categorías nuevas agregadas: {categories_added}")
        print(f"📊 Total de categorías activas: {total_categories}")
        
        # Mostrar las categorías creadas
        print(f"\n📋 Categorías en el sistema:")
        cursor.execute('SELECT name, description, color FROM categories WHERE active = 1 ORDER BY name')
        for category in cursor.fetchall():
            print(f"   • {category[0]} - {category[1]} ({category[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def show_color_preview():
    """Mostrar preview de los colores"""
    print("\n🎨 Preview de colores:")
    colors = {
        'SANDWICH': '#e74c3c',      # Rojo
        'COMPLETOS': '#f39c12',     # Naranja  
        'ENSALADAS': '#27ae60',     # Verde
        'PAPAS FRITAS': '#f1c40f',  # Amarillo
        'BEBIDAS': '#3498db',       # Azul
        'ENERGETICAS': '#9b59b6',   # Púrpura
        'CAFETERIA': '#8b4513',     # Café/Marrón
        'DESAYUNOS': '#ff6b35',     # Naranja claro
    }
    
    for name, color in colors.items():
        print(f"   {name:<12} → {color}")

if __name__ == "__main__":
    print("🍽️  CREACIÓN DE CATEGORÍAS - EPICURO")
    print("=" * 40)
    
    show_color_preview()
    print()
    
    success = create_categories()
    
    if success:
        print(f"\n✨ ¡Listo! Ahora puedes:")
        print(f"   1. Ver las categorías en: http://127.0.0.1:5002/categories")
        print(f"   2. Crear productos asignándolos a estas categorías")
        print(f"   3. Las categorías aparecerán en 'Nueva Comanda' para filtrar")
    else:
        print(f"\n💥 Hubo un problema. Revisa los errores arriba.")