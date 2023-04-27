from flask import Flask, redirect, request, render_template, session
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = "nothing"

@app.route("/farmer-login")
def show_farmer_login():
    product_types = []
    with open("E:\\Sathwik\\IIT KGP\\3.2\\IS Project\\Website\\HTML\\product_types.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            product_types.append(row[0])

    products = []
    with open("E:\\Sathwik\\IIT KGP\\3.2\\IS Project\\Website\\HTML\\products.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            products.append(row[0])
    
    return render_template(
        'Farmer_login.html',
        product_types=product_types,
        products=products)

@app.route('/transporter-login')
def transporter_dashboard():
    # Check if there is a user logged in
    if 'email' not in session:
        return redirect('/login')
    # Retrieve cart items for logged in user from the database
    conn = sqlite3.connect('organic_farming.db')
    c = conn.cursor()
    c.execute('''SELECT state FROM users WHERE email = ?''', (session['email'],))
    user_state = c.fetchone()[0]
    ord = c.execute('''SELECT * FROM orders WHERE state=?''', (user_state,)).fetchall()
    conn.close()
    
    return render_template('transporter_login.html', ord=ord)

@app.route('/delivery', methods=['POST'])
def accept_delivery():
    # Check if there is a user logged in
    if 'email' not in session:
        return redirect('/login')

    # Retrieve the user's state
    conn = sqlite3.connect("organic_farming.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS deliveries
            (delivery_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, order_id INT, quantity INT, dist INT, price_per_km INT, delivery_price INT, 
            FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (order_id) REFERENCES orders (order_id) )
    ''')
    user = c.execute(''' SELECT * FROM users WHERE email=? ''', (session['email'], )).fetchone()

    # Iterate through the selected deliveries and insert into the deliveries table
    for item in request.form:
        if item.startswith('Delivery') and request.form[item] == 'on':
            order_id = item.replace('Delivery', '')
            quantity = int(c.execute('''SELECT total_quantity FROM orders WHERE order_id=?''', (order_id,)).fetchone()[0])
            dist = int(request.form.get('Dist' + order_id, 0))
            price_per_km = int(request.form.get('Price_dist' + order_id, 0))
            delivery_price = dist * price_per_km
            c.execute('''INSERT INTO deliveries (user_id, order_id, quantity, dist, price_per_km, delivery_price) 
                         VALUES (?, ?, ?, ?, ?, ?)''', (user[0], order_id, quantity, dist, price_per_km, delivery_price))
            conn.commit()

    conn.close()
    return redirect('/transporter-login')


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    email = session.get("email")
    if email is None:
        return "Please login to add items to cart"
    
    # Get list of products
    conn = sqlite3.connect("organic_farming.db")
    c = conn.cursor()
    product_ids = [i for (i,) in
                list(c.execute('''
                    SELECT product_id FROM products;
                '''))]

    # Retrieve form data
    quantities = [request.form.get(f"Quantity{product_id}",0) for product_id in product_ids]
    
    # Create database connection
    conn = sqlite3.connect("organic_farming.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cart
            (cart_product_id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INT, 
            product_name TEXT, quantity INT, price_per_unit INT, total_price INT, email TEXT)
    ''')

    # Iterate over selected products and insert into cart
    for i in range(len(product_ids)):
        if request.form.get("Product{}".format(product_ids[i])):
            product_id = int(product_ids[i])
            
            # Fetch product details from the 'vegetables' table
            conn_veg = sqlite3.connect("organic_farming.db")
            c_veg = conn_veg.cursor()
            c_veg.execute("SELECT product_name, unitprice FROM products WHERE product_id=?", (product_id,))
            product_data = c_veg.fetchone()
            conn_veg.close()
            
            # Calculate total price
            quantity = int(quantities[i])
            price_per_unit = int(product_data[1])
            total_price = quantity * price_per_unit
            
            c.execute("INSERT INTO cart (product_id, product_name, quantity, price_per_unit, total_price, email) VALUES (?, ?, ?, ?, ?, ?)", (product_id, product_data[0], quantity, price_per_unit, total_price, email))
    
    # Save changes and close connection
    conn.commit()
    conn.close()

    return redirect('/cart')

@app.route('/cart')
def cart():
    # Check if there is a user logged in
    if 'email' not in session:
        return redirect('/login')
    # Retrieve cart items for logged in user from the database
    conn = sqlite3.connect('organic_farming.db')
    c = conn.cursor()
    cart_items = c.execute('''SELECT * FROM cart WHERE email=?''', (session['email'],)).fetchall()
    conn.close()

    return render_template('products.html', cart_items=cart_items)

@app.route('/view_products')
def view_prod():
    # Check if there is a user logged in
    if 'email' not in session:
        return redirect('/login')
    # Retrieve cart items for logged in user from the database
    conn = sqlite3.connect('organic_farming.db')
    c = conn.cursor()
    c.execute('''SELECT id FROM users WHERE email=?''', (session['email'],))
    user_id = c.fetchone()[0]
    view_products = c.execute('''SELECT * FROM products WHERE user_id=?''', (user_id,)).fetchall()
    conn.close()

    return redirect('/farmer-login', view_products=view_products)


@app.route('/clear_cart', methods=['GET', 'POST'])
def clear_cart():
    if "email" in session:
        email = session["email"]
        conn = sqlite3.connect("organic_farming.db")
        c = conn.cursor()
        c.execute("DELETE FROM cart WHERE email=?", (email,))
        conn.commit()
        conn.close()
        return redirect('/cart')
    else:
        return redirect('/login')


@app.route('/submit_order', methods=['POST'])
def submit_order():
    # Check if there is a user logged in
    if 'email' not in session:
        return redirect('/login')
    name = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    
    conn = sqlite3.connect('organic_farming.db')
    cursor = conn.cursor()
    cart_items = cursor.execute('''SELECT * FROM cart WHERE email=?''', (session['email'],)).fetchall()
    total_price = sum(item[5] for item in cart_items)
    total_quantity = sum(item[3] for item in cart_items)

    # get user ID from the session
    user_email = session['email']
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_id = cursor.fetchone()[0]
    cursor.execute('''SELECT state FROM users WHERE email = ?''', (user_email,))
    user_state = cursor.fetchone()[0]
    
    # insert new order into the table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders
            (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, 
            name TEXT, address TEXT, state TEXT, phone TEXT,total_quantity INT, total_price INT)
    ''')
    cursor.execute('''INSERT INTO orders (user_id, name, address, state, phone, total_quantity, total_price) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', (user_id, name, address, user_state, phone, total_quantity, total_price))
    
    # get the ID of the newly inserted order
    order_id = cursor.lastrowid
    
    # insert order items into the table
    for item in cart_items:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items
            (order_item_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INT, 
            product_id INT, quantity INT, price_per_unit INT)
    ''')
        cursor.execute('''INSERT INTO order_items (order_id, product_id, quantity, price_per_unit) 
                          VALUES (?, ?, ?, ?)''', (order_id, item[0], item[3], item[4]))
    
    # subtract the sold quantity from the products table
    cursor.execute("UPDATE products SET quantity = quantity - ? WHERE product_id = ?", (item[3], item[1]))

    # check if the quantity available is zero, and if so, delete the row
    cursor.execute("SELECT quantity FROM products WHERE product_id = ?", (item[1],))
    row = cursor.fetchone()
    if row[0] == 0:
        cursor.execute("DELETE FROM products WHERE product_id = ?", (item[1],))

    # delete items from cart table
    cursor.execute("DELETE FROM cart WHERE email = ?", (user_email,))
    
    conn.commit()
    conn.close()

    return 'Order submitted successfully!'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Fetch values from the form
        phone_number = request.form.get('username')
        password = request.form.get('password')
        
        # Connect to database and verify login details
        conn = sqlite3.connect('organic_farming.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE email='{phone_number}' AND password='{password}'")
        user = cursor.fetchone()
        
        if user:
            session["email"] = phone_number
            # Redirect to the user's dashboard based on their role:
            if user[5] == 'farmer':
                return redirect('/farmer-login')
            elif user[5] == 'Transporter':
                return redirect('/transporter-login')
            else:
                return redirect('/products')
        else:
            return "Invalid login details"
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def show_signup():
    # Render "signup.html" page
    return render_template('signup.html')

@app.route('/success', methods=['POST'])
def signup():
    # Get form data from request object
    username = request.form['username']
    email = request.form['Phone']
    state = request.form['state']
    password = request.form['password']
    confirm_password = request.form["confirm_password"]
    role = request.form['role']

    # Compare the password and confirm_password fields
    if password == confirm_password:
        # Connect to SQLite database
        conn = sqlite3.connect("organic_farming.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT,
                    state TEXT, password TEXT, role TEXT)''')
        c.execute("INSERT INTO users (username, email, state, password, role) VALUES (?, ?, ?, ?, ?)", 
                (username, email, state, password, role))
        conn.commit()
        conn.close()

        # Render "success.html" page with the username parameter
        return redirect('/login')
    else:
        # Render "signup.html" page with an error message if password and confirm_password did not match
        return render_template("signup.html", error="Passwords did not match")

@app.route('/farmer_dashboard')
def farmer_dashboard():
    return render_template('farmer_dashboard.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    product_type = request.form.get('product_type')
    product = request.form.get('product')
    quantity = request.form.get('quantity')
    grade = request.form.get('grade')
    unitprice = request.form.get('unitprice')
    # Retrieve user_id from organic_farming.db
    conn1 = sqlite3.connect("organic_farming.db")
    cur1 = conn1.cursor()
    user_id = cur1.execute("SELECT id FROM users WHERE email=?", (session.get('email'),)).fetchone()[0]
    conn1.close()
    # INSERT the entered data into organic_farming.db
    conn2 = sqlite3.connect("organic_farming.db")
    cur2 = conn2.cursor()
    cur2.execute('''CREATE TABLE IF NOT EXISTS products
                    (product_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, product_type TEXT, product_name TEXT,
                    quantity INT, grade INT, unitprice INT)''')
    cur2.execute("INSERT INTO products (user_id, product_type, product_name, quantity, grade, unitprice) VALUES (?, ?, ?, ?, ?, ?)", (user_id, product_type, product, quantity, grade, unitprice))
    conn2.commit()
    conn2.close()
    return 'Product added successfully'

# Create a new Flask route that will render the HTML template for the modal
@app.route('/products')
def products():
    conn = sqlite3.connect('organic_farming.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products')
    products = c.fetchall()
    fruits = [i for i in products if i[2] == 'Fruits']
    vegetables = [i for i in products if i[2] == 'Vegetables']
    dairy = [i for i in products if i[2] == 'Diary']
    conn.close()

    return render_template('products.html', fruits=fruits, vegetables=vegetables, dairy=dairy)

@app.route('/home')
def home():
    return render_template('Home.html')

if __name__ == '__main__':
    app.run(debug=True)
