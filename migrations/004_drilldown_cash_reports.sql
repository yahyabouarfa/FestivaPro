ALTER TABLE events
  ADD COLUMN IF NOT EXISTS start_date DATE NULL,
  ADD COLUMN IF NOT EXISTS total_nights_planned INT NOT NULL DEFAULT 1;

UPDATE events SET start_date = event_date WHERE start_date IS NULL;
UPDATE events SET total_nights_planned = total_nights WHERE total_nights_planned = 1;
ALTER TABLE events MODIFY start_date DATE NOT NULL;

ALTER TABLE event_nights
  ADD COLUMN IF NOT EXISTS created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE bar_night_stock
  ADD COLUMN IF NOT EXISTS qty_used DECIMAL(10,2) GENERATED ALWAYS AS (qty_opening + qty_top_up - COALESCE(qty_closing, 0)),
  ADD COLUMN IF NOT EXISTS bought_price DECIMAL(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS selling_price DECIMAL(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS expected_revenue DECIMAL(12,2) GENERATED ALWAYS AS (qty_opening * selling_price),
  ADD COLUMN IF NOT EXISTS expected_cost DECIMAL(12,2) GENERATED ALWAYS AS (qty_opening * bought_price);

UPDATE bar_night_stock bns
JOIN bars b ON b.id = bns.bar_id
JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bns.product_id
SET bns.bought_price = es.bought_price,
    bns.selling_price = es.selling_price
WHERE bns.bought_price = 0 OR bns.selling_price = 0;

CREATE TABLE IF NOT EXISTS night_bar_assignments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_night_id INT NOT NULL,
  bar_id INT NOT NULL,
  user_id INT NOT NULL,
  role VARCHAR(20) NOT NULL,
  salary_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_night_bar_assignment_user_role (event_night_id, bar_id, user_id, role),
  KEY ix_night_bar_assignments_night_bar (event_night_id, bar_id),
  CONSTRAINT fk_night_bar_assignments_night FOREIGN KEY (event_night_id) REFERENCES event_nights(id) ON DELETE CASCADE,
  CONSTRAINT fk_night_bar_assignments_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE,
  CONSTRAINT fk_night_bar_assignments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bartender_cash (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_night_id INT NOT NULL,
  bar_id INT NOT NULL,
  user_id INT NOT NULL,
  cash_collected DECIMAL(12,2) NOT NULL DEFAULT 0,
  recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bartender_cash_night_bar_user (event_night_id, bar_id, user_id),
  KEY ix_bartender_cash_night_bar (event_night_id, bar_id),
  CONSTRAINT fk_bartender_cash_night FOREIGN KEY (event_night_id) REFERENCES event_nights(id) ON DELETE CASCADE,
  CONSTRAINT fk_bartender_cash_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE,
  CONSTRAINT fk_bartender_cash_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bar_night_summary (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bar_id INT NOT NULL,
  event_night_id INT NOT NULL,
  total_cash_collected DECIMAL(12,2) NOT NULL DEFAULT 0,
  expected_cash DECIMAL(12,2) NOT NULL DEFAULT 0,
  cash_discrepancy DECIMAL(12,2) NOT NULL DEFAULT 0,
  stock_cost DECIMAL(12,2) NOT NULL DEFAULT 0,
  staff_cost DECIMAL(12,2) NOT NULL DEFAULT 0,
  gross_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
  net_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
  expected_profit DECIMAL(12,2) NOT NULL DEFAULT 0,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE,
  closed_at DATETIME NULL,
  UNIQUE KEY uq_bar_night_summary_night_bar (event_night_id, bar_id),
  KEY ix_bar_night_summary_night_bar (event_night_id, bar_id),
  CONSTRAINT fk_bar_night_summary_night FOREIGN KEY (event_night_id) REFERENCES event_nights(id) ON DELETE CASCADE,
  CONSTRAINT fk_bar_night_summary_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pdf_reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  event_id INT NOT NULL,
  event_night_id INT NULL,
  bar_id INT NULL,
  report_type VARCHAR(40) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  content_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
  data LONGBLOB NOT NULL,
  generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_pdf_reports_event_night_type (event_id, event_night_id, report_type),
  KEY ix_pdf_reports_bar_type (bar_id, report_type),
  CONSTRAINT fk_pdf_reports_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
  CONSTRAINT fk_pdf_reports_night FOREIGN KEY (event_night_id) REFERENCES event_nights(id) ON DELETE CASCADE,
  CONSTRAINT fk_pdf_reports_bar FOREIGN KEY (bar_id) REFERENCES bars(id) ON DELETE CASCADE
);
