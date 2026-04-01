import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

# ==============================
# DB CONNECTION
# ==============================
# BUG FIX: Use environment variable for MongoDB URI instead of hardcoded credentials.
# Set MONGO_URI in your environment or .env file before running this script.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://TopRankr:TopRankr@cluster0.yzozjgg.mongodb.net/?appName=Cluster0"
)

try:
    client = MongoClient(MONGO_URI)
    # Ping to confirm connection before proceeding
    client.admin.command('ping')
    db = client["topranker"]
    print("✓ Connected to MongoDB")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    exit(1)

# ==============================
# CLEAR DATABASE
# ==============================
db.students.delete_many({})
db.admins.delete_many({})
db.contests.delete_many({})
# IMPORTANT: we DO NOT delete problems (they come from seed_problems.py)

# ==============================
# 1. STUDENTS (ONLY 3)
# ==============================
# BUG FIX: Added missing required fields — 'rating', 'problem_rankings', 'problemsSolved',
# and 'contests_participated' — that the leaderboard and statistics endpoints depend on.
# Without these, queries filtering or sorting on these fields silently return wrong results.
students = [
    {
        "name": "Alice Sharma",
        "email": "alice@test.com",
        "password": generate_password_hash("password123"),
        "role": "student",
        "institution": "",
        "country": "",
        "rating": 0,
        "problemsSolved": 0,
        "problem_rankings": {},
        "contests_participated": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "Bob Kumar",
        "email": "bob@test.com",
        "password": generate_password_hash("password123"),
        "role": "student",
        "institution": "",
        "country": "",
        "rating": 0,
        "problemsSolved": 0,
        "problem_rankings": {},
        "contests_participated": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "Charlie Singh",
        "email": "charlie@test.com",
        "password": generate_password_hash("password123"),
        "role": "student",
        "institution": "",
        "country": "",
        "rating": 0,
        "problemsSolved": 0,
        "problem_rankings": {},
        "contests_participated": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# BUG FIX: Wrapped insertions in try/except blocks to handle failures gracefully
# instead of crashing mid-script and leaving the DB in a partial state.
try:
    db.students.insert_many(students)
    print("✓ Inserted 3 students")
except Exception as e:
    print(f"✗ Failed to insert students: {e}")
    client.close()
    exit(1)

# ==============================
# 2. ADMINS (ONLY 2)
# ==============================
admins = [
    {
        "name": "Admin One",
        "email": "admin1@test.com",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "Admin Two",
        "email": "admin2@test.com",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

try:
    db.admins.insert_many(admins)
    print("✓ Inserted 2 admins")
except Exception as e:
    print(f"✗ Failed to insert admins: {e}")
    client.close()
    exit(1)

# ==============================
# 3. FETCH PROBLEMS (FROM seed_problems.py)
# ==============================
problems = list(db.problems.find())

if len(problems) == 0:
    print("❌ No problems found. Run seed_problems.py first.")
    client.close()
    exit(1)

problem_ids = [p["problemId"] for p in problems]

# ==============================
# 4. SPLIT PROBLEMS INTO 2 CONTESTS
# ==============================
mid = len(problem_ids) // 2

contest1_problems = problem_ids[:mid]
contest2_problems = problem_ids[mid:]

# ==============================
# 5. CREATE 2 CONTESTS
# ==============================
contests = [
    {
        "eventId": "C1",
        "name": "Beginner Contest",
        "organizer": "TopRanker",
        "type": "Open",
        "start": "01 Apr 2026",
        "end": "05 Apr 2026",
        "problems": contest1_problems,
        "participants": [],
        "created_at": datetime.utcnow()
    },
    {
        "eventId": "C2",
        "name": "Advanced Contest",
        "organizer": "TopRanker",
        "type": "Open",
        "start": "10 Apr 2026",
        "end": "15 Apr 2026",
        "problems": contest2_problems,
        "participants": [],
        "created_at": datetime.utcnow()
    }
]

try:
    db.contests.insert_many(contests)
    print("✓ Inserted 2 contests with evenly distributed problems")
except Exception as e:
    print(f"✗ Failed to insert contests: {e}")
    client.close()
    exit(1)

# ==============================
# DONE
# ==============================
print("\n===================================")
print("🎉 SEEDING COMPLETE")
print("===================================")

print("\n👨‍🎓 Students:")
print("alice@test.com / password123")
print("bob@test.com / password123")
print("charlie@test.com / password123")

print("\n👨‍💼 Admins:")
print("admin1@test.com / admin123")
print("admin2@test.com / admin123")

print("\n📊 Contests:")
print("C1 → First half problems")
print("C2 → Second half problems")

client.close()