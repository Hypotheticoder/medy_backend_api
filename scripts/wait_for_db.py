import os
import sys
import time
import psycopg2

def wait_for_db():
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgrespassword")
    db_name = os.getenv("DB_NAME", "medy_db")

    print(f"Waiting for database at {db_host}:{db_port} to become available...")
    
    max_retries = 30
    retry_interval = 2

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            conn.close()
            print("Database is ready!")
            sys.exit(0)
        except psycopg2.OperationalError as e:
            print(f"Database not ready yet... Retrying in {retry_interval} seconds. ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    print("Failed to connect to the database within the time limit.")
    sys.exit(1)

if __name__ == "__main__":
    wait_for_db()
