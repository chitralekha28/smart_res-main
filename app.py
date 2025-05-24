# from flask import Flask, render_template, request, redirect, url_for, session, jsonify
# import mysql.connector
# import os
# import re



# app = Flask(__name__)
# app.secret_key = 'supersecretkey'
# # Load model and encoders
# app.secret_key = os.urandom(24)
# # Database connection
# db = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="",
#     database="smartes"
# )
# cursor = db.cursor()
# @app.route('/home')
# def home():
#     if 'user_id' in session:
#         return render_template('index.html')
#     else:
#         return redirect(url_for('login'))

# @app.route('/login_validation', methods=['POST'])
# def login_validation():
#     email = request.form.get('email')
#     password = request.form.get('password')

#     cursor.execute("SELECT * FROM `` WHERE `email` = %s AND `password` = %s", (email, password))
#     users = cursor.fetchall()

#     if len(users) > 0:
#         session['user_id'] = users[0][0]
#         session['firstname'] = users[0][1]  # Assuming the first name is stored at index 1
#         print(f"User ID: {session['user_id']}, Firstname: {session['firstname']}")  # Debugging session values
#         return redirect(url_for('home'))
#     else:
#         flash('Invalid Email or Password', 'danger')
#         return redirect(url_for('login'))

# @app.route('/add_user', methods=['POST'])
# def add_user():
#     firstname = request.form.get('ufirstName')
#     lastname = request.form.get('ulastName')
#     email = request.form.get('uemail')
#     password = request.form.get('upassword')

#     sql = "INSERT INTO `user` (`id`, `firstname`, `lastname`, `email`, `password`) VALUES (NULL, %s, %s, %s, %s)"
#     values = (firstname, lastname, email, password)

#     try:
#         cursor.execute(sql, values)
#         conn.commit()
#         flash('Registration Successful! Please login.', 'success')
#         return redirect(url_for('login'))
#     except mysql.connector.Error as err:
#         print(f"Database Error: {err}")
#         flash('Registration failed. Try again.', 'danger')
#         return redirect(url_for('register'))

# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     return redirect(url_for('index'))

# # @app.route('/', methods=['GET', 'POST'])
# # def login():
# #     msg = ''
# #     if request.method == 'POST':
# #         username = request.form['username']
# #         password = request.form['password']
# #         cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
# #         account = cursor.fetchone()
# #         if account:
# #             session['loggedin'] = True
# #             session['username'] = username
# #             return redirect(url_for('home'))
# #         else:
# #             msg = 'Incorrect username or password!'
# #     return render_template('login.html', msg=msg)

# @app.route('/home')
# def home():
#     if 'loggedin' in session:
#         return render_template('index.html')
#     return redirect(url_for('login'))

# @app.route('/menu')
# def menu():
#     cursor.execute("SELECT * FROM menu")
#     items = cursor.fetchall()
#     return render_template('menu.html', items=items)

# @app.route('/cart')
# def cart():
#     return render_template('cart.html')

# @app.route('/place_order', methods=['POST'])
# def place_order():
#     data = request.get_json()
#     items = data['items']
#     total = data['total']
#     cursor.execute("INSERT INTO orders (username, total, status) VALUES (%s, %s, %s)", (session['username'], total, 'Pending'))
#     db.commit()
#     return jsonify({'message': 'Order placed successfully!'})

# @app.route('/dashboard')
# def dashboard():
#     cursor.execute("SELECT * FROM orders")
#     orders = cursor.fetchall()
#     return render_template('dashboard.html', orders=orders)

# @app.route('/logout')
# def logout():
#     session.pop('loggedin', None)
#     session.pop('username', None)
#     return redirect(url_for('login'))

# if __name__ == "__main__":
#     app.run(debug=True)
import os
import mysql.connector
import logging
from flask_cors import CORS

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

app.secret_key = os.urandom(24)  # Secure secret key for session management

# Database connection function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='restaurantdb'
        )
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        return None

# ---------- ROUTES ---------- #

@app.route('/')
@app.route('/qr')
def qr():
    return render_template('qr.html')

@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/owner')
def owner():
    return render_template('owner.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('login.html')  # ✅ Combined page


@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')
@app.route('/dashboard')
def dashboard():
    role = session.get('role', 'customer')  # Default to 'customer' if not set

    if role == 'owner':
        return render_template('dashboard.html')  # Admin dashboard
    else:
        return render_template('customer_dashboard.html')  # Customer dashboard


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/get_orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    if conn is None:
        return jsonify([]), 500
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
    SELECT 
        o.id AS order_id, o.name AS customer_name, o.table_number, o.total_amount,
        mi.name AS item_name, mi.price
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    JOIN menu_items mi ON oi.menu_item_id = mi.id
    WHERE o.id = (SELECT MAX(id) FROM orders)
""")

        orders = cursor.fetchall()

        # 🔁 Group by order_id
        grouped_orders = {}
        for row in orders:
            oid = row["order_id"]
            if oid not in grouped_orders:
                grouped_orders[oid] = {
                    "order_id": oid,
                    "customer_name": row["customer_name"],
                    "table_number": row["table_number"],
                    "total_amount": row["total_amount"],
                    "items": []
                }
            grouped_orders[oid]["items"].append({
                "item_name": row["item_name"],
                "price": row["price"]
            })

        return jsonify(list(grouped_orders.values()))

    except Exception as e:
        logging.error(f"Error fetching orders: {e}")
        return jsonify([]), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/clear_orders', methods=['POST'])
def clear_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM order_items")
        conn.commit()
        return jsonify({"status": "All orders cleared!"}), 200
    except Exception as e:
        logging.error(f"Error clearing orders: {e}")
        return jsonify({"status": "Error clearing orders"}), 500
    finally:
        cursor.close()
        conn.close()


# ---------- AUTH ROUTES ---------- #

@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    if conn is None:
        flash("Database connection failed.", "danger")
        return redirect(url_for('login'))

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['username'] = user['name']
            session['user_id'] = user['id']
            session['role'] = user.get('role', 'customer')  # optional, if using roles
            flash("Login successful!", "success")
            return redirect(url_for('menu'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    finally:
        cursor.close()
        conn.close()


@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    if conn is None:
        flash("Database connection failed.", "danger")
        return redirect(url_for('register'))

    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        flash("Registered successfully! Please log in.", "success")
        return redirect(url_for('login'))

    except mysql.connector.IntegrityError:
        flash("Email already exists. Try logging in.", "danger")
        return redirect(url_for('register'))

    finally:
        cursor.close()
        conn.close()

# ---------- ORDER ROUTES ---------- #

@app.route('/place_order', methods=['POST'])
def place_order():
    conn = None
    cursor = None

    try:
        order_data = request.get_json()
        logging.debug(f"Received order data: {order_data}")

        if not order_data:
            return jsonify({"error": "No data received"}), 400
        if 'table_number' not in order_data:
            return jsonify({"error": "Missing 'table_number' in order data"}), 400
        if 'items' not in order_data:
            return jsonify({"error": "Missing 'items' in order data"}), 400

        table_number = order_data['table_number']
        customer_name = order_data.get('name', 'Guest')
        items = order_data['items']

        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor()

        # 🟩 Calculate total amount
        total_amount = 0
        for item in items:
            item_id = item['item_id']
            quantity = item['quantity']

            # Fetch price of the item
            cursor.execute("SELECT price FROM menu_items WHERE id = %s", (item_id,))
            price_result = cursor.fetchone()
            if price_result:
                price = price_result[0]
                total_amount += price * quantity

        # 🟩 Insert order with total_amount
        cursor.execute(
            "INSERT INTO orders (table_number, name, total_amount) VALUES (%s, %s, %s)",
            (table_number, customer_name, total_amount)
        )
        order_id = cursor.lastrowid

        # Insert order items
        for item in items:
            item_id = item['item_id']
            quantity = item['quantity']
            cursor.execute(
                "INSERT INTO order_items (order_id, menu_item_id, quantity) VALUES (%s, %s, %s)",
                (order_id, item_id, quantity)
            )

        conn.commit()
        return jsonify({"message": "Order placed successfully!"}), 200

    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error placing order: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ---------- MAIN ---------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
