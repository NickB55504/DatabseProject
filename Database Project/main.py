import json
import urllib.parse
from flask import Flask, request, render_template, redirect, url_for, flash
from datetime import datetime
import mysql.connector
import secrets



app = Flask(__name__, template_folder='templates/')
app.secret_key = secrets.token_urlsafe(32)
# Configure MySQL connection (outside routes)
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Covids123!",
    "database": "medical_rental"
}
def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client_login')
def client_login():
    return render_template('client_login.html')

@app.route('/manager_login')
def manager_login():
    return render_template('manager_login.html')

@app.route('/client_dashboard', methods=['POST'])
def client_dashboard():
    client_id = request.form['client_id']
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipment")
        equipment = cursor.fetchall()
        cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
        client = cursor.fetchone()
        return render_template('client_dashboard.html', equipment=equipment, client=client)

@app.route('/manager_dashboard', methods=['POST'])
def manager_dashboard():
    manager_id = request.form['manager_id']
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipment")
        equipment = cursor.fetchall()

        return render_template('manager_dashboard.html', equipment=equipment, manager_id=manager_id)

@app.route('/update_inventory', methods=['GET', 'POST'])
def update_inventory():
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor()
        if request.method == 'POST':
            for key, value in request.form.items():
                if key.startswith('stock_'):
                    equipment_id = key.split('_')[1]
                    cursor.execute("SELECT quantity_in_store FROM equipment WHERE id = %s", (equipment_id,))
                    current_quantity = cursor.fetchone()[0]
                    new_quantity = current_quantity + int(value)  # Update based on new stock
                    cursor.execute("UPDATE equipment SET quantity_in_store = %s WHERE id = %s",
                                   (new_quantity, equipment_id))
            db.commit()
            return redirect(url_for('manager_dashboard'))
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipment")
        equipment = cursor.fetchall()
        return render_template('update_inventory.html', equipment=equipment)

@app.route('/equipment_update/<equipment_id>', methods=['GET', 'POST'])
def equipment_update(equipment_id):
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        if request.method == 'POST':
            # Update equipment logic here
            return redirect(url_for('manager_dashboard'))
        cursor.execute("SELECT * FROM equipment WHERE id = %s", (equipment_id,))
        equipment = cursor.fetchone()
        return render_template('equipment_update.html', equipment=equipment)





@app.route('/Order_Conformation')
def Order_Conformation():
    client = request.args.get('client')
    equipment = request.args.get('equipment')
    rental_date = request.args.get('rental_date')
    end_date = request.args.get('end_date')
    total_price = request.args.get('total_price')
    return render_template('Order_Conformation.html',
                           client=client,
                           equipment=equipment,
                           rental_date=rental_date,
                           end_date=end_date,
                           total_price=total_price)

@app.route('/customer_equipment_report', methods=['GET'])
def customer_equipment_report():
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT c.name AS customer_name, e.name AS equipment_name
        FROM clients c
        JOIN rentals r ON c.id = r.client_id
        JOIN equipment e ON r.equipment_id = e.id;
        """
        cursor.execute(query)
        customers = cursor.fetchall()
        return render_template('customer_equipment_report.html', customers=customers)

@app.route('/all_customers_report', methods=['GET'])
def all_customers_report():
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT c.id AS customer_id, c.name AS customer_name, 
               IFNULL(e.name, 'None') AS equipment_name
        FROM clients c
        LEFT JOIN rentals r ON c.id = r.client_id
        LEFT JOIN equipment e ON r.equipment_id = e.id
        ORDER BY c.id, e.name;
        """
        cursor.execute(query)
        customers = cursor.fetchall()
        return render_template('customer_equipment_report.html', customers=customers)
@app.route('/unpaid_customers_report', methods=['GET'])
def unpaid_customers_report():
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        query = """
        SELECT id, name, address, telephone
        FROM clients
        WHERE id IN (101, 102, 104, 107, 108);  # Example condition for unpaid customers
        """
        cursor.execute(query)
        unpaid_customers = cursor.fetchall()
        return render_template('unpaid_customers_report.html', unpaid_customers=unpaid_customers)


@app.route('/payments_report', methods=['GET'])
def payments_report():
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT c.id, c.name, SUM(r.total_price) AS grand_total "
                       "FROM clients c "
                       "JOIN rentals r ON c.id = r.client_id "
                       "GROUP BY c.id, c.name")
        clients_with_grand_total = cursor.fetchall()

        # Calculate the final total price
        final_total = sum(client['grand_total'] for client in clients_with_grand_total)

        return render_template('payments_report.html',
                               clients_with_grand_total=clients_with_grand_total,
                               final_total=final_total)

@app.route('/profit_report', methods=['GET'])
def profit_report():
    with mysql.connector.connect(**db_config) as db:  # Use context manager
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT SUM(r.total_price) AS overall_profit "
                       "FROM rentals r")
        overall_profit = cursor.fetchone()['overall_profit']

        return render_template('profit_report.html', overall_profit=overall_profit)

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


@app.route('/add_equipment', methods=['GET', 'POST'])
def add_equipment():
    if request.method == 'POST':
        equipment_id = request.form['id']
        description = request.form['description']
        quantity_to_add = int(request.form['quantity_to_add'])

        try:
            db = get_db_connection()
            if db is None:
                flash("Database connection error", "error")
                return redirect(url_for('add_equipment'))

            cursor = db.cursor()
            # Check if the equipment already exists
            cursor.execute("SELECT quantity_in_store FROM equipment WHERE id = %s", (equipment_id,))
            result = cursor.fetchone()

            if result:
                # Equipment exists, update the stock
                current_quantity = result[0]
                new_quantity = current_quantity + quantity_to_add
                cursor.execute("UPDATE equipment SET description = %s, quantity_in_store = %s WHERE id = %s",
                               (description, new_quantity, equipment_id))
            else:
                # Equipment does not exist, insert new record
                cursor.execute("INSERT INTO equipment (id, description, quantity_in_store) VALUES (%s, %s, %s)",
                               (equipment_id, description, quantity_to_add))
            db.commit()

            return redirect(url_for('manager_dashboard'))
        except Exception as e:
            # Handle potential errors during database operations
            print(f"Error adding equipment: {e}")
            flash("An error occurred while adding equipment. Please try again.", "error")
            return redirect(url_for('add_equipment'))
        finally:
            cursor.close()
            db.close()

    return render_template('add_equipment.html')




@app.route('/take_order', methods=['GET', 'POST'])
def take_order():
    if request.method == 'POST':
        try:
            customer_id = request.form['customer_id']
            equipment_id = request.form['equipment_id']
            rental_date = request.form['rental_date']
            end_date = request.form['end_date']

            # Convert rental_date and end_date to datetime objects
            rental_date_dt = datetime.strptime(rental_date, '%Y-%m-%d')
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

            db = get_db_connection()
            if db is None:
                flash("Database connection error", "error")
                return redirect(url_for('take_order'))

            cursor = db.cursor(dictionary=True)

            # Check if the equipment is available
            cursor.execute("""
                SELECT * FROM rentals
                WHERE equipment_id = %s AND 
                      ((start_date <= %s AND end_date >= %s) OR
                       (start_date <= %s AND end_date >= %s) OR
                       (start_date >= %s AND end_date <= %s))
            """, (equipment_id, rental_date, rental_date, end_date, end_date, rental_date, end_date))

            existing_rentals = cursor.fetchall()
            if existing_rentals:
                flash("Equipment is not available for the selected dates.", "error")
                db.close()
                return redirect(url_for('take_order'))

            # Calculate the total price based on rental duration
            cursor.execute("SELECT rent_price_per_day FROM equipment WHERE id = %s", (equipment_id,))
            equipment_price = cursor.fetchone()['rent_price_per_day']
            rental_duration = (end_date_dt - rental_date_dt).days
            total_price = equipment_price * rental_duration

            # Insert new rental into the rentals table
            cursor.execute("""
                INSERT INTO rentals (client_id, equipment_id, start_date, end_date, total_price)
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_id, equipment_id, rental_date, end_date, total_price))
            db.commit()

            # Fetch client and equipment information for the receipt
            cursor.execute("SELECT * FROM clients WHERE id = %s", (customer_id,))
            client_info = cursor.fetchone()

            cursor.execute("SELECT * FROM equipment WHERE id = %s", (equipment_id,))
            equipment_info = cursor.fetchone()

            db.close()

            # Redirect to order confirmation page with data
            return redirect(url_for('order_conformation',
                                    client=json.dumps(client_info),
                                    equipment=json.dumps(equipment_info),
                                    rental_date=rental_date,
                                    total_price=total_price))
        except KeyError as e:
            print(f"Missing form key: {e}")
            flash("An error occurred while processing your order. Please ensure all fields are filled in correctly.", "error")
            return redirect(url_for('take_order'))
        except Exception as e:
            print(f"An error occurred: {e}")
            flash("An error occurred while processing your order. Please try again.", "error")
            return redirect(url_for('take_order'))

    # Fetch equipment list to display in the form
    db = get_db_connection()
    if db is None:
        return "Database connection error"
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM equipment")
    equipment = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('take_order.html', equipment=equipment)
@app.route('/order_confirmation')
def order_confirmation():
    client_json = request.args.get('client')
    equipment_json = request.args.get('equipment')
    rental_date = request.args.get('rental_date')
    total_price = request.args.get('total_price')

    company_info = {
        'name': 'Stone Medical Equipment Rental Co.',
        'address': '123 Health St, Wellsville, USA',
        'contact': '555-1234'
    }

    # Decode the JSON strings
    client = json.loads(urllib.parse.unquote(client_json))
    equipment = json.loads(urllib.parse.unquote(equipment_json))

    return render_template('order_conformation.html', client=client, equipment=equipment,
                           rental_date=rental_date, total_price=total_price, company_info=company_info)

if __name__ == '__main__':
    app.run(debug=True)