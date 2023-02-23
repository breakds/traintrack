from flask import Flask, jsonify

app = Flask(__name__)

jobs = {}


@app.route("/query")
def query():
    return jsonify({"status": "ok", "machine_info": "machine"})


if __name__ == "__main__":
    app.run(debug=True)
