# ==========================================
# CONFIGURACIÓN DE PROTEÍNAS SIN COSTO
# ==========================================

import sqlite3
from flask import Flask

def configure_proteins_no_cost():
    """Configurar todas las proteínas para que NO tengan costo adicional"""
    try:
        # Conectar a la base de datos
        db_files = ['database.db', 'app.db', 'instance/database.db', 'sandwich.db']
        db_path = None
        
        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='variation_groups'")
                db_path = db_file
                conn.close()
                break
            except:
                continue
        
        if not db_path:
            print("❌ No se encontró base de datos con tablas de variaciones")
            return False
        
        print(f"📍 Usando base de datos: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Verificar que existe el grupo de proteínas
        cursor.execute("SELECT id FROM variation_groups WHERE name = 'protein'")
        protein_group = cursor.fetchone()
        
        if not protein_group:
            print("⚠️  Grupo de proteínas no existe. Creándolo...")
            cursor.execute("""
                INSERT INTO variation_groups (name, display_name, description) 
                VALUES ('protein', 'Proteína', 'Tipo de proteína (sin costo adicional)')
            """)
            protein_group_id = cursor.lastrowid
        else:
            protein_group_id = protein_group[0]
            print(f"✅ Grupo de proteínas encontrado: ID {protein_group_id}")
        
        # 2. Actualizar todas las proteínas para que tengan price_modifier = 0
        cursor.execute("""
            UPDATE variation_options 
            SET price_modifier = 0 
            WHERE variation_group_id = ?
        """, (protein_group_id,))
        
        affected_rows = cursor.rowcount
        print(f"✅ Actualizadas {affected_rows} opciones de proteína a costo $0")
        
        # 3. Verificar que las proteínas básicas existen
        basic_proteins = [
            ('Churrasco', 'Churrasco a la plancha'),
            ('Lomito', 'Lomito de cerdo'),
            ('Pollo', 'Pechuga de pollo')
        ]
        
        for protein_name, description in basic_proteins:
            cursor.execute("""
                SELECT id FROM variation_options 
                WHERE variation_group_id = ? AND name = ?
            """, (protein_group_id, protein_name))
            
            if not cursor.fetchone():
                print(f"➕ Agregando proteína: {protein_name}")
                cursor.execute("""
                    INSERT INTO variation_options 
                    (variation_group_id, name, display_name, price_modifier, active) 
                    VALUES (?, ?, ?, 0, 1)
                """, (protein_group_id, protein_name, protein_name))
            else:
                print(f"✅ Proteína ya existe: {protein_name}")
        
        # 4. Mostrar resumen final
        cursor.execute("""
            SELECT vo.name, vo.price_modifier, vo.active
            FROM variation_options vo
            WHERE vo.variation_group_id = ?
            ORDER BY vo.name
        """, (protein_group_id,))
        
        proteins = cursor.fetchall()
        
        print("\n🍖 RESUMEN DE PROTEÍNAS CONFIGURADAS:")
        print("=" * 45)
        for protein in proteins:
            status = "✅ ACTIVA" if protein[2] else "❌ INACTIVA"
            cost = f"${protein[1]}" if protein[1] != 0 else "GRATIS"
            print(f"  {protein[0]:12} | {cost:8} | {status}")
        
        # 5. Verificar configuración de productos
        cursor.execute("""
            SELECT COUNT(*) FROM product_variations pv
            JOIN variation_groups vg ON pv.variation_group_id = vg.id
            WHERE vg.name = 'protein'
        """)
        
        products_with_protein = cursor.fetchone()[0]
        print(f"\n📊 Productos con opción de proteína: {products_with_protein}")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 ¡CONFIGURACIÓN COMPLETADA!")
        print("✅ Todas las proteínas están configuradas SIN COSTO ADICIONAL")
        print("✅ Los clientes pueden elegir proteína sin pagar extra")
        print("✅ La selección aparecerá claramente en la comanda de cocina")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando proteínas: {e}")
        return False

def verify_protein_setup():
    """Verificar que la configuración de proteínas está correcta"""
    try:
        db_files = ['database.db', 'app.db', 'instance/database.db', 'sandwich.db']
        db_path = None
        
        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='variation_groups'")
                db_path = db_file
                conn.close()
                break
            except:
                continue
        
        if not db_path:
            print("❌ No se encontró base de datos")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar proteínas
        cursor.execute("""
            SELECT vo.name, vo.price_modifier
            FROM variation_options vo
            JOIN variation_groups vg ON vo.variation_group_id = vg.id
            WHERE vg.name = 'protein' AND vo.active = 1
        """)
        
        proteins = cursor.fetchall()
        
        print("🔍 VERIFICACIÓN DE CONFIGURACIÓN:")
        print("=" * 40)
        
        all_free = True
        for protein in proteins:
            if protein[1] != 0:
                print(f"❌ {protein[0]}: ${protein[1]} (DEBERÍA SER $0)")
                all_free = False
            else:
                print(f"✅ {protein[0]}: GRATIS")
        
        if all_free and proteins:
            print(f"\n🎉 ¡PERFECTO! Todas las {len(proteins)} proteínas son GRATIS")
        elif not proteins:
            print("\n⚠️  No hay proteínas configuradas")
        else:
            print(f"\n❌ Hay proteínas con costo. Ejecuta configure_proteins_no_cost()")
        
        conn.close()
        return all_free
        
    except Exception as e:
        print(f"❌ Error verificando: {e}")
        return False

# ==========================================
# SQL PARA ACTUALIZAR FORMULARIO DE ÓRDENES
# ==========================================

def update_order_form_for_free_proteins():
    """Actualizar el template del formulario para mostrar que las proteínas son gratis"""
    
    # JavaScript para el formulario de órdenes
    js_code = """
// Función para actualizar precio cuando se seleccionan variaciones
function updateProductPrice(productId) {
    const selectedVariations = [];
    const checkboxes = document.querySelectorAll(`input[name="variations_${productId}[]"]:checked`);
    
    checkboxes.forEach(checkbox => {
        selectedVariations.push(checkbox.value);
    });
    
    // Las proteínas NO suman costo, solo otros extras
    fetch(`/api/product/${productId}/price`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            variations: selectedVariations
        })
    })
    .then(response => response.json())
    .then(data => {
        const priceElement = document.getElementById(`price_${productId}`);
        if (priceElement) {
            priceElement.textContent = `$${data.final_price}`;
        }
        
        // Mostrar breakdown de precio si hay extras con costo
        const extraCost = data.total_modifier;
        const proteinNote = document.getElementById(`protein_note_${productId}`);
        if (proteinNote) {
            if (extraCost > 0) {
                proteinNote.innerHTML = '<small class="text-success">✅ Proteína: GRATIS | Extras: +$' + extraCost + '</small>';
            } else {
                proteinNote.innerHTML = '<small class="text-success">✅ Proteína: GRATIS</small>';
            }
        }
    });
}

// Agregar evento a todos los checkboxes de variaciones
document.addEventListener('DOMContentLoaded', function() {
    const variationCheckboxes = document.querySelectorAll('input[name^="variations_"]');
    variationCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const productId = this.name.match(/variations_(\d+)/)[1];
            updateProductPrice(productId);
        });
    });
});
"""
    
    print("📄 CÓDIGO JAVASCRIPT PARA EL FORMULARIO:")
    print("=" * 50)
    print(js_code)
    print("\n💡 Agrega este JavaScript a tu template create_order.html")
    
    # CSS para mostrar claramente las proteínas gratis
    css_code = """
.protein-variation {
    background-color: #e8f5e8 !important;
    border: 2px solid #4caf50 !important;
    border-radius: 5px;
    padding: 8px;
}

.protein-variation label {
    font-weight: bold !important;
    color: #2e7d32 !important;
}

.protein-variation::after {
    content: " 🆓 GRATIS";
    color: #4caf50;
    font-size: 0.8em;
    font-weight: bold;
}

.variation-group.protein {
    border-left: 4px solid #4caf50;
    padding-left: 10px;
    margin-bottom: 15px;
}

.free-protein-badge {
    background: #4caf50;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: bold;
    margin-left: 5px;
}
"""
    
    print("\n🎨 CÓDIGO CSS PARA DESTACAR PROTEÍNAS GRATIS:")
    print("=" * 50)
    print(css_code)
    
    return js_code, css_code

# ==========================================
# SCRIPT PRINCIPAL
# ==========================================

if __name__ == '__main__':
    print("🍖 CONFIGURADOR DE PROTEÍNAS SIN COSTO")
    print("=" * 50)
    
    # 1. Configurar proteínas sin costo
    print("\n1️⃣ Configurando proteínas...")
    configure_proteins_no_cost()
    
    # 2. Verificar configuración
    print("\n2️⃣ Verificando configuración...")
    verify_protein_setup()
    
    # 3. Generar código para formularios
    print("\n3️⃣ Generando código para formularios...")
    update_order_form_for_free_proteins()
    
    print("\n" + "=" * 50)
    print("🎯 PRÓXIMOS PASOS:")
    print("=" * 50)
    print("1. ✅ Ejecuta este script: python protein_setup.py")
    print("2. 📝 Actualiza tu formulario create_order.html con el CSS/JS generado")
    print("3. 🖨️ Usa el template kitchen_print.html para las comandas")
    print("4. 🧪 Prueba creando una orden con proteína")
    print("5. ✅ Verifica que la proteína aparece en la comanda SIN COSTO")
    
    print("\n🎉 ¡LISTO! Las proteínas ya están configuradas sin costo adicional")
