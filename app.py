from flask import Flask, request, jsonify
from pathlib import Path
import hashlib, requests, sys

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify(ok=True, service="transcriber", status="healthy")

def sha256_of(path: Path) -> str:
    """Return SHA256 checksum of a file."""
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

    print(f"[TRANSCRIBE] Incoming request: {data}", file=sys.stderr, flush=True)

    if not src:
        print("[TRANSCRIBE] ❌ No 'source_url' provided", file=sys.stderr, flush=True)
        return jsonify(ok=False, error="Missing 'source_url'"), 400

    # Make filename safe
    safe_name = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".", " ")).strip() or "input.bin"
    out_path = Path("/tmp") / safe_name
    print(f"[TRANSCRIBE] Saving to: {out_path}", file=sys.stderr, flush=True)

    try:
        print(f"[TRANSCRIBE] Starting download from: {src}", file=sys.stderr, flush=True)
        with requests.get(src, stream=True, timeout=60) as r:
            r.raise_for_status()
            with out_path.open("wb") as f:
                for chunk in r.iter_content(1024 * 256):
                    if chunk:
                        f.write(chunk)
        size = out_path.stat().st_size
        digest = sha256_of(out_path)
        print(f"[TRANSCRIBE] ✅ Download complete. Size: {size} bytes, SHA256: {digest}", file=sys.stderr, flush=True)

        return jsonify(
            ok=True,
            message="Downloaded OK",
            saved_path=str(out_path),
            bytes=size,
            sha256=digest,
        )

    except requests.HTTPError as e:
        err_msg = f"HTTP error {e.response.status_code} fetching source_url"
        print(f"[TRANSCRIBE] ❌ {err_msg}", file=sys.stderr, flush=True)
        return jsonify(ok=False, error=err_msg), 502
    except Exception as e:
        err_msg = f"Unexpected error: {str(e)}"
        print(f"[TRANSCRIBE] ❌ {err_msg}", file=sys.stderr, flush=True)
        return jsonify(ok=False, error=err_msg), 500
