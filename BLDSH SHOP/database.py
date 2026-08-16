import sqlite3

from config import STARS_RATE


db = sqlite3.connect("shop.db")

cursor = db.cursor()



# =====================
# USERS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    user_id INTEGER PRIMARY KEY,

    username TEXT,

    name TEXT,

    balance INTEGER DEFAULT 0

)
""")


# =====================
# PRODUCTS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT,

    description TEXT,

    price INTEGER,

    delivery_data TEXT,

    sold INTEGER DEFAULT 0,

    photo TEXT
)
""")

# Миграция для уже существующей базы
try:
    cursor.execute("ALTER TABLE products ADD COLUMN photo TEXT")
    db.commit()
except Exception:
    pass


# =====================
# ORDERS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    product_id INTEGER,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP

)
""")

# Миграция для уже существующей таблицы orders без столбца created_at
try:
    cursor.execute("PRAGMA table_info(orders)")
    columns = [row[1] for row in cursor.fetchall()]
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
        db.commit()
except Exception:
    pass


# =====================
# GetSMS ORDERS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS getsms_orders (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    order_id TEXT,

    service_id INTEGER,

    price REAL,

    phone_number TEXT,

    status TEXT,

    last_code TEXT,

    received_codes INTEGER DEFAULT 0,

    expire_date TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    raw_data TEXT

)
""")


db.commit()
# =====================
# PAYMENTS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS payments (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER,

    invoice_id TEXT,

    amount INTEGER,

    status TEXT DEFAULT 'pending'

)
""")

db.commit()



# =====================
# USERS
# =====================


def add_user(user_id, username, name):
    """Добавляет пользователя. Возвращает True, если пользователь новый."""
    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (
            user_id,
            username,
            name
        )
        VALUES (?, ?, ?)
        """,
        (user_id, username, name)
    )
    db.commit()
    return cursor.rowcount > 0


def get_all_user_ids():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]



def get_balance(user_id):

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE user_id=?
        """,

        (user_id,)
    )

    result = cursor.fetchone()

    return result[0] if result else 0


def get_user_by_username(username):
    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE username=?
        """,
        (username,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def add_balance(user_id, amount):

    cursor.execute(
        """
        UPDATE users

        SET balance = balance + ?

        WHERE user_id=?
        """,

        (
            amount,
            user_id
        )
    )

    db.commit()



# =====================
# PRODUCTS
# =====================


def add_product(
        title,
        description,
        price,
        delivery_data,
        photo=None
):

    cursor.execute(
        """
        INSERT INTO products
        (
            title,
            description,
            price,
            delivery_data,
            photo
        )

        VALUES (?, ?, ?, ?, ?)

        """,

        (
            title,
            description,
            price,
            delivery_data,
            photo
        )
    )

    db.commit()



def get_products():

    cursor.execute(
        """
        SELECT *

        FROM products

        WHERE sold=0
        """
    )

    return cursor.fetchall()



def get_product(product_id):

    cursor.execute(
        """
        SELECT *

        FROM products

        WHERE id=?
        """,

        (
            product_id,
        )
    )

    return cursor.fetchone()



def sell_product(product_id):

    cursor.execute(
        """
        UPDATE products

        SET sold=1

        WHERE id=?
        """,

        (
            product_id,
        )
    )

    db.commit()



def delete_product(product_id):

    cursor.execute(
        """
        DELETE FROM products

        WHERE id=?
        """,

        (
            product_id,
        )
    )

    db.commit()



# =====================
# ORDERS
# =====================


def add_order(user_id, product_id):

    cursor.execute(
        """
        INSERT INTO orders
        (
            user_id,
            product_id
        )

        VALUES (?, ?)

        """,

        (
            user_id,
            product_id
        )
    )

    db.commit()


def get_user_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    row = cursor.fetchone()
    return row[0] if row else 0


def get_sales_summary(period: str):
    cursor.execute(
        """
        SELECT COUNT(*), IFNULL(SUM(products.price), 0)
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.created_at >= datetime('now', 'localtime', ?)
        """,
        (period,)
    )
    row = cursor.fetchone()
    return (row[0] if row else 0, int(row[1] or 0))
def get_orders(user_id):

    cursor.execute(
        """
        SELECT 
            products.title,
            products.description,
            products.price,
            products.delivery_data

        FROM orders

        JOIN products
        ON orders.product_id = products.id

        WHERE orders.user_id=?

        """,
        (user_id,)
    )

    return cursor.fetchall()


def add_getsms_order(user_id, order_id, service_id, price, phone_number, status, raw_data=None):
    cursor.execute(
        """
        INSERT INTO getsms_orders
        (
            user_id,
            order_id,
            service_id,
            price,
            phone_number,
            status,
            raw_data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            order_id,
            service_id,
            price,
            phone_number,
            status,
            raw_data,
        )
    )
    db.commit()


def get_getsms_order(order_id):
    cursor.execute(
        """
        SELECT id, user_id, order_id, service_id, price, phone_number, status, last_code, received_codes, expire_date, created_at, raw_data
        FROM getsms_orders
        WHERE order_id=?
        """,
        (order_id,)
    )
    return cursor.fetchone()


def get_user_getsms_orders(user_id):
    cursor.execute(
        """
        SELECT id, order_id, service_id, price, phone_number, status, last_code, received_codes, expire_date, created_at
        FROM getsms_orders
        WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )
    return cursor.fetchall()


def update_getsms_order(order_id, status=None, last_code=None, received_codes=None, phone_number=None, expire_date=None, raw_data=None):
    updates = []
    values = []
    if status is not None:
        updates.append("status=?")
        values.append(status)
    if last_code is not None:
        updates.append("last_code=?")
        values.append(last_code)
    if received_codes is not None:
        updates.append("received_codes=?")
        values.append(received_codes)
    if phone_number is not None:
        updates.append("phone_number=?")
        values.append(phone_number)
    if expire_date is not None:
        updates.append("expire_date=?")
        values.append(expire_date)
    if raw_data is not None:
        updates.append("raw_data=?")
        values.append(raw_data)

    if not updates:
        return

    values.append(order_id)
    cursor.execute(
        f"UPDATE getsms_orders SET {', '.join(updates)} WHERE order_id=?",
        values,
    )
    db.commit()

# =====================
# PAYMENTS FUNCTIONS
# =====================


def add_payment(
    user_id,
    invoice_id,
    amount
):

    cursor.execute(
        """
        INSERT INTO payments
        (
            user_id,
            invoice_id,
            amount
        )

        VALUES (?, ?, ?)
        """,
        (
            user_id,
            invoice_id,
            amount
        )
    )

    db.commit()



def get_payment(invoice_id):

    cursor.execute(
        """
        SELECT *
        FROM payments
        WHERE invoice_id=?
        """,
        (
            invoice_id,
        )
    )

    return cursor.fetchone()



def complete_payment(invoice_id):

    cursor.execute(
        """
        UPDATE payments

        SET status='paid'

        WHERE invoice_id=?
        """,
        (
            invoice_id,
        )
    )

    db.commit()
def get_pending_payments():
    cursor.execute(
        """
        SELECT invoice_id, user_id, amount
        FROM payments
        WHERE status='pending'
        """
    )
    return cursor.fetchall()


# =====================
# MANUAL PAYMENTS (рубли)
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS manual_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT DEFAULT 'pending',
    username TEXT,
    full_name TEXT
)
""")
db.commit()


# =====================
# REFUND REQUESTS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS refund_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_before INTEGER NOT NULL,
    percent_returned INTEGER NOT NULL,
    calculated_amount INTEGER NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    admin_id INTEGER,
    admin_comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
db.commit()


def create_refund_request(user_id: int, amount_before: int, percent_returned: int, calculated_amount: int, reason: str) -> int:
    cursor.execute(
        """
        INSERT INTO refund_requests (user_id, amount_before, percent_returned, calculated_amount, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount_before, percent_returned, calculated_amount, reason)
    )
    db.commit()
    return cursor.lastrowid


def get_pending_refund_requests():
    cursor.execute(
        "SELECT id, user_id, amount_before, percent_returned, calculated_amount, reason, status, created_at FROM refund_requests WHERE status='pending' ORDER BY created_at DESC"
    )
    return cursor.fetchall()


def get_refund_request(request_id: int):
    cursor.execute(
        "SELECT id, user_id, amount_before, percent_returned, calculated_amount, reason, status, admin_id, admin_comment, created_at FROM refund_requests WHERE id=?",
        (request_id,)
    )
    return cursor.fetchone()


def approve_refund(request_id: int, approved_amount: int, admin_id: int, admin_comment: str | None = None) -> bool:
    req = get_refund_request(request_id)
    if not req or req[6] != 'pending':
        return False
    user_id = req[1]
    add_balance(user_id, approved_amount)
    cursor.execute(
        "UPDATE refund_requests SET status='approved', admin_id=?, admin_comment=? WHERE id=?",
        (admin_id, admin_comment, request_id)
    )
    db.commit()
    return True


def reject_refund(request_id: int, admin_id: int, admin_comment: str | None = None) -> bool:
    req = get_refund_request(request_id)
    if not req or req[6] != 'pending':
        return False
    cursor.execute(
        "UPDATE refund_requests SET status='rejected', admin_id=?, admin_comment=? WHERE id=?",
        (admin_id, admin_comment, request_id)
    )
    db.commit()
    return True


def create_manual_payment(user_id: int, amount: int, username: str = None, full_name: str = None) -> int:
    cursor.execute(
        """
        INSERT INTO manual_payments (user_id, amount, username, full_name)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, amount, username, full_name)
    )
    db.commit()
    return cursor.lastrowid


def get_manual_payment(payment_id: int):
    cursor.execute(
        "SELECT id, user_id, amount, status, username, full_name FROM manual_payments WHERE id=?",
        (payment_id,)
    )
    return cursor.fetchone()


def approve_manual_payment(payment_id: int) -> bool:
    row = get_manual_payment(payment_id)
    if not row or row[3] != "pending":
        return False
    cursor.execute(
        "UPDATE manual_payments SET status='approved' WHERE id=?",
        (payment_id,)
    )
    db.commit()
    return True


def reject_manual_payment(payment_id: int) -> bool:
    row = get_manual_payment(payment_id)
    if not row or row[3] != "pending":
        return False
    cursor.execute(
        "UPDATE manual_payments SET status='rejected' WHERE id=?",
        (payment_id,)
    )
    db.commit()
    return True

# =====================
# STAR GIFT REQUESTS
# =====================

cursor.execute("""
CREATE TABLE IF NOT EXISTS star_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    target_rub REAL NOT NULL,
    target_stars INTEGER NOT NULL,
    received_stars INTEGER DEFAULT 0,
    credited_rub REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Уникальный ключ входящего подарка: chat_id + message_id.
# Защищает от повторной обработки одного и того же подарка.
cursor.execute("""
CREATE TABLE IF NOT EXISTS processed_star_gifts (
    gift_key TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    stars INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
db.commit()


def create_star_request(user_id, target_rub, target_stars):
    # У пользователя может быть только одна активная заявка.
    cursor.execute("""
        UPDATE star_requests
        SET status='cancelled'
        WHERE user_id=? AND status='pending'
    """, (user_id,))
    cursor.execute("""
        INSERT INTO star_requests (user_id, target_rub, target_stars)
        VALUES (?, ?, ?)
    """, (user_id, target_rub, target_stars))
    db.commit()
    return cursor.lastrowid


def get_pending_star_request(user_id):
    cursor.execute("""
        SELECT id, user_id, target_rub, target_stars, received_stars, credited_rub, status
        FROM star_requests
        WHERE user_id=? AND status='pending'
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    return cursor.fetchone()


def get_last_star_request(user_id):
    cursor.execute("""
        SELECT id, user_id, target_rub, target_stars, received_stars, credited_rub, status
        FROM star_requests
        WHERE user_id=?
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    return cursor.fetchone()


def cancel_pending_star_requests(user_id):
    cursor.execute("""
        UPDATE star_requests
        SET status='cancelled'
        WHERE user_id=? AND status='pending'
    """, (user_id,))
    db.commit()


def _stars_to_rubles(stars):
    # 1 ⭐ = STARS_RATE ₽. Баланс магазина целочисленный, поэтому используем
    # обычное математическое округление, а не банковское round().
    return int((float(stars) / STARS_RATE) + 0.5)


def add_star_gift(user_id, stars, gift_key=None):
    """Добавляет один подарок к заявке.

    Возвращает: (request, newly_credited_rub, total_received_stars, completed, duplicate).
    Баланс по заявке зачисляется только после достижения target_stars.
    Если пользователь переплатил подарками, фактически полученные Stars
    конвертируются полностью, чтобы переплата не терялась.
    """
    stars = int(stars)
    if stars <= 0:
        return None, 0, 0, False, False

    if gift_key:
        cursor.execute("SELECT 1 FROM processed_star_gifts WHERE gift_key=?", (gift_key,))
        if cursor.fetchone():
            request = get_pending_star_request(user_id)
            received = request[4] if request else 0
            return (request and (request[0], request[2], request[3])), 0, received, bool(request and request[6] == 'completed'), True
        cursor.execute(
            "INSERT INTO processed_star_gifts (gift_key, user_id, stars) VALUES (?, ?, ?)",
            (gift_key, user_id, stars),
        )

    request = get_pending_star_request(user_id)
    if not request:
        db.commit()
        return None, _stars_to_rubles(stars), stars, False, False

    request_id, _, target_rub, target_stars, received_stars, credited_rub, status = request
    received_stars = int(received_stars or 0) + stars
    completed = received_stars >= int(target_stars)
    newly_credited = 0
    new_credited_rub = int(credited_rub or 0)

    if completed:
        # Зачисляем весь фактически полученный объём Stars, включая переплату.
        total_credit = _stars_to_rubles(received_stars)
        newly_credited = max(0, total_credit - new_credited_rub)
        new_credited_rub = total_credit

    new_status = 'completed' if completed else 'pending'
    cursor.execute("""
        UPDATE star_requests
        SET received_stars=?, credited_rub=?, status=?
        WHERE id=?
    """, (received_stars, new_credited_rub, new_status, request_id))
    db.commit()

    return (request_id, target_rub, target_stars), newly_credited, received_stars, completed, False
