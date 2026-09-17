import psycopg2

connection = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="imageapp",
    user="appuser",
    password="2426rishi"
)

print("Connected to Cloud SQL successfully!")

connection.close()