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


if __name__ == "__main__":
    # Example usage
    print("Running full comparison...")
    result = run_full_comparison()
    
    import json
    print(json.dumps(result, indent=2))
