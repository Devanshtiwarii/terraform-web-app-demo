import psycopg2


connection = psycopg2.connect(
    host="127.0.0.1",
    port=5432,
    database="imageapp",
    user="appuser",
    password="2426rishi"
)

cursor = connection.cursor()


cursor.execute("""
    INSERT INTO users (username, email, password_hash)
    VALUES (%s, %s, %s)
    RETURNING id;
""", (
    "alice",
    "alice@example.com",
    "temporary-password-hash"
))


user_id = cursor.fetchone()[0]

connection.commit()

print(f"User created with ID: {user_id}")


cursor.close()
connection.close()