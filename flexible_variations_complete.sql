-- ==========================================
-- SISTEMA FLEXIBLE DE VARIACIONES
-- ==========================================

-- 1. CREAR TABLAS DEL SISTEMA
-- ===========================

-- Tabla principal: Grupos de Variaciones
CREATE TABLE IF NOT EXISTS variation_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT '⚙️',
    required_by_default BOOLEAN DEFAULT 0,
    multiple_selection BOOLEAN DEFAULT 0,
    min_selections INTEGER DEFAULT 0,
    max_selections INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de opciones para cada grupo
CREATE TABLE IF NOT EXISTS variation_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variation_group_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_modifier DECIMAL(10,2) DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    color_code VARCHAR(7),
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id) ON DELETE CASCADE
);

-- Tabla de asignación: qué productos tienen qué variaciones
CREATE TABLE IF NOT EXISTS product_variations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    variation_group_id INTEGER NOT NULL,
    required BOOLEAN DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (variation_group_id) REFERENCES variation_groups (id) ON DELETE CASCADE,
    UNIQUE(product_id, variation_group_id)
);

-- Tabla de variaciones seleccionadas en órdenes
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
);

-- 2. INSERTAR GRUPOS DE VARIACIONES EJEMPLO
-- =========================================

INSERT OR REPLACE INTO variation_groups 
(id, name, display_name, description, icon, required_by_default, multiple_selection, max_selections, sort_order)
VALUES 
-- Proteínas (radio buttons - solo una)
(1, 'protein', 'Tipo de Proteína', 'Elige tu proteína favorita', '🥩', 1, 0, 1, 1),

-- Tipo de Pan (radio buttons - solo uno)
(2, 'bread_type', 'Tipo de Pan', 'Elige el pan para tu sandwich', '🍞', 1, 0, 1, 2),

-- Sabores de Bebida (radio buttons - solo uno)
(3, 'drink_flavor', 'Sabor de Bebida', 'Elige tu sabor favorito', '🥤', 1, 0, 1, 3),

-- Tamaños (radio buttons - solo uno)
(4, 'size', 'Tamaño', 'Elige el tamaño de tu producto', '📏', 0, 0, 1, 4),

-- Extras (checkboxes - múltiples)
(5, 'extras', 'Extras', 'Ingredientes adicionales', '➕', 0, 1, 5, 5),

-- Salsas (checkboxes - múltiples)
(6, 'sauces', 'Salsas', 'Salsas adicionales', '🌶️', 0, 1, 3, 6),

-- Temperatura (radio buttons - solo una)
(7, 'temperature', 'Temperatura', 'Caliente o frío', '🌡️', 0, 0, 1, 7);

-- 3. INSERTAR OPCIONES PARA CADA GRUPO
-- ====================================

-- PROTEÍNAS (sin costo)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(1, 'churrasco', 'Churrasco', 'Churrasco a la plancha', 0, 1, '#8B4513'),
(1, 'lomito', 'Lomito', 'Lomito de cerdo', 0, 2, '#D2691E'),
(1, 'pollo', 'Pollo', 'Pechuga de pollo', 0, 3, '#F5DEB3'),
(1, 'pavo', 'Pavo', 'Pavo natural', 0, 4, '#DDD'),
(1, 'vegetariano', 'Vegetariano', 'Opción vegetariana', 0, 5, '#228B22');

-- TIPOS DE PAN (sin costo)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(2, 'marraqueta', 'Marraqueta', 'Pan marraqueta tradicional', 0, 1, '#DEB887'),
(2, 'hallulla', 'Hallulla', 'Pan hallulla suave', 0, 2, '#F5E6D3'),
(2, 'pita', 'Pan Pita', 'Pan pita integral', 200, 3, '#D2B48C'),
(2, 'ciabatta', 'Ciabatta', 'Pan ciabatta artesanal', 300, 4, '#CD853F');

-- SABORES DE BEBIDA (sin costo)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(3, 'cola', 'Cola', 'Sabor cola clásico', 0, 1, '#8B0000'),
(3, 'orange', 'Naranja', 'Sabor naranja natural', 0, 2, '#FF8C00'),
(3, 'lemon', 'Limón', 'Sabor limón refrescante', 0, 3, '#FFFF00'),
(3, 'grape', 'Uva', 'Sabor uva dulce', 0, 4, '#800080'),
(3, 'apple', 'Manzana', 'Sabor manzana verde', 0, 5, '#32CD32');

-- TAMAÑOS (con modificadores de precio)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(4, 'small', 'Pequeño', 'Tamaño individual', -500, 1, '#87CEEB'),
(4, 'medium', 'Mediano', 'Tamaño estándar', 0, 2, '#4169E1'),
(4, 'large', 'Grande', 'Tamaño familiar', 800, 3, '#000080'),
(4, 'xl', 'Extra Grande', 'Tamaño compartir', 1500, 4, '#191970');

-- EXTRAS (con costo adicional)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(5, 'cheese', 'Queso', 'Queso cheddar fundido', 400, 1, '#FFD700'),
(5, 'avocado', 'Palta', 'Palta fresca chilena', 500, 2, '#228B22'),
(5, 'bacon', 'Tocino', 'Tocino crocante', 600, 3, '#A0522D'),
(5, 'tomato', 'Tomate', 'Tomate fresco', 200, 4, '#FF6347'),
(5, 'lettuce', 'Lechuga', 'Lechuga crispy', 150, 5, '#90EE90'),
(5, 'onion', 'Cebolla', 'Cebolla caramelizada', 200, 6, '#DDA0DD');

-- SALSAS (sin costo adicional)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(6, 'mayo', 'Mayonesa', 'Mayonesa casera', 0, 1, '#FFF8DC'),
(6, 'ketchup', 'Ketchup', 'Ketchup natural', 0, 2, '#DC143C'),
(6, 'mustard', 'Mostaza', 'Mostaza dijon', 0, 3, '#FFDB58'),
(6, 'bbq', 'BBQ', 'Salsa barbacoa', 0, 4, '#8B4513'),
(6, 'ranch', 'Ranch', 'Salsa ranch', 0, 5, '#F5F5DC'),
(6, 'hot_sauce', 'Picante', 'Salsa picante', 0, 6, '#FF4500');

-- TEMPERATURA (sin costo)
INSERT OR REPLACE INTO variation_options 
(variation_group_id, name, display_name, description, price_modifier, sort_order, color_code)
VALUES 
(7, 'hot', 'Caliente', 'Servido caliente', 0, 1, '#FF6347'),
(7, 'cold', 'Frío', 'Servido frío', 0, 2, '#87CEEB');

-- 4. ASIGNAR VARIACIONES A PRODUCTOS EJEMPLO
-- ==========================================

-- SANDWICHES: Proteína + Pan + Extras + Salsas
INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    1, -- proteína
    1, -- requerido
    1  -- orden
FROM products p
WHERE p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%' OR p.name LIKE '%BARROS%' OR p.name LIKE '%ITALIANO%' OR p.name LIKE '%CHACARERO%';

INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    2, -- tipo de pan
    1, -- requerido
    2  -- orden
FROM products p
WHERE p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%' OR p.name LIKE '%BARROS%' OR p.name LIKE '%ITALIANO%' OR p.name LIKE '%CHACARERO%';

INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    5, -- extras
    0, -- opcional
    3  -- orden
FROM products p
WHERE p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%' OR p.name LIKE '%BARROS%' OR p.name LIKE '%ITALIANO%' OR p.name LIKE '%CHACARERO%';

INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    6, -- salsas
    0, -- opcional
    4  -- orden
FROM products p
WHERE p.name LIKE '%SANDWICH%' OR p.name LIKE '%COMPLETO%' OR p.name LIKE '%BARROS%' OR p.name LIKE '%ITALIANO%' OR p.name LIKE '%CHACARERO%';

-- BEBIDAS: Sabor + Tamaño + Temperatura
INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    3, -- sabor
    1, -- requerido
    1  -- orden
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.name LIKE '%BEBIDA%' OR p.name LIKE '%JUGO%' OR p.name LIKE '%GASEOSA%' OR c.name LIKE '%BEBIDA%' OR p.name LIKE '%COCA%';

INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    4, -- tamaño
    1, -- requerido
    2  -- orden
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.name LIKE '%BEBIDA%' OR p.name LIKE '%JUGO%' OR p.name LIKE '%GASEOSA%' OR c.name LIKE '%BEBIDA%' OR p.name LIKE '%COCA%';

INSERT OR IGNORE INTO product_variations (product_id, variation_group_id, required, sort_order)
SELECT 
    p.id,
    7, -- temperatura
    0, -- opcional
    3  -- orden
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
WHERE p.name LIKE '%BEBIDA%' OR p.name LIKE '%JUGO%' OR p.name LIKE '%GASEOSA%' OR c.name LIKE '%BEBIDA%' OR p.name LIKE '%COCA%';

-- 5. VERIFICAR CONFIGURACIÓN
-- ==========================

SELECT 
    '=== GRUPOS DE VARIACIONES CONFIGURADOS ===' as titulo;

SELECT 
    vg.id,
    vg.display_name as grupo,
    vg.icon,
    CASE 
        WHEN vg.multiple_selection = 1 THEN 'Múltiple (☑️)'
        ELSE 'Única (⭕)'
    END as tipo_seleccion,
    CASE 
        WHEN vg.required_by_default = 1 THEN 'Requerido por defecto'
        ELSE 'Opcional por defecto'
    END as requerimiento,
    COUNT(vo.id) as opciones_disponibles
FROM variation_groups vg
LEFT JOIN variation_options vo ON vg.id = vo.variation_group_id AND vo.active = 1
WHERE vg.active = 1
GROUP BY vg.id
ORDER BY vg.sort_order;

SELECT 
    '=== PRODUCTOS CON VARIACIONES ===' as titulo;

SELECT 
    p.name as producto,
    COUNT(pv.id) as total_variaciones,
    GROUP_CONCAT(vg.display_name, ', ') as variaciones_asignadas
FROM products p
LEFT JOIN product_variations pv ON p.id = pv.product_id AND pv.active = 1
LEFT JOIN variation_groups vg ON pv.variation_group_id = vg.id AND vg.active = 1
GROUP BY p.id, p.name
HAVING COUNT(pv.id) > 0
ORDER BY COUNT(pv.id) DESC, p.name;
