PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS auth_attempts (
    key_hash TEXT PRIMARY KEY,
    failures INTEGER NOT NULL,
    window_start INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    lead_days INTEGER NOT NULL CHECK (lead_days >= 0),
    details TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    status TEXT NOT NULL CHECK (status IN
        ('recebido', 'em_preparacao', 'enviado', 'entregue', 'cancelado')),
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    subtotal_cents INTEGER NOT NULL CHECK (subtotal_cents >= 0),
    delivery_cents INTEGER NOT NULL CHECK (delivery_cents >= 0),
    total_cents INTEGER NOT NULL CHECK (total_cents = subtotal_cents + delivery_cents),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id),
    product_name TEXT NOT NULL,
    size TEXT NOT NULL CHECK (size IN ('petite', 'classic', 'abundant')),
    quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 9),
    vase INTEGER NOT NULL CHECK (vase IN (0, 1)),
    zip TEXT NOT NULL,
    date TEXT NOT NULL,
    message TEXT NOT NULL CHECK (length(message) <= 240),
    color TEXT NOT NULL DEFAULT 'original' CHECK (color IN ('original', 'yellow', 'pink', 'white', 'red', 'lilac')),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 1000),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    delivery_fee_cents INTEGER NOT NULL CHECK (delivery_fee_cents >= 0),
    line_total_cents INTEGER NOT NULL CHECK
        (line_total_cents = (unit_price_cents + delivery_fee_cents) * quantity)
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC, id);
