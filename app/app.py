from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>My Cloud Image App</h1>
    <p>Web application is running!</p>
    <p>GCS + Cloud SQL integration coming next.</p>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    