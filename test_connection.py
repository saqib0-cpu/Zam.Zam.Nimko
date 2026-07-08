import pyodbc

def test_connection():
    print("Searching for SQL Server Drivers...")
    drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
    print(f"Found Drivers: {drivers}")
    
    if not drivers:
        print("ERROR: No SQL Server drivers found. Please install the ODBC Driver for SQL Server.")
        return

    # Try common local instance names
    instances = ['localhost', '(local)', 'localhost\\SQLEXPRESS', '.\\SQLEXPRESS']
    
    for instance in instances:
        print(f"\nTrying to connect to: {instance}...")
        conn_str = (
            f"DRIVER={{{drivers[0]}}};"
            f"SERVER={instance};"
            f"DATABASE=master;" # Connect to master first
            f"Trusted_Connection=yes;"
        )
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            print(f"SUCCESS! Connected to {instance}")
            
            cursor = conn.cursor()
            cursor.execute("SELECT @@SERVERNAME")
            server_name = cursor.fetchone()[0]
            print(f"Your Server Name is: {server_name}")
            
            conn.close()
            return server_name
        except Exception as e:
            print(f"Failed to connect to {instance}: {str(e)}")

    print("\nCOULD NOT CONNECT AUTOMATICALLY.")
    print("Please find your SQL Server name in 'SQL Server Management Studio' (SSMS).")

if __name__ == "__main__":
    test_connection()
