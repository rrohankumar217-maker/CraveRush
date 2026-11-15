import sqlite3, hashlib, os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "craverush.db")
STAGES = ["Placed", "Preparing", "Out for Delivery", "Delivered"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT, role TEXT);
CREATE TABLE IF NOT EXISTS restaurants(id INTEGER PRIMARY KEY, owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE, name TEXT, cuisine TEXT);
CREATE TABLE IF NOT EXISTS menu(id INTEGER PRIMARY KEY, rest_id INTEGER REFERENCES restaurants(id) ON DELETE CASCADE, name TEXT, category TEXT, price REAL, available INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES users(id), rest_id INTEGER REFERENCES restaurants(id), subtotal REAL, tax REAL, delivery REAL, total REAL, status TEXT DEFAULT 'Placed', created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE, name TEXT, price REAL, qty INTEGER);
"""

def h(p): return hashlib.sha256(p.encode()).hexdigest()

def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

def q(sql, args=(), one=False):
    c = conn(); rows = c.execute(sql, args).fetchall(); c.close()
    return (rows[0] if rows else None) if one else rows

def ex(sql, args=()):
    c = conn(); cur = c.execute(sql, args); c.commit(); i = cur.lastrowid; c.close(); return i

def init():
    c = conn(); c.executescript(SCHEMA); c.commit(); c.close()
    if q("SELECT 1 FROM users", one=True): return
    ex("INSERT INTO users(name,email,phone,password,role) VALUES('Admin','admin@craverush.com','0',?,'admin')", (h("admin123"),))
    ex("INSERT INTO users(name,email,phone,password,role) VALUES('Demo Customer','cust@craverush.com','9999999999',?,'customer')", (h("cust123"),))
    data = [("spice@craverush.com", "Spice Garden", "South Indian",
             [("Masala Dosa", "Tiffin", 90), ("Idli Sambar", "Tiffin", 60), ("Chicken Biryani", "Main", 220), ("Filter Coffee", "Drinks", 40)]),
            ("pizza@craverush.com", "Pizza Planet", "Italian",
             [("Margherita Pizza", "Pizza", 249), ("Farmhouse Pizza", "Pizza", 349), ("Garlic Bread", "Sides", 119), ("Cold Coffee", "Drinks", 99)])]
    for email, rn, cu, items in data:
        uid = ex("INSERT INTO users(name,email,phone,password,role) VALUES(?,?,?,?,'restaurant')", (rn + " Owner", email, "8888888888", h("rest123")))
        rid = ex("INSERT INTO restaurants(owner_id,name,cuisine) VALUES(?,?,?)", (uid, rn, cu))
        for n, cat, p in items:
            ex("INSERT INTO menu(rest_id,name,category,price) VALUES(?,?,?,?)", (rid, n, cat, p))

def login(email, pw, role):
    return q("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email, h(pw), role), one=True)

def register(name, email, phone, pw, role, rname="", cuisine=""):
    uid = ex("INSERT INTO users(name,email,phone,password,role) VALUES(?,?,?,?,?)", (name, email, phone, h(pw), role))
    if role == "restaurant":
        ex("INSERT INTO restaurants(owner_id,name,cuisine) VALUES(?,?,?)", (uid, rname or name + "'s Kitchen", cuisine or "Multi-cuisine"))
    return uid

def place_order(cust_id, rest_id, cart):
    sub = sum(p * n for _, p, n in cart.values()); tax = round(sub * 0.05, 2); fee = 30.0
    oid = ex("INSERT INTO orders(customer_id,rest_id,subtotal,tax,delivery,total) VALUES(?,?,?,?,?,?)",
             (cust_id, rest_id, sub, tax, fee, sub + tax + fee))
    for name, price, qty in cart.values():
        ex("INSERT INTO order_items(order_id,name,price,qty) VALUES(?,?,?,?)", (oid, name, price, qty))
    return oid

def bill_text(oid):
    o = q("SELECT o.*, r.name rname, u.name cname FROM orders o JOIN restaurants r ON r.id=o.rest_id JOIN users u ON u.id=o.customer_id WHERE o.id=?", (oid,), one=True)
    L = ["=" * 44, "           CRAVERUSH - INVOICE", "=" * 44,
         f"Order #{o['id']}    {o['created']}", f"Customer  : {o['cname']}", f"Restaurant: {o['rname']}",
         "-" * 44, f"{'Item':<22}{'Qty':>4}{'Price':>8}{'Amt':>8}", "-" * 44]
    for i in q("SELECT * FROM order_items WHERE order_id=?", (oid,)):
        L.append(f"{i['name'][:21]:<22}{i['qty']:>4}{i['price']:>8.0f}{i['price'] * i['qty']:>8.0f}")
    L += ["-" * 44, f"{'Subtotal':<34}{o['subtotal']:>10.2f}", f"{'GST (5%)':<34}{o['tax']:>10.2f}",
          f"{'Delivery fee':<34}{o['delivery']:>10.2f}", "=" * 44, f"{'TOTAL (Rs.)':<34}{o['total']:>10.2f}",
          "=" * 44, f"Status: {o['status']}", "Thank you for ordering with CraveRush!"]
    return "\n".join(L)
