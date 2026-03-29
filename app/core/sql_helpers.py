from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from collections.abc import Iterable as ABCIterable
from app.core.constants import QueryResult
from app.core.utils import convert_to_time

def execute_raw_query(db: Session, raw_sql: str, returns: QueryResult = QueryResult.LIST_OF_DICT, **params):
    """
    Helper to execute raw SQL efficiently while automatically parsing IN clauses, 
    fixing database time objects, and shaping the return type.
    """
    new_params = {}
    for key, value in params.items():
        if isinstance(value, (list, set)):
            value = list(value)
            placeholders = ", ".join(f":{key}_{i}" for i in range(len(value)))
            raw_sql = raw_sql.replace(f":{key}", placeholders)
            new_params.update({f"{key}_{i}": v for i, v in enumerate(value)})
        else:
            new_params[key] = value

    res = db.execute(text(raw_sql), new_params)
    db.flush()
    if not res.returns_rows:
        return None

    rows = res.fetchall()
    columns = res.keys()

    for i in range(len(rows)):
        row = list(rows[i])
        for j in range(len(row)):
            if isinstance(row[j], timedelta):
                row[j] = convert_to_time(row[j])
        rows[i] = tuple(row)

    if returns == QueryResult.LIST_OF_DICT:
        return [dict(zip(columns, row)) for row in rows]
    if returns == QueryResult.LIST:
        return [row[0] for row in rows] if columns and rows else []
    if returns == QueryResult.DICT:
        return dict(zip(columns, rows[0])) if rows else {}
    if returns == QueryResult.SCALAR:
        return rows[0][0] if rows and columns else None

    return rows

def bulk_insert(db: Session, records: object):
    """Insert a single record or list of records."""
    if isinstance(records, ABCIterable) and not isinstance(records, str):
        db.add_all(records)
    else:
        db.add(records)
    db.flush()
