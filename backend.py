from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'KNFoods'  # Change this to a strong, random secret key

# Function to connect to the MySQL database
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',  # Your MySQL server host, typically 'localhost'
        user='root',  # Your MySQL username
        password='Rupa@31',  # Your MySQL password
        database='knfoods',  # Name of the database you're connecting to
    )
    return connection

@app.route('/')
def home():
    return 'Welcome to KNFOODS'

# Route to display users from the MySQL database
@app.route('/users')
def show_users():
    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cursor:  # Using dictionary cursor
        cursor.execute('SELECT * FROM users')  # Query the users table
        users = cursor.fetchall()  # Fetch all users as a list of dictionaries
    conn.close()
    return render_template('users.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['login-username']
        password = request.form['login-password']

        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Check if the user exists in the database
            cursor.execute('SELECT * FROM users WHERE name = %s', (username,))
            user_record = cursor.fetchone()  # Fetch the first matching user
        conn.close()

        if user_record:  # Assuming you would check the password here
            # Login successful, store username in session for future use
            session['username'] = username  
            if username == "manager":
                return redirect(url_for('manager_home'))  # Redirect to manager home
            elif username == "owner":
                return redirect(url_for('owner_home'))
            else:
                return redirect(url_for('employee_home', username=username))  # Redirect to employee home
        else:
            flash('Invalid username or password.')  # Flash an error message
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/get_employees', methods=['GET'])
def get_employees():
    query = request.args.get('query')
    
    # Fetch both in-progress and completed records from the database
    cursor.execute("SELECT name, status FROM employees WHERE name LIKE %s", (f'%{query}%',))
    results = cursor.fetchall()
    
    # Format the data to return both statuses
    data = []
    for row in results:
        employee_name = row[0]
        status = row[1]  # status could be 'in-progress' or 'completed'
        data.append({'name': employee_name, 'status': status})
    
    return jsonify(data)

@app.route('/products/<status>')
def get_products(status):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query for products based on status: 0 for 'In Progress', 1 for 'Completed'
    if status == 'inprogress':
        query = "SELECT product_id, productname, product_weight, employeename FROM productstatus WHERE status = 0 ORDER BY timestamp DESC"
    elif status == 'completed':
        query = "SELECT product_id, productname, product_weight, employeename FROM productstatus WHERE status = 1 ORDER BY timestamp DESC"
    else:
        return jsonify([])

    cursor.execute(query)
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    # Return product data as JSON
    return jsonify(products)

@app.route('/search_suggestions')
def search_suggestions():
    query = request.args.get('query', '').strip()  # Remove any leading/trailing whitespace
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Limit the number of suggestions (e.g., top 10)
    limit = 10

    # Search for matching product names and employee names (assuming 'productname' and 'employeename' fields in the DB)
    search_query = f"""
        SELECT DISTINCT productname, employeename FROM productstatus
        WHERE productname LIKE %s OR employeename LIKE %s
        LIMIT {limit}
    """
    
    cursor.execute(search_query, (f"%{query}%", f"%{query}%"))
    suggestions = cursor.fetchall()

    cursor.close()
    conn.close()

    # Format suggestions for easier handling on the front end
    formatted_suggestions = [
        {
            "label": f"{suggestion['productname']} - {suggestion['employeename']}",
            "value": suggestion['productname']
        }
        for suggestion in suggestions
    ]

    # Return search suggestions as JSON
    return jsonify(formatted_suggestions)

def get_products_by_status(status, employee_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # This is a placeholder for your actual database query logic
    query = """
    SELECT product_id, productname, product_weight, employeename, status 
    FROM productstatus 
    WHERE status = %s AND employeename = %s
    """
    cursor.execute(query, (status, employee_name))
    return cursor.fetchall() 

@app.route('/update_product_status/<int:product_id>/<int:new_status>', methods=['POST'])
def update_product_status(product_id, new_status):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Update product status
        cursor.execute("""
            UPDATE productstatus
            SET status = %s
            WHERE product_id = %s
        """, (new_status, product_id))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def get_in_progress_products(employeename):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT product_id, productname, product_weight, employeename FROM productstatus WHERE status = %s AND employeename = %s", (0, employeename))
    products = cursor.fetchall()
    print("In Progress Products:", products)  # Debugging print
    conn.close()
    return products

def get_recent_completed_products(employeename):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    three_months_ago = datetime.now() - timedelta(days=90)
    
    cursor.execute("SELECT product_id, productname, product_weight, employeename FROM productstatus WHERE status = %s AND employeename = %s AND timestamp >= %s", (1, employeename, three_months_ago))
    products = cursor.fetchall()
    print("Recent Completed Products:", products)  # Debugging print
    conn.close()
    return products

@app.route('/manager-home')
def manager_home():
    return render_template('manager-home.html')  # Render manager home template

@app.route('/owner-home')
def owner_home():
    return render_template('owner-home.html')  # Render owner home template


@app.route('/employee_home')
def employee_home():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    employeename = session['username']  # Assuming the username is stored in the session

    in_progress_products = get_in_progress_products(employeename)
    recent_completed_products = get_recent_completed_products(employeename)

    return render_template('employee-home.html', in_progress_products=in_progress_products, recent_completed_products=recent_completed_products)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            product_name = request.form['product_name']
            employeename = request.form['employeename']
            product_weight = request.form['product_weight']
            status = 0  # Fixed status value for all products
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Insert the product into the productstatus table with a status of 0
                cursor.execute(
                    'INSERT INTO productstatus (employeename, status, product_weight, productname) VALUES (%s, %s, %s, %s)',
                    (employeename, status, product_weight, product_name)
                )
                conn.commit()  # Commit the transaction
            conn.close()

            # Return a JSON response indicating success for the AJAX call
            return jsonify({'status': 'success'})
        except Exception as e:
            # Handle any errors that may occur
            print(f"Error: {e}")
            return jsonify({'status': 'error', 'message': str(e)})
    return render_template('add_product')


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']  # Get the username from the form
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Insert the user into the users table
            cursor.execute("INSERT INTO users (name) VALUES (%s)", (username,))
            conn.commit()  # Commit the transaction
        conn.close()

        flash('User added successfully.', 'success')
    return render_template('add_user')



@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from session
    flash('You have been logged out.')  # Flash a logout message
    return redirect(url_for('login'))  # Redirect to login page


if __name__ == '__main__':
    app.run(debug=True)
