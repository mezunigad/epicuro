-- ==========================================
-- ARREGLAR PROTEÍNAS DUPLICADAS Y PRECIOS
-- ==========================================

-- 1. ELIMINAR TODAS LAS PROTEÍNAS EXISTENTES PARA EMPEZAR LIMPIO
-- ===============================================================

DELETE FROM order_item_variations 
WHERE variation_option_id IN (
    SELECT vo.id FROM variation_options vo
    JOIN variation_groups vg ON vo.variation_group_id = vg.id
    WHERE vg.name IN ('protein', 'protein_type', 'proteina')
);

DELETE FROM variation_options 
WHERE variation_group_id IN (
    SELECT id FROM variation_groups 
    WHERE name IN ('protein', 'protein_type', 'proteina')
);

DELETE FROM variation_groups 
WHERE name IN ('protein', 'protein_type', 'proteina');

-- 2. CREAR GRUPO DE PROTEÍNAS LIMPIO
-- ==================================

INSERT INTO variation_groups 
(id, name, display_name, description, required, multiple_selection, max_selections, active)
VALUES (1, 'protein', 'Tipo de Proteína', 'Selecciona tu proteína (sin costo adicional)', 1, 0, 1, 1);

-- 3. INSERTAR SOLO 3 PROTEÍNAS ÚNICAS CON PRECIO 0
-- ================================================

INSERT INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, active, sort_order)
VALUES 
(1, 'Churrasco', 'Churrasco', 'Churrasco a la plancha - SIN COSTO', 0, 1, 1),
(1, 'Lomito', 'Lomito', 'Lomito de cerdo - SIN COSTO', 0, 1, 2),
(1, 'Pollo', 'Pollo', 'Pechuga de pollo - SIN COSTO', 0, 1, 3);

-- 4. VERIFICAR QUE ESTÁ CORRECTO
-- ==============================

SELECT 
    '=== PROTEÍNAS CONFIGURADAS ===' as titulo;

SELECT 
    vo.id,
    vo.name as proteina,
    vo.price_modifier as precio,
    CASE 
        WHEN vo.price_modifier = 0 THEN '✅ GRATIS'
        ELSE '❌ CON COSTO: +$' || vo.price_modifier
    END as estado_precio,
    CASE 
        WHEN vo.active = 1 THEN '✅ ACTIVA'
        ELSE '❌ INACTIVA'
    END as estado_activo
FROM variation_options vo
JOIN variation_groups vg ON vo.variation_group_id = vg.id
WHERE vg.name = 'protein'
ORDER BY vo.sort_order;

-- 5. LIMPIAR ASIGNACIONES DUPLICADAS A PRODUCTOS
-- ==============================================

-- Eliminar asignaciones duplicadas del grupo de proteínas
DELETE FROM product_variations 
WHERE rowid NOT IN (
    SELECT MIN(rowid) 
    FROM product_variations 
    WHERE variation_group_id = 1
    GROUP BY product_id, variation_group_id
);

-- 6. VERIFICAR PRODUCTOS ASIGNADOS
-- ================================

SELECT 
    '=== PRODUCTOS CON PROTEÍNAS ===' as titulo;

SELECT 
    p.name as producto,
    COUNT(pv.id) as asignaciones,
    CASE 
        WHEN COUNT(pv.id) = 1 THEN '✅ CORRECTO'
        WHEN COUNT(pv.id) > 1 THEN '❌ DUPLICADO'
        ELSE '❌ SIN ASIGNAR'
    END as estado
FROM products p
LEFT JOIN product_variations pv ON p.id = pv.product_id AND pv.variation_group_id = 1
WHERE p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%' OR p.name LIKE '%CHACARERO%'
GROUP BY p.id, p.name
ORDER BY p.name;

-- 7. COMANDO FINAL DE VERIFICACIÓN
-- ================================

SELECT 
    '=== RESUMEN FINAL ===' as titulo;

SELECT 
    (SELECT COUNT(*) FROM variation_options WHERE variation_group_id = 1) as total_proteinas,
    (SELECT COUNT(*) FROM variation_options WHERE variation_group_id = 1 AND price_modifier = 0) as proteinas_gratis,
    (SELECT COUNT(*) FROM variation_options WHERE variation_group_id = 1 AND price_modifier > 0) as proteinas_con_costo;
