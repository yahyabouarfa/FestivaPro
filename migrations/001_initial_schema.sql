CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone_number VARCHAR(40) NULL,
  role VARCHAR(20) NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE refresh_tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token_hash VARCHAR(64) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  revoked_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_refresh_tokens_user_id (user_id),
  CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  location VARCHAR(80) NOT NULL,
  event_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_by INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (status IN ('upcoming', 'active', 'closed')),
  INDEX ix_events_status (status),
  CONSTRAINT fk_events_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE product_categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(140) NOT NULL,
  category_id INT NOT NULL,
  unit VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (unit IN ('bottle', 'can', 'unit')),
  UNIQUE KEY uq_products_name_category (name, category_id),
  CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES product_categories(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bars (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  name VARCHAR(120) NOT NULL,
  responsible_user_id INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bars_event_name (event_id, name),
  CONSTRAINT fk_bars_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_bars_responsible FOREIGN KEY (responsible_user_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bar_assignments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bar_id INT NOT NULL,
  user_id INT NOT NULL,
  assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bar_assignment_user (bar_id, user_id),
  INDEX ix_bar_assignments_user_bar (user_id, bar_id),
  CONSTRAINT fk_bar_assignments_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE,
  CONSTRAINT fk_bar_assignments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE event_stock (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity_total DECIMAL(10,2) NOT NULL,
  bought_price_per_unit DECIMAL(10,2) NOT NULL,
  selling_price_per_unit DECIMAL(10,2) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_event_stock_product (event_id, product_id),
  CONSTRAINT fk_event_stock_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_event_stock_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bar_stock (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bar_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity_allocated DECIMAL(10,2) NOT NULL,
  quantity_sold DECIMAL(10,2) GENERATED ALWAYS AS (quantity_allocated - quantity_remaining) STORED,
  quantity_remaining DECIMAL(10,2) NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bar_stock_product (bar_id, product_id),
  CONSTRAINT fk_bar_stock_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE,
  CONSTRAINT fk_bar_stock_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE VIEW bar_stock_financials AS
SELECT
  bs.id AS bar_stock_id,
  b.event_id,
  bs.bar_id,
  bs.product_id,
  bs.quantity_allocated,
  bs.quantity_remaining,
  bs.quantity_sold,
  es.bought_price_per_unit,
  es.selling_price_per_unit,
  (bs.quantity_sold * es.selling_price_per_unit) AS revenue,
  (bs.quantity_sold * es.bought_price_per_unit) AS cost,
  ((bs.quantity_sold * es.selling_price_per_unit) - (bs.quantity_sold * es.bought_price_per_unit)) AS profit
FROM bar_stock bs
JOIN bars b ON b.id = bs.bar_id
JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bs.product_id;

INSERT INTO users (id, full_name, email, phone_number, role, hashed_password, is_active) VALUES
(1, 'Festival Admin', 'admin@festivapro.local', '+212600000001', 'admin', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(2, 'Yassine Amrani', 'employee1@festivapro.local', '+212600000010', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(3, 'Salma Idrissi', 'employee2@festivapro.local', '+212600000011', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(4, 'Omar Benali', 'employee3@festivapro.local', '+212600000012', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(5, 'Nadia Berrada', 'employee4@festivapro.local', '+212600000013', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(6, 'Mehdi El Fassi', 'employee5@festivapro.local', '+212600000014', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(7, 'Imane Tazi', 'employee6@festivapro.local', '+212600000015', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(8, 'Hassan Alaoui', 'employee7@festivapro.local', '+212600000016', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(9, 'Sara Moutawakil', 'employee8@festivapro.local', '+212600000017', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(10, 'Rachid Mansouri', 'employee9@festivapro.local', '+212600000018', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE),
(11, 'Lina Sabri', 'employee10@festivapro.local', '+212600000019', 'employee', '$2b$12$C6UzMDM.H6dfI/f/IKcEeO6c7jo1dfmjdgKiSmTsgZ7CeJc3prN9a', TRUE);

INSERT INTO events (id, name, location, event_date, start_time, end_time, status, created_by) VALUES
(1, 'Casa Nights Festival', 'Casablanca', '2026-06-05', '18:00:00', '02:00:00', 'upcoming', 1),
(2, 'Marrakech Desert Beats', 'Marrakech', '2026-06-12', '19:00:00', '03:00:00', 'upcoming', 1),
(3, 'Agadir Beach Sessions', 'Agadir', '2026-06-19', '17:30:00', '01:30:00', 'upcoming', 1),
(4, 'Rabat Stage Live', 'Rabat', '2026-06-26', '18:30:00', '02:30:00', 'upcoming', 1),
(5, 'Tanger Harbor Sound', 'Tanger', '2026-07-03', '19:30:00', '03:30:00', 'upcoming', 1);

INSERT INTO product_categories (id, name) VALUES (1, 'Beer'), (2, 'Hard Alcohol'), (3, 'Soda'), (4, 'Consumables');

INSERT INTO products (id, name, category_id, unit) VALUES
(1, 'Gold Special', 1, 'can'), (2, 'Casablanca', 1, 'bottle'),
(3, 'Gordon''s', 2, 'bottle'), (4, 'Tanqueray', 2, 'bottle'), (5, 'Smirnoff', 2, 'bottle'), (6, 'Belvedere', 2, 'bottle'),
(7, 'Red Label', 2, 'bottle'), (8, 'Black Label', 2, 'bottle'), (9, 'Jose Cuervo Tequila', 2, 'bottle'),
(10, 'Coca-Cola', 3, 'can'), (11, 'Sprite', 3, 'can'), (12, 'Water', 3, 'bottle'), (13, 'Tonic', 3, 'can'),
(14, 'Goblets', 4, 'unit'), (15, 'Ice', 4, 'unit'), (16, 'Napkins', 4, 'unit'), (17, 'Straws', 4, 'unit');

INSERT INTO bars (id, event_id, name, responsible_user_id) VALUES
(1, 1, 'VIP Bar', 2), (2, 1, 'Garden Bar', 3), (3, 1, 'Terrace Bar', 4),
(4, 2, 'Garden Bar', 5), (5, 2, 'Terrace Bar', 6), (6, 2, 'Beach Bar', 7), (7, 2, 'Lounge Bar', 8),
(8, 3, 'Terrace Bar', 9), (9, 3, 'Beach Bar', 10), (10, 3, 'Lounge Bar', 11),
(11, 4, 'Beach Bar', 2), (12, 4, 'Lounge Bar', 3),
(13, 5, 'Lounge Bar', 4), (14, 5, 'North Bar', 5), (15, 5, 'Harbor Bar', 6);

INSERT INTO bar_assignments (bar_id, user_id)
SELECT b.id, u.id
FROM bars b
JOIN users u ON u.role = 'employee'
WHERE u.id IN (b.responsible_user_id, 2 + MOD(b.id, 10), 2 + MOD(b.id + 3, 10));

DELIMITER //
CREATE PROCEDURE seed_stock()
BEGIN
  DECLARE e INT DEFAULT 1;
  DECLARE p INT DEFAULT 1;
  DECLARE b INT DEFAULT 1;
  WHILE e <= 5 DO
    SET p = 1;
    WHILE p <= 17 DO
      INSERT INTO event_stock (event_id, product_id, quantity_total, bought_price_per_unit, selling_price_per_unit)
      VALUES (
        e, p, 120 + e * 20 + p * 3,
        CASE p WHEN 1 THEN 12 WHEN 2 THEN 14 WHEN 3 THEN 150 WHEN 4 THEN 230 WHEN 5 THEN 120 WHEN 6 THEN 360 WHEN 7 THEN 180 WHEN 8 THEN 310 WHEN 9 THEN 190 WHEN 10 THEN 5 WHEN 11 THEN 5 WHEN 12 THEN 3 WHEN 13 THEN 6 WHEN 14 THEN 0.60 WHEN 15 THEN 8 WHEN 16 THEN 0.20 ELSE 0.10 END * (1 + ((e - 1) * 0.05)),
        CASE p WHEN 1 THEN 30 WHEN 2 THEN 35 WHEN 3 THEN 350 WHEN 4 THEN 520 WHEN 5 THEN 320 WHEN 6 THEN 760 WHEN 7 THEN 420 WHEN 8 THEN 680 WHEN 9 THEN 450 WHEN 10 THEN 15 WHEN 11 THEN 15 WHEN 12 THEN 10 WHEN 13 THEN 18 WHEN 14 THEN 1 WHEN 15 THEN 12 WHEN 16 THEN 0.50 ELSE 0.30 END * (1 + ((e - 1) * 0.05))
      );
      SET p = p + 1;
    END WHILE;
    SET e = e + 1;
  END WHILE;

  WHILE b <= 15 DO
    SET p = 1;
    WHILE p <= 17 DO
      INSERT INTO bar_stock (bar_id, product_id, quantity_allocated, quantity_remaining)
      VALUES (b, p, 18 + MOD(b, 4) * 4 + MOD(p, 5) * 3, GREATEST(0, 18 + MOD(b, 4) * 4 + MOD(p, 5) * 3 - (4 + MOD(b + p, 9))));
      SET p = p + 1;
    END WHILE;
    SET b = b + 1;
  END WHILE;
END//
DELIMITER ;

CALL seed_stock();
DROP PROCEDURE seed_stock;
