import sqlite3
import os
from tabulate import tabulate

# ---------- Paths ----------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

PROD_DB = os.path.join(DATA_DIR, "prod.db")
STAGING_DB = os.path.join(DATA_DIR, "staging.db")


# ---------- Connect to databases ----------
def connect(db_path):
    return sqlite3.connect(db_path)


# ---------- Get all orders ----------
def get_all_orders(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    return {row[0]: row for row in rows}  # Dictionary with order_id as key


# ---------- Compare databases ----------
def compare_databases():
    prod_conn = connect(PROD_DB)
    staging_conn = connect(STAGING_DB)
    
    prod_orders = get_all_orders(prod_conn)
    staging_orders = get_all_orders(staging_conn)
    
    prod_conn.close()
    staging_conn.close()
    
    # Find missing rows
    missing_rows = []
    for order_id in prod_orders:
        if order_id not in staging_orders:
            missing_rows.append(prod_orders[order_id])
    
    # Find modified rows
    modified_rows = []
    for order_id in prod_orders:
        if order_id in staging_orders:
            prod_row = prod_orders[order_id]
            staging_row = staging_orders[order_id]
            
            # Compare all fields except order_id
            if prod_row[1:] != staging_row[1:]:
                modified_rows.append({
                    'order_id': order_id,
                    'prod_data': prod_row,
                    'staging_data': staging_row
                })
    
    return {
        'prod_total': len(prod_orders),
        'staging_total': len(staging_orders),
        'missing_rows': missing_rows,
        'modified_rows': modified_rows
    }


# ---------- Generate report ----------
def generate_report():
    results = compare_databases()
    
    print("=" * 80)
    print("DATA QUALITY REPORT: Production vs Staging Database")
    print("=" * 80)
    print()
    
    # Summary statistics
    print("📊 SUMMARY STATISTICS")
    print("-" * 80)
    print(f"Production DB - Total Records: {results['prod_total']}")
    print(f"Staging DB - Total Records: {results['staging_total']}")
    print(f"Data Loss: {len(results['missing_rows'])} records ({len(results['missing_rows']) / results['prod_total'] * 100:.1f}%)")
    print(f"Modified Records: {len(results['modified_rows'])} records ({len(results['modified_rows']) / results['prod_total'] * 100:.1f}%)")
    print()
    
    # Missing rows
    print("❌ MISSING ROWS (in Production but not in Staging)")
    print("-" * 80)
    if results['missing_rows']:
        table_data = []
        for row in results['missing_rows']:
            table_data.append([row[0], row[1], row[2], row[3], row[4]])
        print(tabulate(table_data, headers=['Order ID', 'Customer', 'Amount', 'Country', 'Date'], tablefmt='grid'))
        print(f"Total Missing: {len(results['missing_rows'])}")
    else:
        print("✅ No missing rows")
    print()
    
    # Modified rows
    print("⚠️  MODIFIED ROWS (data differences between Production and Staging)")
    print("-" * 80)
    if results['modified_rows']:
        for item in results['modified_rows']:
            order_id = item['order_id']
            prod = item['prod_data']
            staging = item['staging_data']
            
            print(f"Order ID: {order_id}")
            print(f"  Production:  {prod[1]} | ${prod[2]} | {prod[3]} | {prod[4]}")
            print(f"  Staging:     {staging[1]} | ${staging[2]} | {staging[3]} | {staging[4]}")
            
            # Highlight which fields changed
            changes = []
            if prod[1] != staging[1]:
                changes.append(f"Customer: '{prod[1]}' → '{staging[1]}'")
            if prod[2] != staging[2]:
                changes.append(f"Amount: ${prod[2]} → ${staging[2]}")
            if prod[3] != staging[3]:
                changes.append(f"Country: '{prod[3]}' → '{staging[3]}'")
            if prod[4] != staging[4]:
                changes.append(f"Date: '{prod[4]}' → '{staging[4]}'")
            
            if changes:
                print(f"  Changes: {', '.join(changes)}")
            print()
        print(f"Total Modified: {len(results['modified_rows'])}")
    else:
        print("✅ No modified rows")
    print()
    
    # Data Quality Score
    print("📈 DATA QUALITY SCORE")
    print("-" * 80)
    quality_score = ((results['prod_total'] - len(results['missing_rows']) - len(results['modified_rows'])) / results['prod_total']) * 100
    print(f"Quality Score: {quality_score:.1f}%")
    print()
    
    print("=" * 80)


if __name__ == "__main__":
    generate_report()
