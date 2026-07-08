from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pyodbc
import datetime
import json
import os

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "active": "local",
            "local": {
                "server": "Saqib-pc\\SQLEXPRESS",
                "database": "junimkoDB",
                "driver": "{ODBC Driver 17 for SQL Server}",
                "authentication": "windows"
            },
            "remote": {
                "server": "",
                "database": "junimkoDB",
                "driver": "{ODBC Driver 17 for SQL Server}",
                "authentication": "sql",
                "username": "",
                "password": ""
            }
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_db_connection():
    config = load_config()
    active = str(config.get('active', 'local'))
    db_data = config.get(active)
    
    # Ensure db_settings is a dictionary
    if not isinstance(db_data, dict):
        db_settings = config.get('local')
        if not isinstance(db_settings, dict):
            # Absolute fallback for extreme cases
            db_settings = {
                "server": "Saqib-pc\\SQLEXPRESS",
                "database": "junimkoDB",
                "driver": "{ODBC Driver 17 for SQL Server}",
                "authentication": "windows"
            }
    else:
        db_settings = db_data
    
    try:
        auth_mode = str(db_settings.get('authentication', 'windows'))
        server = str(db_settings.get('server', ''))
        database = str(db_settings.get('database', 'junimkoDB'))
        driver = str(db_settings.get('driver', '{ODBC Driver 17 for SQL Server}'))
        
        if auth_mode == 'windows':
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
            )
        else:
            uid = str(db_settings.get('username', ''))
            pwd = str(db_settings.get('password', ''))
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={uid};"
                f"PWD={pwd};"
            )
        return pyodbc.connect(conn_str, timeout=5)
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {str(e)}")
        # Re-raise with a cleaner message for the API
        raise Exception(f"Failed to connect to {active} database at {db_settings.get('server')}. Error: {str(e)}")

@app.route('/api/diagnose', methods=['GET'])
def diagnose_connection():
    config = load_config()
    results = {
        "active_env": config.get('active'),
        "server_time": datetime.datetime.now().isoformat(),
        "client_ip": request.remote_addr,
        "database_status": "Starting test..."
    }
    try:
        conn = get_db_connection()
        conn.close()
        results["database_status"] = "Connected Successfully"
    except Exception as e:
        results["database_status"] = "Failed"
        results["error_detail"] = str(e)
    return jsonify(results)

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(load_config())

@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        data = request.json
        save_config(data)
        return jsonify({"message": "Settings updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products")
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/near-expiry', methods=['GET'])
def get_near_expiry():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 5 Name, ExpiryDate, DATEDIFF(day, GETDATE(), ExpiryDate) as DaysRemaining
            FROM Products 
            WHERE ExpiryDate <= DATEADD(month, 3, GETDATE())
            ORDER BY ExpiryDate ASC
        """)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (Name, Category, Packs, UnitsPerPack, PurchasePrice, SellingPrice, ExpiryDate, Supplier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('category'),
            data.get('packs'),
            data.get('unitsPerPack', 24),
            data.get('purchasePrice'),
            data.get('sellingPrice'),
            data.get('expiryDate'),
            data.get('supplier')
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Product saved successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE ProductID = ?", (product_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Product deleted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Insert Invoice
        cursor.execute("""
            INSERT INTO Invoices (InvoiceNumber, CustomerName, CustomerPhone, Subtotal, Tax, Discount, Total, PaidAmount, Balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('invoiceNumber'),
            data.get('customerName'),
            data.get('customerPhone'),
            data.get('subtotal'),
            data.get('tax'),
            data.get('discount'),
            data.get('total'),
            data.get('paidAmount', 0),
            data.get('balance', 0)
        ))
        
        # Get the ID of the inserted invoice
        cursor.execute("SELECT SCOPE_IDENTITY()")
        invoice_id = cursor.fetchone()[0]

        # 1b. If balance > 0, create a record in Dues
        balance = data.get('balance', 0)
        if balance > 0:
            from datetime import datetime, timedelta
            due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO Dues (InvoiceID, CustomerName, PhoneNumber, AmountDue, DueDate, Status)
                VALUES (?, ?, ?, ?, ?, 'Pending')
            """, (
                invoice_id,
                data.get('customerName'),
                data.get('customerPhone'),
                balance,
                due_date
            ))
        
        # 2. Insert Invoice Items
        for item in data.get('items', []):
            cursor.execute("""
                INSERT INTO InvoiceItems (InvoiceID, ProductID, Quantity, UnitPrice, TotalPrice)
                VALUES (?, ?, ?, ?, ?)
            """, (
                invoice_id,
                item.get('productId'),
                item.get('quantity'),
                item.get('unitPrice'),
                item.get('totalPrice')
            ))
            
            # 3. Update Inventory (Subtract from Products table)
            # Use Decimal division to avoid losing partial packs
            cursor.execute("""
                UPDATE Products SET Packs = Packs - ( CAST(? AS DECIMAL(18,2)) / CAST(UnitsPerPack AS DECIMAL(18,2)) )
                WHERE ProductID = ?
            """, (item.get('quantity'), item.get('productId')))

        conn.commit()
        conn.close()
        return jsonify({"message": "Invoice created successfully!", "invoice_id": invoice_id}), 201
    except Exception as e:
        print("!!! INVOICE SAVE ERROR !!!")
        print(f"Error Message: {str(e)}")
        print(f"Received Data: {request.json}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch last 10 invoices
        cursor.execute("SELECT TOP 10 * FROM Invoices ORDER BY Date DESC")
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/loans', methods=['POST'])
def add_loan():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Loans (PersonName, MobileNumber, LoanAmount, InterestRate, LoanDate, DueDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('personName'),
            data.get('mobileNumber'),
            data.get('loanAmount'),
            data.get('interestRate'),
            data.get('loanDate'),
            data.get('dueDate')
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Loan record saved!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/loans', methods=['GET'])
def get_loans():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Loans")
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales/flow', methods=['GET'])
def get_sales_flow():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    customer = request.args.get('customer')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Recent Flow Records with optional filters
        query = """
            SELECT TOP 100 i.Date, i.CustomerName, p.Name, ii.Quantity, ii.TotalPrice, 'Paid' as Status
            FROM Invoices i
            JOIN InvoiceItems ii ON i.InvoiceID = ii.InvoiceID
            JOIN Products p ON ii.ProductID = p.ProductID
            WHERE 1=1
        """
        params = []
        if date_from:
            query += " AND CAST(i.Date AS DATE) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND CAST(i.Date AS DATE) <= ?"
            params.append(date_to)
        if customer:
            query += " AND i.CustomerName LIKE ?"
            params.append(f"%{customer}%")
            
        query += " ORDER BY i.Date DESC"
        
        cursor.execute(query, params)
        columns = ['date', 'customer', 'product', 'quantity', 'amount', 'status']
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Flow Stats (Total across these filtered records)
        # We'll use a subquery to get stats for the filtered invoices
        stats_query = """
            SELECT ISNULL(SUM(Total), 0), COUNT(DISTINCT CustomerName), COUNT(*) 
            FROM Invoices i
            WHERE 1=1
        """
        stats_params = []
        if date_from:
            stats_query += " AND CAST(Date AS DATE) >= ?"
            stats_params.append(date_from)
        if date_to:
            stats_query += " AND CAST(Date AS DATE) <= ?"
            stats_params.append(date_to)
        if customer:
            stats_query += " AND CustomerName LIKE ?"
            stats_params.append(f"%{customer}%")
            
        cursor.execute(stats_query, stats_params)
        row_total = cursor.fetchone()
        
        # Additional context-aware stats
        cursor.execute("SELECT COUNT(*) FROM Invoices WHERE CAST(Date AS DATE) = CAST(GETDATE() AS DATE)")
        today_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT ISNULL(SUM(Quantity), 0) FROM InvoiceItems ii JOIN Invoices i ON ii.InvoiceID = i.InvoiceID WHERE 1=1 " + 
                      (" AND CAST(i.Date AS DATE) >= ?" if date_from else "") + 
                      (" AND CAST(i.Date AS DATE) <= ?" if date_to else "") + 
                      (" AND i.CustomerName LIKE ?" if customer else ""), stats_params)
        total_products_sold = cursor.fetchone()[0]
        
        stats = {
            "totalSales": float(row_total[0]),
            "activeCustomers": row_total[1],
            "invoicesToday": today_count,
            "productsSold": float(total_products_sold),
            "records": records
        }
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/customer-sales', methods=['GET'])
def get_customer_sales_stats():
    """Return top 10 customers by total sales for charting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 10 CustomerName, SUM(Total) as TotalSales, COUNT(*) as OrderCount
            FROM Invoices
            WHERE CustomerName IS NOT NULL AND CustomerName != ''
            GROUP BY CustomerName
            ORDER BY TotalSales DESC
        """)
        results = []
        for row in cursor.fetchall():
            results.append({
                'name': row[0],
                'totalSales': float(row[1]),
                'orderCount': row[2]
            })
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dues', methods=['GET'])
def get_dues():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Dues ORDER BY DateCreated DESC")
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Return distinct customers from Invoices for autocomplete."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT CustomerName, CustomerPhone
            FROM Invoices
            WHERE CustomerName IS NOT NULL AND CustomerName != ''
            ORDER BY CustomerName
        """)
        results = [{'CustomerName': row[0], 'CustomerPhone': row[1] or ''} for row in cursor.fetchall()]
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Today's Stats
        cursor.execute("SELECT ISNULL(SUM(Total), 0) FROM Invoices WHERE CAST(Date AS DATE) = CAST(GETDATE() AS DATE)")
        sales_today = float(cursor.fetchone()[0])
        
        cursor.execute("SELECT COUNT(*) FROM Invoices WHERE CAST(Date AS DATE) = CAST(GETDATE() AS DATE)")
        invoices_today = cursor.fetchone()[0]
        
        # 2. Monthly & Yearly Sales
        cursor.execute("SELECT ISNULL(SUM(Total), 0) FROM Invoices WHERE MONTH(Date) = MONTH(GETDATE()) AND YEAR(Date) = YEAR(GETDATE())")
        sales_monthly = float(cursor.fetchone()[0])
        
        cursor.execute("SELECT ISNULL(SUM(Total), 0) FROM Invoices WHERE YEAR(Date) = YEAR(GETDATE())")
        sales_yearly = float(cursor.fetchone()[0])
        
        cursor.execute("SELECT ISNULL(SUM(Total), 0) FROM Invoices")
        sales_total = float(cursor.fetchone()[0])

        # 3. Dues Stats
        cursor.execute("SELECT ISNULL(SUM(AmountDue), 0) FROM Dues WHERE Status = 'Pending'")
        total_dues = float(cursor.fetchone()[0])

        cursor.execute("SELECT ISNULL(SUM(AmountDue), 0) FROM Dues WHERE Status = 'Pending' AND CAST(DateCreated AS DATE) = CAST(GETDATE() AS DATE)")
        dues_today = float(cursor.fetchone()[0])

        # 4. Products Stats
        cursor.execute("SELECT COUNT(*) FROM Products")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Products WHERE ExpiryDate <= DATEADD(month, 3, GETDATE())")
        near_expiry = cursor.fetchone()[0]
        
        # 5. Average Daily Sales (last 30 days)
        cursor.execute("SELECT ISNULL(AVG(DailyTotal), 0) FROM (SELECT SUM(Total) as DailyTotal FROM Invoices WHERE Date >= DATEADD(day, -30, GETDATE()) GROUP BY CAST(Date AS DATE)) as DailySales")
        avg_daily = float(cursor.fetchone()[0])

        conn.close()
        return jsonify({
            "salesToday": sales_today,
            "invoicesToday": invoices_today,
            "salesMonthly": sales_monthly,
            "salesYearly": sales_yearly,
            "salesTotal": sales_total,
            "totalProducts": total_products,
            "totalDues": total_dues,
            "duesToday": dues_today,
            "nearExpiry": near_expiry,
            "avgDaily": avg_daily
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats/daily-trend', methods=['GET'])
def get_daily_trend():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch last 30 days of sales
        cursor.execute("""
            SELECT CAST(Date AS DATE) as SaleDate, ISNULL(SUM(Total), 0) as DailyTotal
            FROM Invoices
            WHERE Date >= DATEADD(day, -30, GETDATE())
            GROUP BY CAST(Date AS DATE)
            ORDER BY SaleDate ASC
        """)
        labels = []
        data = []
        for row in cursor.fetchall():
            labels.append(row[0].strftime('%d %b'))
            data.append(float(row[1]))
        
        conn.close()
        return jsonify({"labels": labels, "data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dues/<int:due_id>/clear', methods=['POST'])
def clear_due(due_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Dues SET Status = 'Paid' WHERE DueID = ?", (due_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Due marked as Paid!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/daily', methods=['GET'])
def get_daily_report():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT Date, InvoiceNumber, CustomerName, Total FROM Invoices WHERE 1=1"
        params = []
        if date_from:
            query += " AND CAST(Date AS DATE) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND CAST(Date AS DATE) <= ?"
            params.append(date_to)
        query += " ORDER BY Date DESC"
        
        cursor.execute(query, params)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reports/summary', methods=['GET'])
def get_report_summary():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Total Revenue, Total Profit (Revenue - Cost), Total Count
        # Profit calculation assumes we have a 'PurchasePrice' in Products.
        # Let's simplify and just do revenue for now since we don't have cost in InvoiceItems yet.
        cursor.execute("SELECT SUM(Total) as TotalRevenue, COUNT(*) as TotalInvoices FROM Invoices")
        row = cursor.fetchone()
        summary = {
            "totalRevenue": float(row[0] or 0),
            "totalInvoices": row[1] or 0,
            "totalProfit": float(row[0] or 0) * 0.4  # ESTIMATE: 40% margin until we have real cost data
        }
        conn.close()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/loans/<int:loan_id>/payments', methods=['POST'])
def add_loan_payment(loan_id):
    data = request.json
    payment_amount = data.get('paymentAmount')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Record payment
        cursor.execute("""
            INSERT INTO LoanPayments (LoanID, PaymentAmount, PaymentDate, PaymentMethod)
            VALUES (?, ?, GETDATE(), ?)
        """, (loan_id, payment_amount, data.get('paymentMethod', 'Cash')))
        
        # 2. Update Loan total paid
        cursor.execute("""
            UPDATE Loans 
            SET PaidAmount = PaidAmount + ?
            WHERE LoanID = ?
        """, (payment_amount, loan_id))
        
        # 3. Check if fully paid
        cursor.execute("SELECT LoanAmount, PaidAmount FROM Loans WHERE LoanID = ?", (loan_id,))
        loan = cursor.fetchone()
        if loan and loan[1] >= loan[0]:
            cursor.execute("UPDATE Loans SET Status = 'Paid' WHERE LoanID = ?", (loan_id,))
            
        conn.commit()
        conn.close()
        return jsonify({"message": "Payment recorded successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Print a clear message to console (if visible)
    print("--- ZAM ZAM NIMKO SERVER STARTED ---")
    print("Local Access: http://localhost:5000")
    print("Network Access: http://192.168.0.104:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
