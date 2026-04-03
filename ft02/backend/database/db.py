import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# NOTE: Removed ?pgbouncer=true — psycopg2 does not recognize it as a valid DSN option.
# PgBouncer works transparently at the connection-pool level; no client-side flag is needed.
DEFAULT_DB_URL = "postgresql://postgres.dpcmvystzvchfcxznpyb:CXIBBGxysB8Foxld@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # auto-reconnect stale connections
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()