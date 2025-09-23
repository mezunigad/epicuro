-- Script para crear productos básicos del Excel
-- Ejecutar en tu base de datos SQLite

-- Crear categorías si no existen
INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('CAFETERÍA', 'Bebidas calientes y café', '#8B4513', 1);
INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('SANDWICH', 'Sándwiches y comida', '#FF6B35', 1);
INSERT OR IGNORE INTO categories (name, description, color, active) VALUES ('BEBIDA', 'Bebidas frías', '#4A90E2', 1);

-- Crear productos básicos
INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('MOCACCINO GRANDE', 'Café mocaccino tamaño grande', 2800, (SELECT id FROM categories WHERE name = 'CAFETERÍA'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('TÉ NEGRO', 'Té negro tradicional', 1200, (SELECT id FROM categories WHERE name = 'CAFETERÍA'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('LATTE', 'Café latte', 2400, (SELECT id FROM categories WHERE name = 'CAFETERÍA'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('PAPA MEDIANA', 'Papa rellena tamaño mediano', 2500, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('SANDWICH CHACARERO', 'Sandwich chacarero tradicional', 8790, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('PAPA CHICA', 'Papa rellena tamaño chico', 1000, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('SANDWICH EPICURO', 'Sandwich especial de la casa', 8990, (SELECT id FROM categories WHERE name = 'SANDWICH'), 1);

INSERT OR IGNORE INTO products (name, description, price, category_id, available) 
VALUES ('COCA COLA', 'Coca Cola 350ml', 1400, (SELECT id FROM categories WHERE name = 'BEBIDA'), 1);

-- Verificar productos creados
SELECT p.name, p.price, c.name as categoria 
FROM products p 
JOIN categories c ON p.category_id = c.id 
WHERE p.available = 1 
ORDER BY c.name, p.name;
