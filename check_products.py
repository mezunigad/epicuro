import pandas as pd
import sqlite3
import os

def check_missing_products(excel_file, db_path='data/sandwich.db'):
    """
    Verificar qué productos del Excel no existen en la base de datos
    """
    print("=== VERIFICANDO PRODUCTOS FALTANTES ===")
    
    # Verificar archivos
    if not os.path.exists(excel_file):
        print(f"❌ Archivo {excel_file} no encontrado")
        return
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos {db_path} no encontrada")
        return
    
    try:
        # Leer Excel
        print(f"📖 Leyendo {excel_file}...")
        df_excel = pd.read_excel(excel_file, sheet_name='Detalle de Ventas')
        
        # Extraer productos únicos del Excel
        productos_excel = df_excel.groupby(['Producto', 'Categoría']).agg({
            'Precio': 'mean',  # Precio promedio
            'Cantidad': 'sum',  # Cantidad total vendida
            'ID': 'count'  # Veces vendido
        }).round(0).reset_index()
        
        productos_excel.columns = ['Producto', 'Categoria', 'Precio_Promedio', 'Cantidad_Total', 'Veces_Vendido']
        productos_excel = productos_excel.sort_values('Veces_Vendido', ascending=False)
        
        print(f"📊 Productos únicos en Excel: {len(productos_excel)}")
        
        # Conectar a BD y obtener productos existentes
        print(f"🔍 Consultando base de datos...")
        conn = sqlite3.connect(db_path)
        
        # Obtener productos existentes
        df_bd = pd.read_sql_query('''
            SELECT p.name as producto, c.name as categoria, p.price as precio
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.available = 1
        ''', conn)
        
        print(f"📊 Productos en base de datos: {len(df_bd)}")
        
        # Obtener categorías existentes
        df_categorias = pd.read_sql_query('''
            SELECT name as categoria FROM categories WHERE active = 1
        ''', conn)
        categorias_bd = set(df_categorias['categoria'].str.upper())
        
        conn.close()
        
        # Comparar productos
        productos_bd = set(df_bd['producto'].str.upper())
        productos_excel_set = set(productos_excel['Producto'].str.upper())
        
        # Productos que faltan
        productos_faltantes = productos_excel_set - productos_bd
        productos_existentes = productos_excel_set & productos_bd
        
        print(f"\n=== RESULTADOS ===")
        print(f"✅ Productos que YA EXISTEN: {len(productos_existentes)}")
        print(f"❌ Productos que FALTAN: {len(productos_faltantes)}")
        
        if productos_existentes:
            print(f"\n📋 PRODUCTOS QUE YA EXISTEN EN BD:")
            for producto in sorted(productos_existentes):
                # Buscar info del producto en Excel
                info = productos_excel[productos_excel['Producto'].str.upper() == producto].iloc[0]
                print(f"  ✅ {producto} - ${info['Precio_Promedio']:.0f} ({info['Categoria']})")
        
        if productos_faltantes:
            print(f"\n📋 PRODUCTOS QUE NECESITAS CREAR:")
            productos_faltantes_info = productos_excel[
                productos_excel['Producto'].str.upper().isin(productos_faltantes)
            ].sort_values('Veces_Vendido', ascending=False)
            
            for _, row in productos_faltantes_info.iterrows():
                print(f"  ❌ {row['Producto']} - ${row['Precio_Promedio']:.0f} ({row['Categoria']}) - Vendido {row['Veces_Vendido']} veces")
        
        # Verificar categorías
        categorias_excel = set(productos_excel['Categoria'].str.upper())
        categorias_faltantes = categorias_excel - categorias_bd
        
        print(f"\n=== VERIFICACIÓN DE CATEGORÍAS ===")
        print(f"✅ Categorías que YA EXISTEN: {len(categorias_excel & categorias_bd)}")
        print(f"❌ Categorías que FALTAN: {len(categorias_faltantes)}")
        
        if categorias_faltantes:
            print(f"\n📋 CATEGORÍAS QUE NECESITAS CREAR:")
            for categoria in sorted(categorias_faltantes):
                productos_cat = len(productos_excel[productos_excel['Categoria'].str.upper() == categoria])
                print(f"  ❌ {categoria} ({productos_cat} productos)")
        
        # Generar archivo CSV con productos faltantes
        if not productos_faltantes_info.empty:
            output_file = 'productos_faltantes.csv'
            productos_faltantes_info.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\n💾 Archivo generado: {output_file}")
            print("   Puedes usar este archivo para crear los productos manualmente")
        
        # Resumen final
        print(f"\n=== RESUMEN PARA IMPORTACIÓN ===")
        if len(productos_faltantes) == 0:
            print("🎉 ¡Perfecto! Todos los productos ya existen en tu BD")
            print("   Puedes proceder con la importación directamente")
        else:
            print(f"⚠️  Necesitas crear {len(productos_faltantes)} productos antes de importar")
            print("   Opciones:")
            print("   1. Crear productos manualmente en tu sistema web")
            print("   2. Ejecutar script de auto-creación de productos")
            print("   3. Editar el Excel para usar nombres de productos existentes")
        
        return {
            'productos_faltantes': len(productos_faltantes),
            'productos_existentes': len(productos_existentes),
            'categorias_faltantes': len(categorias_faltantes),
            'total_productos_excel': len(productos_excel)
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def create_missing_products_sql(excel_file, db_path='data/sandwich.db'):
    """
    Generar script SQL para crear productos faltantes
    """
    print("\n=== GENERANDO SCRIPT SQL ===")
    
    try:
        # Leer Excel
        df_excel = pd.read_excel(excel_file, sheet_name='Detalle de Ventas')
        
        # Agrupar productos
        productos_excel = df_excel.groupby(['Producto', 'Categoría']).agg({
            'Precio': 'mean',
            'ID': 'count'
        }).round(0).reset_index()
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        df_bd = pd.read_sql_query('SELECT name FROM products WHERE available = 1', conn)
        df_categorias = pd.read_sql_query('SELECT name FROM categories WHERE active = 1', conn)
        conn.close()
        
        productos_bd = set(df_bd['name'].str.upper())
        categorias_bd = set(df_categorias['name'].str.upper())
        
        # Productos faltantes
        productos_faltantes = productos_excel[
            ~productos_excel['Producto'].str.upper().isin(productos_bd)
        ]
        
        if productos_faltantes.empty:
            print("No hay productos faltantes para crear")
            return
        
        # Generar SQL
        sql_lines = ["-- Script para crear productos faltantes", ""]
        
        # Crear categorías faltantes
        categorias_faltantes = set(productos_faltantes['Categoría'].str.upper()) - categorias_bd
        
        if categorias_faltantes:
            sql_lines.append("-- Crear categorías faltantes")
            for categoria in sorted(categorias_faltantes):
                sql_lines.append(f"INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('{categoria}', 'Categoría importada', '#3498db', 1);")
            sql_lines.append("")
        
        # Crear productos
        sql_lines.append("-- Crear productos faltantes")
        for _, row in productos_faltantes.iterrows():
            producto = row['Producto'].replace("'", "''")  # Escapar comillas
            categoria = row['Categoría']
            precio = int(row['Precio'])
            
            sql_lines.append(f"""INSERT INTO products (name, description, price, category_id, available) 
VALUES ('{producto}', 'Producto importado', {precio}, (SELECT id FROM categories WHERE name = '{categoria}'), 1);""")
        
        # Guardar archivo SQL
        sql_content = "\n".join(sql_lines)
        with open('crear_productos_faltantes.sql', 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        print("💾 Archivo generado: crear_productos_faltantes.sql")
        print("   Puedes ejecutar este SQL en tu base de datos")
        
    except Exception as e:
        print(f"❌ Error generando SQL: {str(e)}")

if __name__ == "__main__":
    excel_file = "Reporte_Ventas_Epicuro_20250822_a_20250921.xlsx"
    
    # Verificar productos faltantes
    resultado = check_missing_products(excel_file)
    
    if resultado and resultado['productos_faltantes'] > 0:
        print(f"\n🔧 ¿Quieres generar un script SQL para crear los productos faltantes? (s/n)")
        respuesta = input().lower()
        if respuesta in ['s', 'si', 'y', 'yes']:
            create_missing_products_sql(excel_file)