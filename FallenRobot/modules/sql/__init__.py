from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from FallenRobot import LOGGER as log

# Database URL for your MySQL database
DB_URI = "mysql+pymysql://sql12755405:uEKcUyymli@sql12.freesqldatabase.com:3306/sql12755405"

# Define the base for SQLAlchemy models
BASE = declarative_base()


def start() -> scoped_session:
    """
    Initializes the SQLAlchemy engine and returns a scoped session.
    Supports MySQL connection.
    """
    # Create SQLAlchemy engine
    try:
        engine = create_engine(DB_URI)
        log.info("[Database] Connecting to the database...")
        BASE.metadata.bind = engine
        BASE.metadata.create_all(engine)  # Create tables if they don't exist
        log.info("[Database] Connection successful.")
        return scoped_session(sessionmaker(bind=engine, autoflush=False))
    except Exception as e:
        log.exception(f"[Database] Failed to connect: {e}")
        raise e  # Re-raise exception to halt execution on failure


# Start the database session
try:
    SESSION = start()
except Exception as db_error:
    log.error("[Database] Unable to initialize the database session. Exiting.")
    exit(1)

