import pandas as pd
import sqlite3
import datetime
from pytz import timezone
import os
import json

def import_sales_from_excel(excel_file_path, db_path='data/sandwich.db'):
    """
    Importar ventas desde archivo Excel al sistema Epicuro
    """
    print("=== INICIANDO IMPORTACIÓN DE VENTAS ===")
    
    # Configurar zona horaria de Chile
    CHILE_TZ = timezone('America/Santiago')
    
    try:
        # Leer archivo Excel
        print(f"Leyendo archivo: {excel_file_path}")
        df = pd.read_excel(excel_file_path, sheet_name='Detalle de Ventas')
        
        print(f"Datos encontrados: {len(df)} items en {df['ID'].nunique()} órdenes")
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear backup antes de importar
        backup_orders = pd.read_sql_query("SELECT * FROM orders", conn)
        backup_items = pd.read_sql_query("SELECT * FROM order_items", conn)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_orders.to_csv(f'backup_orders_{timestamp}.csv', index=False)
        backup_items.to_csv(f'backup_order_items_{timestamp}.csv', index=False)
        print(f"Backup creado: backup_orders_{timestamp}.csv")
        
        # Agrupar datos por ID de orden
        orders_data = df.groupby('ID').agg({
            'Fecha': 'first',
            'Cliente': 'first',
            'Total': 'sum'
        }).reset_index()
        
        # Estadísticas antes de importar
        existing_orders = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        print(f"Órdenes existentes en BD: {existing_orders}")
        
        orders_imported = 0
        items_imported = 0
        errors = []
        
        # Procesar cada orden
        for _, order_row in orders_data.iterrows():
            try:
                order_id_excel = order_row['ID']
                fecha_str = str(order_row['Fecha'])
                cliente = order_row['Cliente'] if pd.notna(order_row['Cliente']) else 'Cliente Importado'
                total_orden = order_row['Total']
                
                # Convertir fecha
                try:
                    if 'T' in fecha_str:
                        fecha_dt = datetime.datetime.fromisoformat(fecha_str.replace('T', ' '))
                    else:
                        fecha_dt = datetime.datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                except:
                    # Si falla, usar fecha actual
                    fecha_dt = datetime.datetime.now()
                    print(f"Warning: No se pudo parsear fecha para orden {order_id_excel}, usando fecha actual")
                
                # Generar número de orden único
                order_number = f"IMP-{order_id_excel}-{fecha_dt.strftime('%Y%m%d%H%M')}"
                
                # Verificar si la orden ya existe
                existing = cursor.execute(
                    "SELECT id FROM orders WHERE order_number = ?", 
                    (order_number,)
                ).fetchone()
                
                if existing:
                    print(f"Orden {order_number} ya existe, saltando...")
                    continue
                
                # Insertar orden principal
                cursor.execute('''
                    INSERT INTO orders (
                        order_number, customer_name, customer_phone, 
                        subtotal, discount, total_amount, status, 
                        payment_method, notes, order_type, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order_number,
                    cliente,
                    '',  # customer_phone
                    total_orden,  # subtotal
                    0,  # discount
                    total_orden,  # total_amount
                    'completed',  # status
                    'efectivo',  # payment_method
                    f'Importado desde Excel - ID original: {order_id_excel}',  # notes
                    'dine_in',  # order_type
                    fecha_dt.strftime('%Y-%m-%d %H:%M:%S'),  # created_at
                    fecha_dt.strftime('%Y-%m-%d %H:%M:%S')   # updated_at
                ))
                
                new_order_id = cursor.lastrowid
                orders_imported += 1
                
                # Obtener items de esta orden
                order_items = df[df['ID'] == order_id_excel]
                
                # Insertar cada item
                for _, item_row in order_items.iterrows():
                    producto = item_row['Producto']
                    categoria = item_row['Categoría'] if pd.notna(item_row['Categoría']) else 'Sin categoría'
                    cantidad = int(item_row['Cantidad']) if pd.notna(item_row['Cantidad']) else 1
                    precio_unitario = float(item_row['Precio']) if pd.notna(item_row['Precio']) else 0
                    total_item = float(item_row['Total']) if pd.notna(item_row['Total']) else 0
                    
                    # Buscar si el producto existe en la BD
                    product_id = cursor.execute(
                        "SELECT id FROM products WHERE UPPER(name) = UPPER(?)", 
                        (producto,)
                    ).fetchone()
                    
                    product_id = product_id[0] if product_id else None
                    
                    cursor.execute('''
                        INSERT INTO order_items (
                            order_id, product_id, product_name, quantity, 
                            unit_price, total_price, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_order_id,
                        product_id,
                        producto,
                        cantidad,
                        precio_unitario,
                        total_item,
                        f'Categoría: {categoria}'
                    ))
                    
                    items_imported += 1
                
                if orders_imported % 10 == 0:
                    print(f"Progreso: {orders_imported} órdenes importadas...")
                    
            except Exception as e:
                error_msg = f"Error procesando orden {order_id_excel}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
                continue
        
        # Confirmar cambios
        conn.commit()
        
        # Estadísticas finales
        final_orders = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        final_items = cursor.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
        
        print("\n=== RESUMEN DE IMPORTACIÓN ===")
        print(f"Órdenes importadas: {orders_imported}")
        print(f"Items importados: {items_imported}")
        print(f"Total órdenes en BD: {final_orders}")
        print(f"Total items en BD: {final_items}")
        
        if errors:
            print(f"\nErrores encontrados ({len(errors)}):")
            for error in errors[:5]:  # Mostrar solo primeros 5 errores
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... y {len(errors) - 5} errores más")
        
        # Análisis de productos no encontrados
        print("\n=== VERIFICACIÓN DE PRODUCTOS ===")
        cursor.execute('''
            SELECT DISTINCT product_name, COUNT(*) as cantidad
            FROM order_items 
            WHERE product_id IS NULL AND notes LIKE '%Categoría:%'
            GROUP BY product_name
            ORDER BY cantidad DESC
            LIMIT 10
        ''')
        productos_faltantes = cursor.fetchall()
        
        if productos_faltantes:
            print("Productos que no existen en el catálogo:")
            for producto, cantidad in productos_faltantes:
                print(f"  - {producto} ({cantidad} veces)")
            print("\nRecomendación: Crear estos productos en el sistema")
        
        conn.close()
        
        print(f"\n✅ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        return False

def create_products_from_import(db_path='data/sandwich.db'):
    """
    Crear productos automáticamente basados en los datos importados
    """
    print("\n=== CREANDO PRODUCTOS DESDE IMPORTACIÓN ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener productos únicos de las órdenes importadas
    cursor.execute('''
        SELECT DISTINCT 
            oi.product_name,
            REPLACE(REPLACE(oi.notes, 'Categoría: ', ''), 'Sin categoría', 'General') as categoria,
            AVG(oi.unit_price) as precio_promedio,
            COUNT(*) as veces_vendido
        FROM order_items oi
        WHERE oi.product_id IS NULL 
        AND oi.notes LIKE '%Categoría:%'
        GROUP BY oi.product_name, categoria
        ORDER BY veces_vendido DESC
    ''')
    
    productos_importados = cursor.fetchall()
    
    if not productos_importados:
        print("No hay productos para crear")
        return
    
    # Crear/obtener categorías
    categorias_map = {}
    for _, categoria, _, _ in productos_importados:
        if categoria not in categorias_map:
            # Buscar si la categoría existe
            cat_exists = cursor.execute(
                "SELECT id FROM categories WHERE UPPER(name) = UPPER(?)", 
                (categoria,)
            ).fetchone()
            
            if cat_exists:
                categorias_map[categoria] = cat_exists[0]
            else:
                # Crear nueva categoría
                cursor.execute('''
                    INSERT INTO categories (name, description, color, active)
                    VALUES (?, ?, ?, ?)
                ''', (categoria, f'Categoría importada: {categoria}', '#3498db', 1))
                categorias_map[categoria] = cursor.lastrowid
                print(f"Categoría creada: {categoria}")
    
    # Crear productos
    productos_creados = 0
    for producto, categoria, precio, veces in productos_importados:
        # Verificar si el producto ya existe
        exists = cursor.execute(
            "SELECT id FROM products WHERE UPPER(name) = UPPER(?)", 
            (producto,)
        ).fetchone()
        
        if exists:
            continue
        
        category_id = categorias_map.get(categoria)
        
        cursor.execute('''
            INSERT INTO products (name, description, price, category_id, available)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            producto,
            f'Producto importado - Vendido {veces} veces',
            round(precio, 0),  # Redondear precio
            category_id,
            1
        ))
        
        productos_creados += 1
        print(f"Producto creado: {producto} - ${precio:.0f} ({categoria})")
    
    # Actualizar product_id en order_items
    cursor.execute('''
        UPDATE order_items 
        SET product_id = (
            SELECT p.id FROM products p 
            WHERE UPPER(p.name) = UPPER(order_items.product_name)
        )
        WHERE product_id IS NULL
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {productos_creados} productos creados")
    print("✅ Referencias actualizadas en órdenes")

if __name__ == "__main__":
    # Configuración
    excel_file = "Reporte_Ventas_Epicuro_20250822_a_20250921.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Archivo {excel_file} no encontrado")
        print("Coloca el archivo Excel en la misma carpeta que este script")
        exit(1)
    
    # Ejecutar importación
    success = import_sales_from_excel(excel_file)
    
    if success:
        # Crear productos automáticamente
        create_products_from_import()
        print("\n🎉 ¡IMPORTACIÓN COMPLETA!")
        print("Puedes revisar los datos en tu aplicación web")
    else:
        print("\n❌ La importación falló")