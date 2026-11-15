import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import db

ORANGE, DARK, LIGHT = "#fc8019", "#282c3f", "#f5f5f5"

def table(parent, cols, h=12):
    t = ttk.Treeview(parent, columns=cols, show="headings", height=h)
    for c in cols:
        t.heading(c, text=c); t.column(c, width=60 if c in ("ID", "Qty") else 130)
    return t

def fill(t, rows):
    t.delete(*t.get_children())
    for r in rows: t.insert("", "end", values=tuple(r))

def sel(t):
    s = t.selection()
    return t.item(s[0])["values"] if s else None

def btn(parent, text, cmd, side="left"):
    b = tk.Button(parent, text=text, command=cmd, bg=ORANGE, fg="white", relief="flat", padx=12, pady=4, cursor="hand2")
    b.pack(side=side, padx=4, pady=4); return b

def header(frame, app, title, nav=()):
    bar = tk.Frame(frame, bg=DARK); bar.pack(fill="x")
    tk.Label(bar, text="CraveRush", bg=DARK, fg=ORANGE, font=("Segoe UI", 18, "bold")).pack(side="left", padx=12, pady=8)
    tk.Label(bar, text=title, bg=DARK, fg="white", font=("Segoe UI", 12)).pack(side="left", padx=12)
    btn(bar, "Logout", app.logout, "right")
    for text, cmd in nav: btn(bar, text, cmd, "right")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CraveRush - Online Food Ordering"); self.geometry("1000x650"); self.configure(bg=LIGHT)
        self.user, self.cart, self.rest_id = None, {}, None
        self.box = tk.Frame(self); self.box.pack(fill="both", expand=True)
        self.show(LoginPage)

    def show(self, cls, **kw):
        for w in self.box.winfo_children(): w.destroy()
        cls(self.box, self, **kw).pack(fill="both", expand=True)

    def logout(self):
        self.user, self.cart, self.rest_id = None, {}, None; self.show(LoginPage)

    def home(self):
        role = self.user["role"]
        self.show({"customer": MenuPage, "restaurant": RestaurantDashboard, "admin": AdminDashboard}[role])

class LoginPage(tk.Frame):
    def __init__(s, p, app):
        super().__init__(p, bg=ORANGE); s.app = app
        card = tk.Frame(s, bg="white", padx=40, pady=30); card.place(relx=.5, rely=.5, anchor="center")
        tk.Label(card, text="CraveRush", fg=ORANGE, bg="white", font=("Segoe UI", 28, "bold")).pack()
        tk.Label(card, text="Hungry? Crave it. Rush it.", bg="white", fg="gray").pack(pady=(0, 15))
        s.role = ttk.Combobox(card, values=["customer", "restaurant", "admin"], state="readonly"); s.role.set("customer")
        s.email, s.pw = tk.Entry(card, width=32), tk.Entry(card, width=32, show="*")
        for lbl, w in (("Login as", s.role), ("Email", s.email), ("Password", s.pw)):
            tk.Label(card, text=lbl, bg="white", anchor="w").pack(fill="x"); w.pack(fill="x", pady=(0, 8))
        tk.Button(card, text="Login", command=s.go, bg=ORANGE, fg="white", relief="flat", pady=5).pack(fill="x", pady=6)
        tk.Button(card, text="New here? Register", command=lambda: app.show(RegisterPage), relief="flat", bg="white", fg=DARK).pack()
        tk.Label(card, text="Demo: cust@craverush.com/cust123 | spice@craverush.com/rest123\nadmin@craverush.com/admin123",
                 bg="white", fg="gray", font=("Segoe UI", 8)).pack(pady=8)
        s.pw.bind("<Return>", lambda e: s.go())

    def go(s):
        u = db.login(s.email.get().strip(), s.pw.get(), s.role.get())
        if not u: return messagebox.showerror("Login failed", "Invalid email, password or role.")
        s.app.user = dict(u); s.app.home()

class RegisterPage(tk.Frame):
    def __init__(s, p, app):
        super().__init__(p, bg=ORANGE); s.app = app
        card = tk.Frame(s, bg="white", padx=40, pady=25); card.place(relx=.5, rely=.5, anchor="center")
        tk.Label(card, text="Create your account", fg=ORANGE, bg="white", font=("Segoe UI", 20, "bold")).pack(pady=(0, 10))
        s.f = {}
        for key, lbl in (("name", "Full name"), ("email", "Email"), ("phone", "Phone"), ("pw", "Password"),
                         ("rname", "Restaurant name (restaurants only)"), ("cuisine", "Cuisine (restaurants only)")):
            tk.Label(card, text=lbl, bg="white", anchor="w").pack(fill="x")
            s.f[key] = tk.Entry(card, width=34, show="*" if key == "pw" else ""); s.f[key].pack(fill="x", pady=(0, 6))
        s.role = ttk.Combobox(card, values=["customer", "restaurant"], state="readonly"); s.role.set("customer")
        tk.Label(card, text="Register as", bg="white", anchor="w").pack(fill="x"); s.role.pack(fill="x")
        tk.Button(card, text="Register", command=s.go, bg=ORANGE, fg="white", relief="flat", pady=5).pack(fill="x", pady=8)
        tk.Button(card, text="Back to login", command=lambda: app.show(LoginPage), relief="flat", bg="white").pack()

    def go(s):
        v = {k: e.get().strip() for k, e in s.f.items()}
        if not (v["name"] and v["email"] and v["pw"]): return messagebox.showwarning("Missing", "Name, email and password are required.")
        try: db.register(v["name"], v["email"], v["phone"], v["pw"], s.role.get(), v["rname"], v["cuisine"])
        except sqlite3.IntegrityError: return messagebox.showerror("Error", "Email already registered.")
        messagebox.showinfo("Done", "Account created. Please login."); s.app.show(LoginPage)

class MenuPage(tk.Frame):
    def __init__(s, p, app):
        super().__init__(p); s.app = app
        header(s, app, f"Hi, {app.user['name']}", [("My Orders", lambda: app.show(OrderPage))])
        body = tk.Frame(s); body.pack(fill="both", expand=True, padx=10, pady=8)
        left = tk.Frame(body); left.pack(side="left", fill="both", expand=True)
        top = tk.Frame(left); top.pack(fill="x")
        s.rests = db.q("SELECT * FROM restaurants")
        s.rv = ttk.Combobox(top, state="readonly", width=34, values=[f"{r['name']} - {r['cuisine']}" for r in s.rests])
        s.rv.pack(side="left"); s.rv.bind("<<ComboboxSelected>>", s.load)
        tk.Label(top, text=" Search:").pack(side="left"); s.sv = tk.Entry(top); s.sv.pack(side="left"); s.sv.bind("<KeyRelease>", s.load)
        s.items = table(left, ("ID", "Item", "Category", "Price"), 15); s.items.pack(fill="both", expand=True, pady=6)
        row = tk.Frame(left); row.pack(fill="x"); tk.Label(row, text="Qty").pack(side="left")
        s.qty = tk.Spinbox(row, from_=1, to=20, width=4); s.qty.pack(side="left"); btn(row, "Add to Cart", s.add)
        right = tk.Frame(body, padx=10); right.pack(side="right", fill="y")
        tk.Label(right, text="Your Cart", font=("Segoe UI", 14, "bold")).pack()
        s.cart = table(right, ("ID", "Item", "Qty", "Price"), 12); s.cart.pack()
        s.total = tk.Label(right, text="", font=("Segoe UI", 11, "bold")); s.total.pack(pady=6)
        r2 = tk.Frame(right); r2.pack(); btn(r2, "Remove", s.remove); btn(r2, "Place Order", s.place)
        if app.rest_id:
            i = [r["id"] for r in s.rests].index(app.rest_id); s.rv.current(i); s.load()
        s.refresh()

    def load(s, _=None):
        i = s.rv.current()
        if i < 0: return
        s.app_rest = s.rests[i]["id"]
        rows = db.q("SELECT id,name,category,price FROM menu WHERE rest_id=? AND available=1 AND name LIKE ?", (s.app_rest, f"%{s.sv.get()}%"))
        fill(s.items, rows)

    def add(s):
        it = sel(s.items)
        if not it: return messagebox.showinfo("Select", "Pick an item first.")
        if s.app.rest_id and s.app.rest_id != s.app_rest and s.app.cart:
            if not messagebox.askyesno("New restaurant", "Cart has items from another restaurant. Clear it?"): return
            s.app.cart = {}
        s.app.rest_id = s.app_rest; n = int(s.qty.get())
        mid, name, _, price = it; cur = s.app.cart.get(mid, [name, float(price), 0]); cur[2] += n; s.app.cart[mid] = cur; s.refresh()

    def remove(s):
        it = sel(s.cart)
        if it: s.app.cart.pop(int(it[0]), None); s.refresh()

    def refresh(s):
        fill(s.cart, [(k, v[0], v[2], v[1] * v[2]) for k, v in s.app.cart.items()])
        s.total.config(text=f"Subtotal: Rs. {sum(v[1] * v[2] for v in s.app.cart.values()):.2f}")

    def place(s):
        if not s.app.cart: return messagebox.showinfo("Empty", "Add something tasty first!")
        oid = db.place_order(s.app.user["id"], s.app.rest_id, s.app.cart); s.app.cart = {}
        s.app.show(OrderPage, oid=oid)

class OrderPage(tk.Frame):
    def __init__(s, p, app, oid=None):
        super().__init__(p); s.app = app; s.sim = set()
        header(s, app, "My Orders", [("Browse Menu", lambda: app.show(MenuPage))])
        s.t = table(s, ("ID", "Restaurant", "Total", "Status", "Placed at"), 10); s.t.pack(fill="x", padx=10, pady=10)
        s.t.bind("<<TreeviewSelect>>", lambda e: s.show_status())
        s.lbl = tk.Label(s, text="Select an order to track", font=("Segoe UI", 13, "bold")); s.lbl.pack()
        s.bar = ttk.Progressbar(s, length=600, maximum=3); s.bar.pack(pady=6)
        s.steps = tk.Label(s, text="  >  ".join(db.STAGES), fg="gray"); s.steps.pack()
        r = tk.Frame(s); r.pack(pady=10); btn(r, "Track (simulate)", s.track); btn(r, "View Bill", s.bill)
        s.load(oid); s.poll()

    def load(s, oid=None):
        fill(s.t, [(r["id"], r["rname"], f"{r['total']:.2f}", r["status"], r["created"]) for r in db.q(
            "SELECT o.*, r.name rname FROM orders o JOIN restaurants r ON r.id=o.rest_id WHERE customer_id=? ORDER BY o.id DESC", (s.app.user["id"],))])
        if oid:
            for iid in s.t.get_children():
                if s.t.item(iid)["values"][0] == oid: s.t.selection_set(iid)

    def cur(s):
        v = sel(s.t); return int(v[0]) if v else None

    def show_status(s):
        oid = s.cur()
        if not oid: return
        st = db.q("SELECT status FROM orders WHERE id=?", (oid,), one=True)["status"]
        s.bar["value"] = db.STAGES.index(st); s.lbl.config(text=f"Order #{oid}: {st}")

    def track(s):
        oid = s.cur()
        if not oid: return messagebox.showinfo("Select", "Select an order first.")
        if oid in s.sim: return
        s.sim.add(oid); s.step(oid)

    def step(s, oid):
        if not s.winfo_exists(): return
        st = db.q("SELECT status FROM orders WHERE id=?", (oid,), one=True)["status"]; i = db.STAGES.index(st)
        if i < 3:
            db.ex("UPDATE orders SET status=? WHERE id=?", (db.STAGES[i + 1], oid)); s.app.after(3000, lambda: s.step(oid))
        else: s.sim.discard(oid)
        s.load(oid); s.show_status()

    def poll(s):
        if s.winfo_exists(): s.show_status(); s.app.after(2000, s.poll)

    def bill(s):
        oid = s.cur()
        if not oid: return messagebox.showinfo("Select", "Select an order first.")
        w = tk.Toplevel(s); w.title(f"Bill - Order #{oid}")
        t = tk.Text(w, font=("Courier New", 10), width=48, height=24); t.insert("1.0", db.bill_text(oid)); t.config(state="disabled"); t.pack(padx=10, pady=10)

class RestaurantDashboard(tk.Frame):
    def __init__(s, p, app):
        super().__init__(p); s.app = app
        s.r = db.q("SELECT * FROM restaurants WHERE owner_id=?", (app.user["id"],), one=True)
        header(s, app, f"Restaurant Dashboard - {s.r['name']}")
        nb = ttk.Notebook(s); nb.pack(fill="both", expand=True, padx=10, pady=10)
        o, m = tk.Frame(nb), tk.Frame(nb); nb.add(o, text="Incoming Orders"); nb.add(m, text="Manage Menu")
        s.ot = table(o, ("ID", "Customer", "Total", "Status", "Placed at"), 12); s.ot.pack(fill="both", expand=True, pady=6)
        r = tk.Frame(o); r.pack()
        for st in db.STAGES[1:]: btn(r, f"Mark {st}", lambda st=st: s.setst(st))
        btn(r, "Refresh", s.load_o); s.rev = tk.Label(o, font=("Segoe UI", 12, "bold")); s.rev.pack()
        s.mt = table(m, ("ID", "Item", "Category", "Price", "Available"), 12); s.mt.pack(fill="both", expand=True, pady=6)
        f = tk.Frame(m); f.pack(); s.e = [tk.Entry(f, width=18) for _ in range(3)]
        for lbl, e in zip(("Name", "Category", "Price"), s.e): tk.Label(f, text=lbl).pack(side="left"); e.pack(side="left", padx=4)
        btn(f, "Add Item", s.add); btn(f, "Toggle Availability", s.toggle); btn(f, "Delete", s.delete)
        s.load_o(); s.load_m()

    def load_o(s):
        fill(s.ot, [(r["id"], r["cname"], f"{r['total']:.2f}", r["status"], r["created"]) for r in db.q(
            "SELECT o.*, u.name cname FROM orders o JOIN users u ON u.id=o.customer_id WHERE rest_id=? ORDER BY o.id DESC", (s.r["id"],))])
        tot = db.q("SELECT COALESCE(SUM(total),0) t FROM orders WHERE rest_id=?", (s.r["id"],), one=True)["t"]
        s.rev.config(text=f"Total revenue: Rs. {tot:.2f}")

    def load_m(s):
        fill(s.mt, [(r["id"], r["name"], r["category"], r["price"], "Yes" if r["available"] else "No") for r in db.q("SELECT * FROM menu WHERE rest_id=?", (s.r["id"],))])

    def setst(s, st):
        v = sel(s.ot)
        if v: db.ex("UPDATE orders SET status=? WHERE id=?", (st, v[0])); s.load_o()

    def add(s):
        n, c, p = [e.get().strip() for e in s.e]
        try: db.ex("INSERT INTO menu(rest_id,name,category,price) VALUES(?,?,?,?)", (s.r["id"], n, c or "General", float(p)))
        except ValueError: return messagebox.showerror("Error", "Enter a valid price.")
        s.load_m()

    def toggle(s):
        v = sel(s.mt)
        if v: db.ex("UPDATE menu SET available=1-available WHERE id=?", (v[0],)); s.load_m()

    def delete(s):
        v = sel(s.mt)
        if v: db.ex("DELETE FROM menu WHERE id=?", (v[0],)); s.load_m()

class AdminDashboard(tk.Frame):
    def __init__(s, p, app):
        super().__init__(p); header(s, app, "Admin Panel")
        nb = ttk.Notebook(s); nb.pack(fill="both", expand=True, padx=10, pady=10)
        s.tabs = {}
        for name, cols, sql in (("Users", ("ID", "Name", "Email", "Role"), "SELECT id,name,email,role FROM users"),
                                ("Restaurants", ("ID", "Name", "Cuisine"), "SELECT id,name,cuisine FROM restaurants"),
                                ("Orders", ("ID", "Restaurant", "Total", "Status"), "SELECT o.id,r.name,o.total,o.status FROM orders o JOIN restaurants r ON r.id=o.rest_id")):
            f = tk.Frame(nb); nb.add(f, text=name); t = table(f, cols, 16); t.pack(fill="both", expand=True); fill(t, db.q(sql)); s.tabs[name] = (t, sql)
        btn(s.tabs["Users"][0].master, "Delete selected user", s.deluser)

    def deluser(s):
        t, sql = s.tabs["Users"]; v = sel(t)
        if v and v[3] != "admin" and messagebox.askyesno("Confirm", f"Delete {v[1]}?"):
            try: db.ex("DELETE FROM users WHERE id=?", (v[0],)); fill(t, db.q(sql))
            except sqlite3.IntegrityError: messagebox.showerror("Error", "User has existing orders.")

if __name__ == "__main__":
    db.init(); App().mainloop()
