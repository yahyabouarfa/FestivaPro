ALTER TABLE events
  ADD COLUMN IF NOT EXISTS total_nights INT NOT NULL DEFAULT 1;

ALTER TABLE event_stock
  ADD COLUMN IF NOT EXISTS total_qty_purchased DECIMAL(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS bought_price DECIMAL(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS selling_price DECIMAL(10,2) NOT NULL DEFAULT 0;

UPDATE event_stock SET total_qty_purchased = quantity_total WHERE total_qty_purchased = 0;
UPDATE event_stock SET bought_price = bought_price_per_unit WHERE bought_price = 0;
UPDATE event_stock SET selling_price = selling_price_per_unit WHERE selling_price = 0;

CREATE TABLE IF NOT EXISTS event_nights (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  night_number INT NOT NULL,
  date DATE NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'upcoming',
  UNIQUE KEY uq_event_nights_event_number (event_id, night_number),
  KEY ix_event_nights_event_id (event_id),
  KEY ix_event_nights_status (status),
  KEY ix_event_nights_event_status (event_id, status),
  CONSTRAINT fk_event_nights_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

INSERT IGNORE INTO event_nights (event_id, night_number, date, status)
SELECT id, 1, event_date, status
FROM events;

CREATE TABLE IF NOT EXISTS bar_night_stock (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bar_id INT NOT NULL,
  event_night_id INT NOT NULL,
  product_id INT NOT NULL,
  qty_opening DECIMAL(10,2) NOT NULL DEFAULT 0,
  qty_top_up DECIMAL(10,2) NOT NULL DEFAULT 0,
  qty_closing DECIMAL(10,2) NULL,
  qty_sold DECIMAL(10,2) GENERATED ALWAYS AS (qty_opening + qty_top_up - COALESCE(qty_closing, 0)),
  is_locked BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bar_night_stock_product (bar_id, event_night_id, product_id),
  KEY ix_bar_night_stock_bar_id (bar_id),
  KEY ix_bar_night_stock_event_night_id (event_night_id),
  KEY ix_bar_night_stock_product_id (product_id),
  KEY ix_bar_night_stock_night_bar (event_night_id, bar_id),
  CONSTRAINT fk_bar_night_stock_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE,
  CONSTRAINT fk_bar_night_stock_event_night FOREIGN KEY (event_night_id) REFERENCES event_nights(id) ON DELETE CASCADE,
  CONSTRAINT fk_bar_night_stock_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

INSERT IGNORE INTO bar_night_stock (bar_id, event_night_id, product_id, qty_opening, qty_top_up, qty_closing, is_locked, updated_at)
SELECT bs.bar_id, en.id, bs.product_id, bs.quantity_allocated, 0, bs.quantity_remaining, FALSE, bs.updated_at
FROM bar_stock bs
JOIN bars b ON b.id = bs.bar_id
JOIN event_nights en ON en.event_id = b.event_id AND en.night_number = 1;

CREATE TABLE IF NOT EXISTS profit_snapshots (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  event_night_id INT NULL,
  bar_id INT NULL,
  expected_revenue DECIMAL(12,2) NOT NULL DEFAULT 0,
  actual_revenue DECIMAL(12,2) NOT NULL DEFAULT 0,
  expected_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
  actual_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
  staff_cost DECIMAL(12,2) NOT NULL DEFAULT 0,
  net_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
  snapshot_level VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_profit_snapshots_event_id (event_id),
  KEY ix_profit_snapshots_event_night_id (event_night_id),
  KEY ix_profit_snapshots_bar_id (bar_id),
  KEY ix_profit_snapshots_snapshot_level (snapshot_level),
  KEY ix_profit_snapshots_event_level (event_id, snapshot_level),
  KEY ix_profit_snapshots_night_bar (event_night_id, bar_id),
  CONSTRAINT fk_profit_snapshots_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_profit_snapshots_event_night FOREIGN KEY (event_night_id) REFERENCES event_nights(id) ON DELETE CASCADE,
  CONSTRAINT fk_profit_snapshots_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE
);
