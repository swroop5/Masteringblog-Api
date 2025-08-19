"""Masterblog API
-----------------

A minimal Flask JSON API for simple blog posts stored in a local JSON file.
Includes:
- CRUD endpoints under /api/posts
- Simple substring search
- Swagger UI mounted at /api/docs

Run:
    python app.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# Paths / constants
DATA_FILE: Path = Path(__file__).parent / "posts.json"

# Swagger/OpenAPI UI configuration
SWAGGER_URL = "/api/docs"
# Ensure this file exists and is served
API_URL = "/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Masterblog API"},
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


def load_posts() -> List[Dict[str, Any]]:
    """Load all posts from the JSON data file.

    If the data file does not exist, it is created with seed content.

    Returns:
        list[dict]: The list of post dictionaries with keys
        ``id``, ``title``, and ``content``.
    """
    if not DATA_FILE.exists():
        seed = [
            {"id": 1, "title": "First post", "content": "This is the first post."},
            {"id": 2, "title": "Second post", "content": "This is the second post."},
        ]
        DATA_FILE.write_text(json.dumps(seed, indent=2), encoding="utf-8")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_posts(posts: List[Dict[str, Any]]) -> None:
    """Persist posts to the JSON data file.

    Args:
        posts: The list of post dictionaries to save.
    """
    DATA_FILE.write_text(
        json.dumps(posts, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def next_id(posts: List[Dict[str, Any]]) -> int:
    """Compute the next numeric post ID.

    Args:
        posts: The existing list of posts.

    Returns:
        int: The next ID (max existing ID + 1, or 1 if none).
    """
    return max([p["id"] for p in posts], default=0) + 1


@app.route("/api/posts", methods=["GET"])
def get_posts():
    """List all posts.

    Returns:
        Response: 200 with JSON array of posts.
    """
    posts = load_posts()
    return jsonify(posts), 200


@app.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post(post_id: int):
    """Retrieve a single post by its ID.

    Args:
        post_id: The numeric ID of the post.

    Returns:
        Response: 200 with the post JSON if found, else 404.
    """
    posts = load_posts()
    for post in posts:
        if post["id"] == post_id:
            return jsonify(post), 200
    return jsonify({"error": "Post not found"}), 404


@app.route("/api/posts", methods=["POST"])
def create_post():
    """Create a new post.

    Expects JSON with non-empty ``title`` and ``content``.

    Returns:
        Response:
            - 201 with created post JSON.
            - 400 if fields are missing/empty.
            - 415 if Content-Type is not JSON.
    """
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


@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id: int):
    """Update an existing post (full/partial).

    Accepts JSON with optional ``title`` and/or ``content``.
    Empty strings are rejected.

    Args:
        post_id: The numeric ID of the post to update.

    Returns:
        Response:
            - 200 with updated post JSON on success.
            - 400 if provided fields are empty.
            - 404 if the post does not exist.
            - 415 if Content-Type is not JSON.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json(silent=True) or {}
    posts = load_posts()

    for post in posts:
        if post["id"] == post_id:
            if "title" in data:
                title = str(data["title"]).strip()
                if not title:
                    return jsonify({"error": "Title cannot be empty"}), 400
                post["title"] = title

            if "content" in data:
                content = str(data["content"]).strip()
                if not content:
                    return jsonify({"error": "Content cannot be empty"}), 400
                post["content"] = content

            save_posts(posts)
            return jsonify(post), 200

    return jsonify({"error": "Post not found"}), 404


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id: int):
    """Delete a post by its ID.

    Args:
        post_id: The numeric ID of the post to delete.

    Returns:
        Response:
            - 204 on successful deletion.
            - 404 if the post does not exist.
    """
    posts = load_posts()
    new_posts = [p for p in posts if p["id"] != post_id]
    if len(new_posts) == len(posts):
        return jsonify({"error": "Post not found"}), 404

    save_posts(new_posts)
    return "", 204


@app.route("/api/posts/search", methods=["GET"])
def search_posts():
    """Search posts by title/content (case-insensitive).

    Query Parameters:
        title (str, optional): Substring to search in titles.
        content (str, optional): Substring to search in contents.

    Behavior:
        - If both params are provided, both must match (AND).
        - If neither is provided (or only whitespace), returns an empty list.

    Returns:
        Response: 200 with JSON array of matching posts.
    """
    title_q = (request.args.get("title") or "").strip()
    content_q = (request.args.get("content") or "").strip()

    if not title_q and not content_q:
        return jsonify([]), 200

    posts = load_posts()
    results = posts

    if title_q:
        tl = title_q.lower()
        results = [p for p in results if tl in p.get("title", "").lower()]

    if content_q:
        cl = content_q.lower()
        results = [p for p in results if cl in p.get("content", "").lower()]

    return jsonify(results), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
