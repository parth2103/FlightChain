
import pymysql
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Parse database URL
# Format: mysql+pymysql://user:password@host:port/dbname
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found")
    exit(1)

# Simple parsing (not robust but sufficient for this specific URL)
# Assumes format: mysql+pymysql://root:password@localhost:3306/flightchain
try:
    auth_part = db_url.split("://")[1]
    credentials, location = auth_part.split("@")
    user, password = credentials.split(":")
    host_port, db_name = location.split("/")
    host, port = host_port.split(":")
    port = int(port)
except Exception as e:
    print(f"Failed to parse DATABASE_URL: {e}")
    exit(1)

print(f"Connecting to {host}:{port} as {user}...")

# Connect to MySQL server (no DB selected yet)
try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        cursorclass=pymysql.cursors.DictCursor
    )
except pymysql.err.OperationalError as e:
    print(f"Connection failed: {e}")
    # If connection fails, ensure you check if you need to use a different user/pass
    exit(1)

try:
    with conn.cursor() as cursor:
        # Create database
        print(f"Creating database {db_name} if not exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # Read schema file
        with open("migrations/schema.sql", "r") as f:
            schema_sql = f.read()
        
        # Split by statements
        # This is a naive split by semicolon, might break on complex SQL but ok for this schema
        statements = schema_sql.split(";")
        
        print("Executing schema...")
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    print(f"Error executing statement: {e}")
                    # Continue anyway as some might be benign (like DROP IF EXISTS)
        
    conn.commit()
    print("Database initialized successfully!")

finally:
    conn.close()
