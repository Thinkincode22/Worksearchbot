"""Допоміжні функції для роботи з БД"""
from contextlib import contextmanager
from database.database import get_db
from sqlalchemy.orm import Session


@contextmanager
def get_db_session():
    """Context manager для роботи з сесією БД"""
    db_gen = get_db()
    db: Session = next(db_gen)
    try:
        yield db
    finally:
        try:
            next(db_gen, None)
        except StopIteration:
            pass
