"""Quick end-to-end check. Start the server first (uvicorn main:app --reload),
then run:  python smoke_test.py
Uses only the standard library."""
import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=120) as r:
        return json.load(r)


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def check(name, fn):
    try:
        result = fn()
        print(f"[PASS] {name}: {str(result)[:110]!r}")
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] {name}: {e}")


check("health", lambda: get("/health"))
check("qa", lambda: get("/qa?question=" + urllib.parse.quote("Which is the largest ocean?")))
check("explain", lambda: post("/explain", {"topic": "Photosynthesis"}))
check("summarize", lambda: post("/summarize", {"text": "The Industrial Revolution began in the late 18th century and moved production from farms to factories. New machines such as the steam engine made goods faster and cheaper, but also caused pollution and harsh working conditions."}))
check("quiz", lambda: post("/quiz", {"text": "Pythagoras theorem"}))
check("learn", lambda: get("/learn/recommendations?topic=SQL"))
