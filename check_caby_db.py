import psycopg2
conn = psycopg2.connect(dbname="products_db", user="postgres", password="postgres", host="localhost", port="5432")
cur = conn.cursor()
cur.execute("SELECT id, order_type, vehicle_type, status FROM customer_orders ORDER BY created_at DESC LIMIT 5;")
for row in cur.fetchall():
    print(row)
