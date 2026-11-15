-- Reference copy of the SQLite schema (db.py creates it automatically)

CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, role TEXT);
CREATE TABLE IF NOT EXISTS restaurants(id INTEGER PRIMARY KEY, owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE, name TEXT, cuisine TEXT);
CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY, rest_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE, name TEXT, category TEXT, price REAL, available INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES users(id), rest_id INTEGER REFERENCES restaurants(id), subtotal REAL, tax REAL, delivery REAL, total REAL, status TEXT DEFAULT 'Placed', created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE, name TEXT, price REAL, qty INTEGER);
