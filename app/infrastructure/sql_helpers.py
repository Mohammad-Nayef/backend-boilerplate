from collections.abc import Iterable as ABCIterable
from datetime import timedelta
from typing import Any, Literal, overload

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.constants import QueryResult
from app.common.utils import convert_to_time


@overload
def sql(
    db: Session,
    raw_sql: str,
    returns: Literal[QueryResult.LIST_OF_DICT],
    **params: Any,
) -> list[dict[str, Any]]: ...


@overload
def sql(
    db: Session,
    raw_sql: str,
    returns: Literal[QueryResult.DICT],
    **params: Any,
) -> dict[str, Any]: ...


@overload
def sql(
    db: Session,
    raw_sql: str,
    returns: Literal[QueryResult.LIST],
    **params: Any,
) -> list[Any]: ...


@overload
def sql(
    db: Session,
    raw_sql: str,
    returns: Literal[QueryResult.SCALAR],
    **params: Any,
) -> Any: ...


@overload
def sql(
    db: Session,
    raw_sql: str,
    returns: QueryResult = QueryResult.LIST_OF_DICT,
    **params: Any,
) -> Any: ...


def sql(
    db: Session,
    raw_sql: str,
    returns: QueryResult = QueryResult.LIST_OF_DICT,
    **params: Any,
) -> Any:
    new_params: dict[str, Any] = {}
    for key, value in params.items():
        if isinstance(value, (list, set)):
            values = list(value)
            placeholders = ", ".join(f":{key}_{index}" for index in range(len(values)))
            raw_sql = raw_sql.replace(f":{key}", placeholders)
            new_params.update(
                {f"{key}_{index}": item for index, item in enumerate(values)}
            )
        else:
            new_params[key] = value

    result = db.execute(text(raw_sql), new_params)
    db.flush()
    if not result.returns_rows:
        return None

    rows = result.fetchall()
    columns = result.keys()

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


def insert(db: Session, record: object):
    db.add(record)
    db.flush()
    return record


def bulk_insert(db: Session, records: object):
    if not isinstance(records, ABCIterable) or isinstance(records, str):
        raise TypeError("bulk_insert expects an iterable of records")
    db.add_all(records)
    db.flush()
