from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/topranker')

try:
    client = MongoClient(MONGO_URI)
    db = client['topranker']
    print("✓ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    db = None

# Import blueprints
from auth import auth_bp
from problems import problems_bp
from contests import contests_bp
from statistics import statistics_bp
from leaderboard import leaderboard_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(problems_bp, url_prefix='/api/problems')
app.register_blueprint(contests_bp, url_prefix='/api/contests')
app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')

@app.route("/health", methods=["GET"])
def health_check():
    mongo_status = "connected" if db is not None else "disconnected"
    return jsonify(status="ok", mongodb=mongo_status), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3999, debug=True)