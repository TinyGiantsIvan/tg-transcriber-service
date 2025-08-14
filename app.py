from flask import Flask, request, jsonify
from pathlib import Path
import hashlib, os, requests

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True, service="transcriber", status="healthy")

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

@app.route("/transcribe", methods=["POST"])
def transcribe_download_probe():
    data = request.get_json(silent=True) or {}
    src = data.get("source_url")
    filename = data.get("filename") or "input.bin"

    if not src:
        return jsonify(ok=False, error="Missing 'source_url'"), 400

    # Save to /tmp (writable in Render)
    safe_name = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".", " ")).strip() or "input.bin"
    out_path = Path("/tmp") / safe_name

    try:
        with requests.get(src, stream=True, timeout=60) as r:
            r.raise_for_status()
            with out_path.open("wb") as f:
                for chunk in r.iter_content(1024 * 256):
                    if chunk:
                        f.write(chunk)
        size = out_path.stat().st_size
        digest = sha256_of(out_path)
        return jsonify(
            ok=True,
            message="Downloaded OK",
            saved_path=str(out_path),
            bytes=size,
            sha256=digest,
        )
    except requests.HTTPError as e:
        return jsonify(ok=False, error=f"HTTP error fetching source_url: {e.response.status_code}"), 502
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500
