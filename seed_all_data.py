import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone

load_dotenv()

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
    client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "name": "Admin Two",
        "email": "admin2@test.com",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
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
        "cc": "🏆",
        "name": "Beginner Contest",
        "organizer": "TopRanker",
        "type": "Open to All",
        "startDate": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "endDate": datetime(2026, 4, 5, tzinfo=timezone.utc),
        "status": "active",
        "prize": 500,
        "eventCode": "BEGIN2026",
        "confHomePage": "",
        "problems": contest1_problems,
        "participants": [],
        "created_at": datetime.now(timezone.utc)
    },
    {
        "eventId": "C2",
        "cc": "🎯",
        "name": "Advanced Contest",
        "organizer": "TopRanker",
        "type": "Open to All",
        "startDate": datetime(2026, 4, 10, tzinfo=timezone.utc),
        "endDate": datetime(2026, 4, 15, tzinfo=timezone.utc),
        "status": "upcoming",
        "prize": 1000,
        "eventCode": "ADV2026",
        "confHomePage": "",
        "problems": contest2_problems,
        "participants": [],
        "created_at": datetime.now(timezone.utc)
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