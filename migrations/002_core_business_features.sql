ALTER TABLE events
  ADD COLUMN attendance_count INT NOT NULL DEFAULT 0;

CREATE TABLE event_salaries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  user_id INT NOT NULL,
  bar_id INT NOT NULL,
  salary_amount DECIMAL(10,2) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_event_salaries_event_user_created (event_id, user_id, created_at),
  INDEX ix_event_salaries_event_bar (event_id, bar_id),
  CONSTRAINT fk_event_salaries_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_event_salaries_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_event_salaries_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bartender_sales (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  bar_id INT NOT NULL,
  user_id INT NOT NULL,
  units_sold DECIMAL(10,2) NOT NULL DEFAULT 0,
  sales_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  contribution_pct DECIMAL(5,2) NOT NULL DEFAULT 0,
  recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bartender_sales_event_bar_user (event_id, bar_id, user_id),
  INDEX ix_bartender_sales_event_user (event_id, user_id),
  CONSTRAINT fk_bartender_sales_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_bartender_sales_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE,
  CONSTRAINT fk_bartender_sales_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE price_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_stock_id INT NOT NULL,
  event_id INT NOT NULL,
  product_id INT NOT NULL,
  old_selling_price DECIMAL(10,2) NULL,
  new_selling_price DECIMAL(10,2) NOT NULL,
  changed_by_id INT NULL,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_price_history_stock FOREIGN KEY (event_stock_id) REFERENCES event_stock(id) ON DELETE CASCADE,
  CONSTRAINT fk_price_history_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_price_history_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
  CONSTRAINT fk_price_history_user FOREIGN KEY (changed_by_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO event_salaries (event_id, user_id, bar_id, salary_amount, created_at)
SELECT b.event_id, ba.user_id, ba.bar_id, 300.00, ba.assigned_at
FROM bar_assignments ba
JOIN bars b ON b.id = ba.bar_id;

INSERT INTO price_history (event_stock_id, event_id, product_id, old_selling_price, new_selling_price, changed_by_id, changed_at)
SELECT id, event_id, product_id, NULL, selling_price_per_unit, NULL, created_at
FROM event_stock;
