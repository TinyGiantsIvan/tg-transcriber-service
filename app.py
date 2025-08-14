from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True, service="transcriber", status="healthy")

@app.route("/transcribe", methods=["POST"])
def transcribe_stub():
    data = request.get_json(silent=True) or {}
    return jsonify(received=data, message="Transcriber endpoint is alive")
