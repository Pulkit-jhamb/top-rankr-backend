#!/usr/bin/env python3
"""Create test users for workflow testing"""

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI, tlsInsecure=True)
db = client.topranker

# Test student
student = {
    "name": "Test Student",
    "email": "student@test.com",
    "password": generate_password_hash("password123"),
    "role": "student",
    "country": "Test Country",
    "institution": "Test University",
    "created_at": datetime.now(timezone.utc),
    "problem_rankings": {},
    "contest_rankings": {}
}

# Test admin
admin = {
    "name": "Test Admin",
    "email": "admin@test.com",
    "password": generate_password_hash("admin123"),
    "role": "admin",
    "permissions": [],
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
}

# Upsert (update if exists, insert if not)
db.students.update_one({"email": student["email"]}, {"$set": student}, upsert=True)
db.admins.update_one({"email": admin["email"]}, {"$set": admin}, upsert=True)

print("✅ Test users created/updated:")
print(f"   Student: {student['email']} / password123")
print(f"   Admin: {admin['email']} / admin123")
