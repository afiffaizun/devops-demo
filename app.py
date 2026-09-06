from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from DevOps CI/CD!"

@app.route("/health")
def health():
    return "OK"

app.run(host="0.0.0.0", port=5000)
