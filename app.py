from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import pymysql
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database configuration
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='2005',
    database='inventory_management_new'
)
# Routes
@app.route('/')
def home():
    domains = [
        {'name': 'Edge AI', 'description': 'Advanced AI edge computing devices.'},
        {'name': 'Autonomous Drone', 'description': 'High-performance drones with autonomous capabilities.'},
        {'name': '8-bit', 'description': 'Classic 8-bit computing devices and accessories.'},
        {'name': 'Autonomous Racing Car', 'description': 'Self-driving racing cars with advanced sensors.'},
        {'name': 'General', 'description': 'General electronic components and devices.'}
    ]
    return render_template('home.html', domains=domains)

@app.route('/products/<domain_name>')
def product_list(domain_name):
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT id FROM domains WHERE name = %s", (domain_name,))
        domain = cursor.fetchone()
        if domain:
            cursor.execute("SELECT * FROM products WHERE domain_id = %s", (domain['id'],))
            products = cursor.fetchall()
            for product in products:
                cursor.execute("SELECT username FROM purchase_history WHERE product_id = %s ORDER BY purchased_date DESC LIMIT 5", (product['id'],))
                recent_purchases = cursor.fetchall()
                product['recent_purchases'] = recent_purchases
        else:
            products = []
    return render_template('product_list.html', domain_name=domain_name, products=products)

@app.route('/search')
def search():
    query = request.args.get('q')
    if query:
        # Implement search logic here, e.g., querying products by name or description
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM products WHERE name LIKE %s OR description LIKE %s", ('%' + query + '%', '%' + query + '%'))
            products = cursor.fetchall()
        return render_template('search_results.html', products=products, query=query)
    else:
        flash('Please enter a search query.', 'warning')
        return redirect(url_for('home'))

@app.route('/purchase/<int:product_id>', methods=['GET', 'POST'])
def purchase(product_id):
    if request.method == 'POST':
        username = request.form['username']
        rollno = request.form['rollno']
        purchased_date = request.form['purchased_date']
        return_date = request.form['return_date']
        contact_no = request.form['contact_no']

        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO purchase_history (product_id, username, rollno, purchased_date, return_date, contact_no) VALUES (%s, %s, %s, %s, %s, %s)",
                           (product_id, username, rollno, purchased_date, return_date, contact_no))
            cursor.execute("UPDATE products SET count = count - 1 WHERE id = %s AND count > 0", (product_id,))
            connection.commit()

        flash('Product purchased successfully!', 'success')
        return redirect(url_for('purchase_history'))

    return render_template('purchase.html', product_id=product_id, domain_name=request.args.get('domain_name'))

# Purchase History route
@app.route('/purchase_history')
def purchase_history():
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT p.name as product_name, d.name as domain_name, h.username, h.rollno, h.purchased_date, h.return_date FROM purchase_history h JOIN products p ON h.product_id = p.id JOIN domains d ON p.domain_id = d.id")
        history = cursor.fetchall()
    return render_template('purchase_history.html', history=history)

# Route to serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
