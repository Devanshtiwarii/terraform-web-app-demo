import os

import psycopg2

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    Response,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from google.cloud import storage


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-secret-key-change-later"
)


# -----------------------------
# Google Cloud Storage
# -----------------------------

BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)


# -----------------------------
# Cloud SQL
# -----------------------------

def get_db_connection():
    db_host = os.environ.get("DB_HOST", "127.0.0.1")

    return psycopg2.connect(
        host=db_host,
        port=int(os.environ.get("DB_PORT", "5432")),
        database="imageapp",
        user="appuser",
        password=os.environ["DB_PASSWORD"]
    )
# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            filename,
            gcs_object,
            content_type,
            created_at
        FROM images
        WHERE user_id = %s
        ORDER BY created_at DESC;
    """, (user_id,))

    images = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        images=images
    )

# -----------------------------
# Register
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        return "All fields are required", 400

    password_hash = generate_password_hash(password)

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (
            username,
            email,
            password_hash
        ))

        user_id = cursor.fetchone()[0]

        connection.commit()

    except psycopg2.errors.UniqueViolation:

        connection.rollback()

        cursor.close()
        connection.close()

        return "Username or email already exists", 400

    cursor.close()
    connection.close()

    session["user_id"] = user_id
    session["username"] = username

    return redirect(url_for("home"))


# -----------------------------
# Login
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, password_hash
        FROM users
        WHERE email = %s;
    """, (email,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:
        return "Invalid email or password", 401

    user_id, username, password_hash = user

    if not check_password_hash(
        password_hash,
        password
    ):
        return "Invalid email or password", 401

    session["user_id"] = user_id
    session["username"] = username

    return redirect(url_for("home"))


# -----------------------------
# Logout
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# -----------------------------
# Upload
# -----------------------------

@app.route("/upload", methods=["POST"])
def upload():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    file = request.files.get("image")

    if not file or file.filename == "":
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)

    gcs_object = f"users/{user_id}/{filename}"

    blob = bucket.blob(gcs_object)

    blob.upload_from_file(
        file,
        content_type=file.content_type
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO images
        (
            user_id,
            filename,
            gcs_object,
            content_type
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """, (
        user_id,
        filename,
        gcs_object,
        file.content_type
    ))

    image_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Uploaded image ID: {image_id}")

    return redirect(url_for("home"))

# -----------------------------
# View image
# -----------------------------

@app.route("/image/<int:image_id>")
def view_image(image_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT gcs_object, content_type
        FROM images
        WHERE id = %s
        AND user_id = %s;
    """, (
        image_id,
        user_id
    ))

    image = cursor.fetchone()

    cursor.close()
    connection.close()

    if not image:
        return "Image not found", 404

    gcs_object, content_type = image

    blob = bucket.blob(gcs_object)

    if not blob.exists():
        return "File not found in Cloud Storage", 404

    image_data = blob.download_as_bytes()

    return Response(
        image_data,
        mimetype=content_type
    )
    
@app.route(
    "/edit/<int:image_id>",
    methods=["POST"]
)
def edit_image(image_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    new_filename = secure_filename(
        request.form.get("new_filename", "")
    )

    if not new_filename:
        return redirect(url_for("home"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT gcs_object
        FROM images
        WHERE id = %s
        AND user_id = %s;
    """, (
        image_id,
        user_id
    ))

    image = cursor.fetchone()

    if not image:

        cursor.close()
        connection.close()

        return "Image not found", 404

    old_gcs_object = image[0]

    new_gcs_object = (
        f"users/{user_id}/{new_filename}"
    )

    old_blob = bucket.blob(
        old_gcs_object
    )

    if not old_blob.exists():

        cursor.close()
        connection.close()

        return "File not found in Cloud Storage", 404

    bucket.copy_blob(
        old_blob,
        bucket,
        new_gcs_object
    )

    old_blob.delete()

    cursor.execute("""
        UPDATE images
        SET
            filename = %s,
            gcs_object = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        AND user_id = %s;
    """, (
        new_filename,
        new_gcs_object,
        image_id,
        user_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("home"))

# -----------------------------
# Delete
# -----------------------------

@app.route(
    "/delete/<int:image_id>",
    methods=["POST"]
)
def delete_image(image_id):

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT gcs_object
        FROM images
        WHERE id = %s
        AND user_id = %s;
    """, (
        image_id,
        user_id
    ))

    image = cursor.fetchone()

    if not image:

        cursor.close()
        connection.close()

        return "Image not found", 404

    gcs_object = image[0]

    blob = bucket.blob(gcs_object)

    if blob.exists():
        blob.delete()

    cursor.execute("""
        DELETE FROM images
        WHERE id = %s
        AND user_id = %s;
    """, (
        image_id,
        user_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)