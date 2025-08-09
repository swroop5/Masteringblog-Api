from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import json
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)  # enable CORS for all routes

DATA_FILE = Path(__file__).parent / "posts.json"

SWAGGER_URL="/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
API_URL="/static/masterblog.json" # (2) ensure you create this dir and file

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API' # (3) You can change this if you like
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

def load_posts():
    if not DATA_FILE.exists():
        seed = [
            {"id": 1, "title": "First post", "content": "This is the first post."},
            {"id": 2, "title": "Second post", "content": "This is the second post."},
        ]
        DATA_FILE.write_text(json.dumps(seed, indent=2), encoding="utf-8")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def save_posts(posts):
    DATA_FILE.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")

def next_id(posts):
    return max([p["id"] for p in posts], default=0) + 1

@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = load_posts()
    return jsonify(posts), 200

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    posts = load_posts()
    for p in posts:
        if p['id'] == post_id:
            return jsonify(p), 200
    return jsonify({"error": "Post not found"}), 404

@app.route('/api/posts', methods=['POST'])
def create_post():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify({"error": "Both 'title' and 'content' are required"}), 400

    posts = load_posts()
    post = {"id": next_id(posts), "title": title, "content": content}
    posts.append(post)
    save_posts(posts)
    return jsonify(post), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True) or {}

    posts = load_posts()
    for p in posts:
        if p['id'] == post_id:
            if "title" in data:
                t = str(data["title"]).strip()
                if not t:
                    return jsonify({"error": "Title cannot be empty"}), 400
                p["title"] = t
            if "content" in data:
                c = str(data["content"]).strip()
                if not c:
                    return jsonify({"error": "Content cannot be empty"}), 400
                p["content"] = c
            save_posts(posts)
            return jsonify(p), 200
    return jsonify({"error": "Post not found"}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    posts = load_posts()
    new_posts = [p for p in posts if p['id'] != post_id]
    if len(new_posts) == len(posts):
        return jsonify({"error": "Post not found"}), 404
    save_posts(new_posts)
    return "", 204

@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """
    GET /api/posts/search?title=<str>&content=<str>
    Returns posts whose title and/or content contain the given substrings
    (case-insensitive). If both params are provided, both must match (AND).
    If neither is provided (or only whitespace), returns an empty list.
    """
    # Read and normalize query params
    title_q = (request.args.get('title') or '').strip()
    content_q = (request.args.get('content') or '').strip()

    if not title_q and not content_q:
        return jsonify([]), 200

    posts = load_posts()
    results = posts

    if title_q:
        tl = title_q.lower()
        results = [p for p in results if tl in p.get('title', '').lower()]

    if content_q:
        cl = content_q.lower()
        results = [p for p in results if cl in p.get('content', '').lower()]

    return jsonify(results), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
