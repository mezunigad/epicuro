#!/usr/bin/env python3
"""
Script de Importación de Productos a Epicuro
Extrae productos de una BD externa y los normaliza al esquema actual

Uso:
    python3 import_products.py --source database.db --dry-run
    python3 import_products.py --source database.db --import
    python3 import_products.py --csv productos.csv --import
"""

import sqlite3
import argparse
import json
import csv
from datetime import datetime
from decimal import Decimal
import os
import sys

class ProductImporter:
    def __init__(self, target_db_path='epicuro.db'):
        self.target_db_path = target_db_path
        self.categories_map = {}
        self.imported_count = 0
        self.error_count = 0
        self.errors = []
        
    def connect_target_db(self):
        """Conectar a la base de datos objetivo (Epicuro)"""
        return sqlite3.connect(self.target_db_path)
    
    def connect_source_db(self, source_path):
        """Conectar a la base de datos origen"""
        return sqlite3.connect(source_path)
    
    def load_categories_map(self):
        """Cargar mapeo de categorías existentes"""
        conn = self.connect_target_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name FROM categories')
        categories = cursor.fetchall()
        
        for cat_id, cat_name in categories:
            self.categories_map[cat_name.upper()] = cat_id
        
        conn.close()
        print(f"📂 Categorías cargadas: {list(self.categories_map.keys())}")
        
    def create_category_if_not_exists(self, category_name):
        """Crear categoría si no existe"""
        if not category_name:
            return 1  # Categoría por defecto
            
        category_upper = category_name.upper()
        
        if category_upper in self.categories_map:
            return self.categories_map[category_upper]
        
        # Crear nueva categoría
        conn = self.connect_target_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO categories (name, description)
            VALUES (?, ?)
        ''', (category_upper, f'Categoría importada: {category_name}'))
        
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.categories_map[category_upper] = category_id
        print(f"✅ Nueva categoría creada: {category_upper} (ID: {category_id})")
        
        return category_id
    
    def normalize_price(self, price_value):
        """Normalizar precio a decimal"""
        if not price_value:
            return 0.0
        
        # Limpiar formato de precio
        if isinstance(price_value, str):
            # Remover símbolos de moneda y espacios
            price_clean = price_value.replace('$', '').replace(',', '').replace(' ', '')
            try:
                return float(price_clean)
            except ValueError:
                return 0.0
        
        return float(price_value)
    
    def extract_from_database(self, source_db_path, table_name='products'):
        """Extraer productos de base de datos SQLite"""
        try:
            conn = self.connect_source_db(source_db_path)
            cursor = conn.cursor()
            
            # Detectar estructura de la tabla
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"🔍 Columnas detectadas: {columns}")
            
            # Extraer todos los productos
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            products = []
            for row in rows:
                product = dict(zip(columns, row))
                products.append(self.normalize_product_data(product))
            
            conn.close()
            print(f"📊 Productos extraídos: {len(products)}")
            return products
            
        except Exception as e:
            print(f"❌ Error extrayendo de BD: {e}")
            return []
    
    def extract_from_csv(self, csv_path):
        """Extraer productos de archivo CSV"""
        products = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    product = self.normalize_product_data(row)
                    if product:
                        products.append(product)
            
            print(f"📊 Productos extraídos del CSV: {len(products)}")
            return products
            
        except Exception as e:
            print(f"❌ Error leyendo CSV: {e}")
            return []
    
    def normalize_product_data(self, raw_data):
        """Normalizar datos de producto al esquema actual"""
        
        # Mapeos comunes de nombres de campos
        field_mappings = {
            # Nombre del producto
            'name': ['name', 'nombre', 'producto', 'title', 'item_name'],
            'description': ['description', 'descripcion', 'desc', 'details'],
            'price': ['price', 'precio', 'cost', 'valor', 'amount'],
            'cost': ['cost', 'costo', 'cost_price', 'precio_costo'],
            'category': ['category', 'categoria', 'type', 'tipo', 'group'],
            'available': ['available', 'disponible', 'active', 'activo', 'enabled']
        }
        
        normalized = {}
        
        # Normalizar campos
        for target_field, possible_names in field_mappings.items():
            value = None
            
            for possible_name in possible_names:
                if possible_name in raw_data:
                    value = raw_data[possible_name]
                    break
                # Buscar case-insensitive
                for key in raw_data:
                    if key.lower() == possible_name.lower():
                        value = raw_data[key]
                        break
                if value is not None:
                    break
            
            normalized[target_field] = value
        
        # Validaciones y limpieza
        if not normalized.get('name'):
            print(f"⚠️  Producto sin nombre: {raw_data}")
            return None
        
        # Limpiar nombre
        normalized['name'] = str(normalized['name']).strip().upper()
        
        # Normalizar precio
        normalized['price'] = self.normalize_price(normalized.get('price', 0))
        normalized['cost'] = self.normalize_price(normalized.get('cost', 0))
        
        # Normalizar disponibilidad
        available = normalized.get('available', True)
        if isinstance(available, str):
            normalized['available'] = available.lower() in ['true', '1', 'yes', 'si', 'disponible', 'active']
        else:
            normalized['available'] = bool(available)
        
        return normalized
    
    def import_product(self, product_data, dry_run=False):
        """Importar un producto individual"""
        try:
            # Obtener o crear categoría
            category_id = self.create_category_if_not_exists(product_data.get('category'))
            
            if dry_run:
                print(f"🔄 [DRY-RUN] Importaría: {product_data['name']} - ${product_data['price']} - Cat: {category_id}")
                return True
            
            # Insertar producto
            conn = self.connect_target_db()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO products (name, description, price, cost, category_id, available, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data['name'],
                product_data.get('description', ''),
                product_data['price'],
                product_data.get('cost', 0),
                category_id,
                product_data['available'],
                datetime.now()
            ))
            
            product_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ Producto importado: {product_data['name']} (ID: {product_id})")
            self.imported_count += 1
            return True
            
        except Exception as e:
            error_msg = f"❌ Error importando {product_data.get('name', 'UNKNOWN')}: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            self.error_count += 1
            return False
    
    def import_products(self, products, dry_run=False):
        """Importar lista completa de productos"""
        print(f"\n🚀 {'Simulación de importación' if dry_run else 'Iniciando importación'}")
        print(f"📊 Total productos a procesar: {len(products)}")
        
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}]", end=" ")
            self.import_product(product, dry_run)
        
        # Resumen
        print(f"\n📈 RESUMEN DE IMPORTACIÓN:")
        print(f"✅ Importados exitosamente: {self.imported_count}")
        print(f"❌ Errores: {self.error_count}")
        
        if self.errors:
            print(f"\n🔍 DETALLE DE ERRORES:")
            for error in self.errors:
                print(f"  • {error}")
    
    def show_preview(self, products, limit=5):
        """Mostrar vista previa de productos a importar"""
        print(f"\n🔍 VISTA PREVIA (primeros {limit} productos):")
        print("-" * 80)
        
        for i, product in enumerate(products[:limit]):
            print(f"\n[{i+1}] {product['name']}")
            print(f"    💰 Precio: ${product['price']}")
            print(f"    🏷️  Categoría: {product.get('category', 'Sin categoría')}")
            print(f"    📝 Descripción: {product.get('description', 'Sin descripción')[:50]}...")
            print(f"    ✅ Disponible: {'Sí' if product['available'] else 'No'}")
        
        if len(products) > limit:
            print(f"\n... y {len(products) - limit} productos más")

def main():
    parser = argparse.ArgumentParser(description='Importar productos a Epicuro')
    parser.add_argument('--source', required=True, help='Ruta de la BD/CSV origen')
    parser.add_argument('--table', default='products', help='Nombre de la tabla (para BD)')
    parser.add_argument('--target', default='epicuro.db', help='BD objetivo')
    parser.add_argument('--dry-run', action='store_true', help='Solo simular, no importar')
    parser.add_argument('--import', action='store_true', dest='do_import', help='Ejecutar importación')
    parser.add_argument('--preview', type=int, default=5, help='Número de productos en vista previa')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.do_import:
        print("❌ Debes especificar --dry-run o --import")
        return
    
    # Inicializar importador
    importer = ProductImporter(args.target)
    importer.load_categories_map()
    
    # Detectar tipo de archivo y extraer datos
    if args.source.endswith('.csv'):
        products = importer.extract_from_csv(args.source)
    else:
        products = importer.extract_from_database(args.source, args.table)
    
    if not products:
        print("❌ No se encontraron productos para importar")
        return
    
    # Mostrar vista previa
    importer.show_preview(products, args.preview)
    
    # Confirmar importación
    if args.do_import:
        confirm = input(f"\n¿Importar {len(products)} productos? [y/N]: ")
        if confirm.lower() != 'y':
            print("Importación cancelada")
            return
    
    # Ejecutar importación
    importer.import_products(products, dry_run=args.dry_run)

if __name__ == '__main__':
    main()
