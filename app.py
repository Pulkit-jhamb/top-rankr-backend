from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = "mongodb+srv://softwareproject011:software12345678@cluster1.iwwtbfy.mongodb.net/?appName=Cluster1"

try:
    client = MongoClient(MONGO_URI)
    db = client['topranker']
    print("✓ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    db = None

from auth import auth_bp
from problems import problems_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(problems_bp, url_prefix='/api/problems')

@app.route("/health", methods=["GET"])
def health_check():
    mongo_status = "connected" if db is not None else "disconnected"
    return jsonify(status="ok", mongodb=mongo_status), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3999, debug=True)

