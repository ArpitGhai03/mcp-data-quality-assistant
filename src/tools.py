"""
MCP-style tools for database comparison and data quality analysis.
These tools are designed to be called by AI systems and provide structured data output.
"""

import os
import psycopg2
from decimal import Decimal
from datetime import date
from typing import Dict, List, Tuple, Any
from db_config import get_prod_config, get_staging_config

# Data directory for exports
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ---------- Helper Functions ----------
def _convert_to_serializable(obj):
    """Convert non-JSON-serializable objects to serializable types."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, date):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_serializable(item) for item in obj]
    return obj


# ---------- Database Connection ----------
def _connect_prod():
    """Internal function to connect to production database."""
    return psycopg2.connect(**get_prod_config())


def _connect_staging():
    """Internal function to connect to staging database."""
    return psycopg2.connect(**get_staging_config())


def _get_all_orders(conn) -> Dict[int, Tuple]:
    """Internal function to fetch all orders from database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    cursor.close()
    return {row[0]: row for row in rows}  # Dictionary with order_id as key


# ---------- Tool: get_missing_rows ----------
def get_missing_rows() -> Dict[str, Any]:
    """
    Get all rows that exist in Production DB but are missing in Staging DB.
    
    Returns:
        Dict with:
        - 'count': number of missing rows
        - 'percentage': percentage of data loss
        - 'rows': list of missing row dictionaries
    """
    prod_conn = _connect_prod()
    staging_conn = _connect_staging()
    
    prod_orders = _get_all_orders(prod_conn)
    staging_orders = _get_all_orders(staging_conn)
    
    prod_conn.close()
    staging_conn.close()
    
    missing_rows = []
    for order_id in prod_orders:
        if order_id not in staging_orders:
            row = prod_orders[order_id]
            missing_rows.append({
                'order_id': row[0],
                'customer_name': row[1],
                'amount': float(row[2]) if isinstance(row[2], Decimal) else row[2],
                'country': row[3],
                'created_at': str(row[4]) if row[4] else None
            })
    
    percentage = (len(missing_rows) / len(prod_orders)) * 100 if prod_orders else 0
    
    return _convert_to_serializable({
        'count': len(missing_rows),
        'percentage': round(percentage, 2),
        'total_prod_records': len(prod_orders),
        'rows': missing_rows
    })


# ---------- Tool: get_mismatched_rows ----------
def get_mismatched_rows() -> Dict[str, Any]:
    """
    Get all rows that exist in both databases but have different data.
    
    Returns:
        Dict with:
        - 'count': number of mismatched rows
        - 'percentage': percentage of data with differences
        - 'rows': list of mismatched row dictionaries with before/after comparison
    """
    prod_conn = _connect_prod()
    staging_conn = _connect_staging()
    
    prod_orders = _get_all_orders(prod_conn)
    staging_orders = _get_all_orders(staging_conn)
    
    prod_conn.close()
    staging_conn.close()
    
    mismatched_rows = []
    for order_id in prod_orders:
        if order_id in staging_orders:
            prod_row = prod_orders[order_id]
            staging_row = staging_orders[order_id]
            
            # Compare all fields except order_id
            if prod_row[1:] != staging_row[1:]:
                changes = {}
                
                if prod_row[1] != staging_row[1]:
                    changes['customer_name'] = {'prod': prod_row[1], 'staging': staging_row[1]}
                if prod_row[2] != staging_row[2]:
                    prod_amount = float(prod_row[2]) if isinstance(prod_row[2], Decimal) else prod_row[2]
                    staging_amount = float(staging_row[2]) if isinstance(staging_row[2], Decimal) else staging_row[2]
                    changes['amount'] = {'prod': prod_amount, 'staging': staging_amount}
                if prod_row[3] != staging_row[3]:
                    changes['country'] = {'prod': prod_row[3], 'staging': staging_row[3]}
                if prod_row[4] != staging_row[4]:
                    changes['created_at'] = {'prod': str(prod_row[4]), 'staging': str(staging_row[4])}
                
                mismatched_rows.append({
                    'order_id': order_id,
                    'changes': changes,
                    'production': {
                        'customer_name': prod_row[1],
                        'amount': float(prod_row[2]) if isinstance(prod_row[2], Decimal) else prod_row[2],
                        'country': prod_row[3],
                        'created_at': str(prod_row[4]) if prod_row[4] else None
                    },
                    'staging': {
                        'customer_name': staging_row[1],
                        'amount': float(staging_row[2]) if isinstance(staging_row[2], Decimal) else staging_row[2],
                        'country': staging_row[3],
                        'created_at': str(staging_row[4]) if staging_row[4] else None
                    }
                })
    
    percentage = (len(mismatched_rows) / len(prod_orders)) * 100 if prod_orders else 0
    
    return _convert_to_serializable({
        'count': len(mismatched_rows),
        'percentage': round(percentage, 2),
        'total_prod_records': len(prod_orders),
        'rows': mismatched_rows
    })


# ---------- Tool: get_quality_score ----------
def get_quality_score() -> Dict[str, Any]:
    """
    Calculate overall data quality score comparing Production and Staging databases.
    
    Returns:
        Dict with:
        - 'quality_score': percentage of records that match perfectly
        - 'prod_total': total records in production
        - 'staging_total': total records in staging
        - 'missing_count': number of missing records
        - 'mismatched_count': number of mismatched records
        - 'healthy_count': number of matching records
    """
    missing = get_missing_rows()
    mismatched = get_mismatched_rows()
    
    prod_total = missing['total_prod_records']
    
    missing_count = missing['count']
    mismatched_count = mismatched['count']
    healthy_count = prod_total - missing_count - mismatched_count
    
    quality_score = (healthy_count / prod_total * 100) if prod_total > 0 else 0
    
    return {
        'quality_score': round(quality_score, 2),
        'prod_total': prod_total,
        'staging_total': prod_total - missing_count,
        'missing_count': missing_count,
        'missing_percentage': missing['percentage'],
        'mismatched_count': mismatched_count,
        'mismatched_percentage': mismatched['percentage'],
        'healthy_count': healthy_count,
        'healthy_percentage': round((healthy_count / prod_total * 100), 2) if prod_total > 0 else 0
    }


# ---------- Tool: run_full_comparison ----------
def run_full_comparison() -> Dict[str, Any]:
    """
    Run a full comparison between Production and Staging databases.
    Combines all analysis in one call.
    
    Returns:
        Dict with complete comparison results including:
        - quality_metrics: overall quality statistics
        - missing_rows: rows that are missing in staging
        - mismatched_rows: rows with data differences
    """
    quality = get_quality_score()
    missing = get_missing_rows()
    mismatched = get_mismatched_rows()
    
    return _convert_to_serializable({
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'databases': {
            'production': get_prod_config()['database'],
            'staging': get_staging_config()['database']
        },
        'quality_metrics': quality,
        'missing_rows': missing,
        'mismatched_rows': mismatched,
        'summary': {
            'status': 'GOOD' if quality['quality_score'] >= 90 else 'WARNING' if quality['quality_score'] >= 80 else 'CRITICAL',
            'recommendation': _get_recommendation(quality, missing, mismatched)
        }
    })


# ---------- Helper: Get Recommendation ----------
def _get_recommendation(quality: Dict, missing: Dict, mismatched: Dict) -> str:
    """Generate recommendation based on comparison results."""
    if quality['quality_score'] >= 95:
        return "Data quality is excellent. Staging database is reliable for use."
    elif quality['quality_score'] >= 80:
        return f"Data quality is acceptable. {missing['count']} records are missing and {mismatched['count']} have differences. Review before deployment."
    elif quality['quality_score'] >= 70:
        return f"Data quality needs attention. {missing['count']} missing records ({missing['percentage']}%) and {mismatched['count']} mismatches. Investigate before production use."
    else:
        return f"Critical data quality issues. Only {quality['quality_score']:.1f}% match. Recommend full data reconciliation."


# ---------- Tool: Export Report to JSON ----------
def export_report(output_file: str = None) -> Dict[str, Any]:
    """
    Export full comparison report to JSON file.
    
    Args:
        output_file: Path to save the JSON report. If None, uses default location.
    
    Returns:
        Dict with report data and file path where it was saved.
    """
    import json
    
    if output_file is None:
        output_file = os.path.join(DATA_DIR, "comparison_report.json")
    
    report = run_full_comparison()
    
    with open(output_file, 'w') as f:
        json.dump(_convert_to_serializable(report), f, indent=2)
    
    return _convert_to_serializable({
        'status': 'success',
        'file_path': output_file,
        'report': report
    })


# ---------- Migration Tools ----------

def preview_migration(source_db: str, dest_db: str, migration_type: str) -> Dict[str, Any]:
    """
    Preview what will be migrated without actually migrating.
    
    Args:
        source_db: 'prod' or 'staging' - source database
        dest_db: 'prod' or 'staging' - destination database
        migration_type: 'missing' or 'mismatched' or 'both'
    
    Returns:
        Dict with preview of migration including row counts and samples
    """
    # Determine which connection to use as source
    if source_db == 'prod':
        source_conn = _connect_prod()
        dest_conn = _connect_staging()
    else:
        source_conn = _connect_staging()
        dest_conn = _connect_prod()
    
    source_orders = _get_all_orders(source_conn)
    dest_orders = _get_all_orders(dest_conn)
    
    missing_rows = []
    mismatched_rows = []
    
    # Find missing rows (in source but not in dest)
    if migration_type in ['missing', 'both']:
        for order_id in source_orders:
            if order_id not in dest_orders:
                row = source_orders[order_id]
                missing_rows.append({
                    'order_id': row[0],
                    'customer_name': row[1],
                    'amount': float(row[2]) if isinstance(row[2], Decimal) else row[2],
                    'country': row[3],
                    'created_at': str(row[4]) if row[4] else None
                })
    
    # Find mismatched rows (exist in both but with different data)
    if migration_type in ['mismatched', 'both']:
        for order_id in source_orders:
            if order_id in dest_orders:
                source_row = source_orders[order_id]
                dest_row = dest_orders[order_id]
                
                if source_row[1:] != dest_row[1:]:
                    mismatched_rows.append({
                        'order_id': order_id,
                        'customer_name': source_row[1],
                        'amount': float(source_row[2]) if isinstance(source_row[2], Decimal) else source_row[2],
                        'country': source_row[3],
                        'created_at': str(source_row[4]) if source_row[4] else None
                    })
    
    source_conn.close()
    dest_conn.close()
    
    total_rows = len(missing_rows) + len(mismatched_rows)
    
    return _convert_to_serializable({
        'status': 'success',
        'source_db': source_db,
        'dest_db': dest_db,
        'migration_type': migration_type,
        'missing_rows_count': len(missing_rows),
        'mismatched_rows_count': len(mismatched_rows),
        'total_rows_to_migrate': total_rows,
        'missing_rows_preview': missing_rows[:10],  # Show first 10
        'mismatched_rows_preview': mismatched_rows[:10]
    })


def create_backup_snapshot(db_name: str) -> Dict[str, Any]:
    """
    Create a backup snapshot of a database before migration.
    
    Args:
        db_name: 'prod' or 'staging'
    
    Returns:
        Dict with backup metadata and timestamp
    """
    import json
    from datetime import datetime
    
    if db_name == 'prod':
        conn = _connect_prod()
        db_config = get_prod_config()
    else:
        conn = _connect_staging()
        db_config = get_staging_config()
    
    orders = _get_all_orders(conn)
    conn.close()
    
    # Convert to list of dicts
    orders_list = []
    for order_id, row in orders.items():
        orders_list.append({
            'order_id': row[0],
            'customer_name': row[1],
            'amount': float(row[2]) if isinstance(row[2], Decimal) else row[2],
            'country': row[3],
            'created_at': str(row[4]) if row[4] else None
        })
    
    timestamp = datetime.now().isoformat()
    backup_filename = f"backup_{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    backup_path = os.path.join(DATA_DIR, backup_filename)
    
    backup_data = {
        'timestamp': timestamp,
        'database': db_name,
        'record_count': len(orders_list),
        'orders': orders_list
    }
    
    with open(backup_path, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    return _convert_to_serializable({
        'status': 'success',
        'backup_id': backup_filename,
        'database': db_name,
        'timestamp': timestamp,
        'record_count': len(orders_list),
        'backup_path': backup_path
    })


def migrate_missing_rows(source_db: str, dest_db: str, backup_id: str = None) -> Dict[str, Any]:
    """
    Migrate missing rows from source to destination database.
    
    Args:
        source_db: 'prod' or 'staging'
        dest_db: 'prod' or 'staging'
        backup_id: Optional backup ID for rollback
    
    Returns:
        Dict with migration results
    """
    if source_db == 'prod':
        source_conn = _connect_prod()
        dest_conn = _connect_staging()
    else:
        source_conn = _connect_staging()
        dest_conn = _connect_prod()
    
    source_orders = _get_all_orders(source_conn)
    dest_orders = _get_all_orders(dest_conn)
    
    # Find missing rows
    migrated_count = 0
    migrated_rows = []
    
    try:
        dest_cursor = dest_conn.cursor()
        
        for order_id in source_orders:
            if order_id not in dest_orders:
                row = source_orders[order_id]
                
                # Insert into destination
                dest_cursor.execute("""
                    INSERT INTO orders (order_id, customer_name, amount, country, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (order_id) DO NOTHING
                """, (row[0], row[1], row[2], row[3], row[4]))
                
                migrated_count += 1
                migrated_rows.append({
                    'order_id': row[0],
                    'customer_name': row[1],
                    'amount': float(row[2]) if isinstance(row[2], Decimal) else row[2]
                })
        
        dest_conn.commit()
        source_conn.close()
        dest_conn.close()
        
        return _convert_to_serializable({
            'status': 'success',
            'migration_type': 'missing_rows',
            'source_db': source_db,
            'dest_db': dest_db,
            'rows_migrated': migrated_count,
            'backup_id': backup_id,
            'migrated_rows_sample': migrated_rows[:10]
        })
    
    except Exception as e:
        dest_conn.rollback()
        source_conn.close()
        dest_conn.close()
        
        return {
            'status': 'error',
            'error': str(e),
            'backup_id': backup_id
        }


def migrate_mismatched_rows(source_db: str, dest_db: str, backup_id: str = None) -> Dict[str, Any]:
    """
    Migrate mismatched rows from source to destination database (overwrite).
    
    Args:
        source_db: 'prod' or 'staging'
        dest_db: 'prod' or 'staging'
        backup_id: Optional backup ID for rollback
    
    Returns:
        Dict with migration results
    """
    if source_db == 'prod':
        source_conn = _connect_prod()
        dest_conn = _connect_staging()
    else:
        source_conn = _connect_staging()
        dest_conn = _connect_prod()
    
    source_orders = _get_all_orders(source_conn)
    dest_orders = _get_all_orders(dest_conn)
    
    # Find mismatched rows
    migrated_count = 0
    migrated_rows = []
    
    try:
        dest_cursor = dest_conn.cursor()
        
        for order_id in source_orders:
            if order_id in dest_orders:
                source_row = source_orders[order_id]
                dest_row = dest_orders[order_id]
                
                # Check if they differ
                if source_row[1:] != dest_row[1:]:
                    # Update in destination
                    dest_cursor.execute("""
                        UPDATE orders 
                        SET customer_name = %s, amount = %s, country = %s, created_at = %s
                        WHERE order_id = %s
                    """, (source_row[1], source_row[2], source_row[3], source_row[4], source_row[0]))
                    
                    migrated_count += 1
                    migrated_rows.append({
                        'order_id': source_row[0],
                        'customer_name': source_row[1],
                        'amount': float(source_row[2]) if isinstance(source_row[2], Decimal) else source_row[2]
                    })
        
        dest_conn.commit()
        source_conn.close()
        dest_conn.close()
        
        return _convert_to_serializable({
            'status': 'success',
            'migration_type': 'mismatched_rows',
            'source_db': source_db,
            'dest_db': dest_db,
            'rows_migrated': migrated_count,
            'backup_id': backup_id,
            'migrated_rows_sample': migrated_rows[:10]
        })
    
    except Exception as e:
        dest_conn.rollback()
        source_conn.close()
        dest_conn.close()
        
        return {
            'status': 'error',
            'error': str(e),
            'backup_id': backup_id
        }


def rollback_to_backup(backup_id: str, db_name: str) -> Dict[str, Any]:
    """
    Rollback a database to a previous backup.
    
    Args:
        backup_id: Backup filename to restore from
        db_name: 'prod' or 'staging' - database to restore
    
    Returns:
        Dict with rollback results
    """
    import json
    
    backup_path = os.path.join(DATA_DIR, backup_id)
    
    if not os.path.exists(backup_path):
        return {
            'status': 'error',
            'error': f'Backup file not found: {backup_id}'
        }
    
    try:
        # Load backup data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Get connection to database
        if db_name == 'prod':
            conn = _connect_prod()
        else:
            conn = _connect_staging()
        
        cursor = conn.cursor()
        
        # Delete all current data
        cursor.execute("DELETE FROM orders")
        
        # Restore from backup
        for order in backup_data['orders']:
            cursor.execute("""
                INSERT INTO orders (order_id, customer_name, amount, country, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (order['order_id'], order['customer_name'], order['amount'], order['country'], order['created_at']))
        
        conn.commit()
        conn.close()
        
        return _convert_to_serializable({
            'status': 'success',
            'message': f'Successfully restored {db_name} database from backup',
            'backup_id': backup_id,
            'database': db_name,
            'records_restored': len(backup_data['orders'])
        })
    
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        
        return {
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    # Example usage
    print("Running full comparison...")
    result = run_full_comparison()
    
    import json
    print(json.dumps(result, indent=2))
