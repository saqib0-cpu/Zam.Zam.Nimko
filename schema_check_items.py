import pyodbc
import json

def test():
    try:
        config = json.load(open('config.json'))
        active = config.get('active', 'local')
        db = config.get(active)
        
        conn_str = f"DRIVER={db['driver']};SERVER={db['server']};DATABASE={db['database']};Trusted_Connection=yes;"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        print("\nTable: InvoiceItems")
        cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'InvoiceItems'")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
