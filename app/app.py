import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    Response
)

from werkzeug.utils import secure_filename
from google.cloud import storage


app = Flask(__name__)


# ============================================================
# GCS CONFIGURATION
# ============================================================

BUCKET_NAME = "terraform-webapp-images-12345"

storage_client = storage.Client()

bucket = storage_client.bucket(BUCKET_NAME)


# ============================================================
# TEMPORARY USER
# ============================================================

# This is temporary.
# Later Cloud SQL + authentication will provide the real user ID.

CURRENT_USER_ID = 1


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    prefix = f"users/{CURRENT_USER_ID}/"

    blobs = bucket.list_blobs(
        prefix=prefix
    )

    images = []

    for blob in blobs:

        if blob.name == prefix:
            continue

        filename = blob.name.split("/")[-1]

        if filename:
            images.append(filename)

    return render_template(
        "index.html",
        images=images
    )


# ============================================================
# UPLOAD IMAGE
# ============================================================

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files.get("image")

    if not file or file.filename == "":
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)

    if not filename:
        return redirect(url_for("home"))

    object_name = (
        f"users/{CURRENT_USER_ID}/{filename}"
    )

    blob = bucket.blob(object_name)

    blob.upload_from_file(
        file,
        content_type=file.content_type
    )

    return redirect(url_for("home"))


# ============================================================
# VIEW IMAGE
# ============================================================

@app.route("/image/<filename>")
def view_image(filename):

    filename = secure_filename(filename)

    if not filename:
        return redirect(url_for("home"))

    object_name = (
        f"users/{CURRENT_USER_ID}/{filename}"
    )

    blob = bucket.blob(object_name)

    if not blob.exists():
        return "Image not found", 404

    image_data = blob.download_as_bytes()

    return Response(
        image_data,
        mimetype=blob.content_type
    )


# ============================================================
# DELETE IMAGE
# ============================================================

@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):

    filename = secure_filename(filename)

    if not filename:
        return redirect(url_for("home"))

    object_name = (
        f"users/{CURRENT_USER_ID}/{filename}"
    )

    blob = bucket.blob(object_name)

    if blob.exists():
        blob.delete()

    return redirect(url_for("home"))


# ============================================================
# EDIT / RENAME IMAGE
# ============================================================

@app.route("/edit/<filename>", methods=["POST"])
def edit(filename):

    filename = secure_filename(filename)

    new_filename = secure_filename(
        request.form.get(
            "new_filename",
            ""
        )
    )

    if not filename or not new_filename:
        return redirect(url_for("home"))

    old_object_name = (
        f"users/{CURRENT_USER_ID}/{filename}"
    )

    new_object_name = (
        f"users/{CURRENT_USER_ID}/{new_filename}"
    )

    old_blob = bucket.blob(
        old_object_name
    )

    if not old_blob.exists():
        return "Image not found", 404

    # GCS rename = copy + delete
    bucket.copy_blob(
        old_blob,
        bucket,
        new_object_name
    )

    old_blob.delete()

    return redirect(url_for("home"))


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
