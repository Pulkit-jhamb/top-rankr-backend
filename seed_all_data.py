"""
Comprehensive Data Seeding Script for TopRanker Platform
Seeds all collections with 30 realistic entries each:
- Students (30)
- Admins (5)
- Problems (30)
- Submissions (300+ distributed across users and problems)
- Contests (30)

This allows frontend to work dynamically without hardcoded data.
"""

from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import numpy as np

# MongoDB connection
MONGO_URI = "mongodb+srv://softwareproject011:software12345678@cluster1.iwwtbfy.mongodb.net/?appName=Cluster1"

try:
    client = MongoClient(MONGO_URI)
    db = client['topranker']
    print("✓ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    exit(1)

# Fitness function evaluators (from evaluate_solution.py)
def ackley_function(x):
    D = len(x)
    sum_sq = np.sum(x**2)
    sum_cos = np.sum(np.cos(2 * np.pi * x))
    term1 = -20 * np.exp(-0.02 * np.sqrt(sum_sq / D))
    term2 = -np.exp(sum_cos / D)
    return term1 + term2 + 20 + np.e

def rastrigin_function(x):
    D = len(x)
    return 10 * D + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))

def schwefel_function(x):
    D = len(x)
    return 418.9829 * D - np.sum(x * np.sin(np.sqrt(np.abs(x))))

def rosenbrock_function(x):
    return np.sum(100 * (x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def sphere_function(x):
    return np.sum(x**2)

def griewank_function(x):
    sum_sq = np.sum(x**2)
    prod_cos = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    return 1 + sum_sq / 4000 - prod_cos

def levy_function(x):
    w = 1 + (x - 1) / 4
    term1 = np.sin(np.pi * w[0])**2
    term2 = np.sum((w[:-1] - 1)**2 * (1 + 10 * np.sin(np.pi * w[:-1] + 1)**2))
    term3 = (w[-1] - 1)**2 * (1 + np.sin(2 * np.pi * w[-1])**2)
    return term1 + term2 + term3

# Fitness function mapping
FITNESS_FUNCTIONS = {
    '302': {'func': ackley_function, 'bounds': (-35, 35)},
    '301': {'func': rastrigin_function, 'bounds': (-5.12, 5.12)},
    '300': {'func': schwefel_function, 'bounds': (-500, 500)},
    '299': {'func': rosenbrock_function, 'bounds': (-5, 10)},
    '298': {'func': sphere_function, 'bounds': (-5.12, 5.12)},
    '297': {'func': griewank_function, 'bounds': (-600, 600)},
    '296': {'func': levy_function, 'bounds': (-10, 10)}
}

# Helper data
COUNTRIES = ["India", "USA", "China", "UK", "Germany", "France", "Japan", "Canada", "Australia", "Brazil", 
             "Russia", "South Korea", "Italy", "Spain", "Netherlands", "Sweden", "Poland", "Singapore"]

COUNTRY_FLAGS = {
    "India": "🇮🇳", "USA": "🇺🇸", "China": "🇨🇳", "UK": "🇬🇧", "Germany": "🇩🇪",
    "France": "🇫🇷", "Japan": "🇯🇵", "Canada": "🇨🇦", "Australia": "🇦🇺", "Brazil": "🇧🇷",
    "Russia": "🇷🇺", "South Korea": "🇰🇷", "Italy": "🇮🇹", "Spain": "🇪🇸", "Netherlands": "🇳🇱",
    "Sweden": "🇸🇪", "Poland": "🇵🇱", "Singapore": "🇸🇬"
}

INSTITUTIONS = [
    "IIT Delhi", "IIT Bombay", "IIT Kanpur", "IIT Kharagpur", "IIT Madras",
    "MIT", "Stanford University", "Harvard University", "Oxford University", "Cambridge University",
    "Tsinghua University", "Peking University", "ETH Zurich", "University of Tokyo",
    "National University of Singapore", "Thapar University", "BITS Pilani",
    "IIT Roorkee", "IIT Guwahati", "Anna University", "VIT University", "IIIT Delhi"
]

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Arjun", "Ananya", "Vikram", "Kavya", "Rohan", "Pooja",
    "John", "Emily", "Michael", "Sarah", "David", "Lisa", "James", "Emma", "Robert", "Olivia",
    "Wei", "Li", "Chen", "Zhang", "Wang", "Liu", "Yuki", "Sakura", "Hans", "Anna"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Verma", "Reddy", "Rao",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez",
    "Wang", "Li", "Zhang", "Chen", "Liu", "Yamamoto", "Sato", "Mueller", "Schmidt"
]

def generate_random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def generate_random_email(name):
    username = name.lower().replace(" ", ".")
    domains = ["gmail.com", "yahoo.com", "outlook.com", "university.edu", "student.edu"]
    return f"{username}{random.randint(1, 999)}@{random.choice(domains)}"

def generate_random_solution(dimension, bounds, quality='random'):
    """Generate solution array with different quality levels"""
    lower, upper = bounds
    
    if quality == 'excellent':
        # Near optimal solution
        if lower < 0 < upper:
            return np.random.normal(0, 0.5, dimension).clip(lower, upper)
        else:
            optimal = (lower + upper) / 2
            return np.random.normal(optimal, abs(upper - lower) * 0.05, dimension).clip(lower, upper)
    elif quality == 'good':
        # Good solution
        if lower < 0 < upper:
            return np.random.normal(0, 2, dimension).clip(lower, upper)
        else:
            optimal = (lower + upper) / 2
            return np.random.normal(optimal, abs(upper - lower) * 0.2, dimension).clip(lower, upper)
    else:
        # Random solution
        return np.random.uniform(lower, upper, dimension)

# ============================================================================
# 1. SEED STUDENTS (30 entries)
# ============================================================================
print("\n📚 Seeding Students...")

students_data = []
for i in range(30):
    name = generate_random_name()
    country = random.choice(COUNTRIES)
    
    student = {
        "name": name,
        "email": generate_random_email(name),
        "password": generate_password_hash("password123"),
        "role": "student",
        "institution": random.choice(INSTITUTIONS),
        "country": country,
        "rating": random.randint(800, 2500),
        "problems_solved": random.randint(0, 50),
        "contests_participated": random.randint(0, 15),
        "problem_rankings": {},  # Will be populated after submissions
        "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
        "updated_at": datetime.utcnow()
    }
    students_data.append(student)

# Clear existing students
db.students.delete_many({})
result = db.students.insert_many(students_data)
student_ids = result.inserted_ids
print(f"✓ Inserted {len(student_ids)} students")

# ============================================================================
# 2. SEED ADMINS (5 entries)
# ============================================================================
print("\n👨‍💼 Seeding Admins...")

admins_data = [
    {
        "name": "Admin Master",
        "email": "admin@topranker.com",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "permissions": ["manage_contests", "manage_problems", "manage_users"],
        "created_at": datetime.utcnow() - timedelta(days=730),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "JC Bansal",
        "email": "jc.bansal@sau.ac.in",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "permissions": ["manage_problems", "manage_contests"],
        "created_at": datetime.utcnow() - timedelta(days=700),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "MK Tiwari",
        "email": "mk.tiwari@iitkgp.ac.in",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "permissions": ["manage_problems"],
        "created_at": datetime.utcnow() - timedelta(days=680),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "Manoj Thakur",
        "email": "manoj.thakur@iitmandi.ac.in",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "permissions": ["manage_problems"],
        "created_at": datetime.utcnow() - timedelta(days=650),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "Contest Manager",
        "email": "contest@topranker.com",
        "password": generate_password_hash("admin123"),
        "role": "admin",
        "permissions": ["manage_contests", "manage_users"],
        "created_at": datetime.utcnow() - timedelta(days=600),
        "updated_at": datetime.utcnow()
    }
]

db.admins.delete_many({})
db.admins.insert_many(admins_data)
print(f"✓ Inserted {len(admins_data)} admins")

# ============================================================================
# 3. SEED PROBLEMS (30 entries - including existing 7 + 23 new)
# ============================================================================
print("\n🧩 Seeding Problems...")

# Keep existing 7 problems, add 23 more
existing_problems = [
    {
        "problemId": "302",
        "name": "Ackley Function Optimization",
        "description": "The Ackley function is a widely used benchmark function for testing optimization algorithms. It is characterized by a nearly flat outer region and a large hole at the center. The function poses a risk for optimization algorithms, particularly hill-climbing algorithms, to be trapped in one of its many local minima.",
        "owner": "JC Bansal",
        "ownerName": "JC Bansal",
        "ownerInstitution": "SAU, New Delhi",
        "cc": "🇮🇳",
        "level": "Easy",
        "type": "Multi-Modal, Continuous, Differentiable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "multi-modal", "benchmark"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = -20e^(-0.02√(1/D∑x_i²)) - e^(1/D∑cos(2πx_i)) + 20 + e",
            "constraint": "subject to -35 ≤ x_i ≤ 35. The global minimum is located at origin x* = (0,...,0) with f(x*) = 0.",
            "codeFiles": {
                "python": "ackley.py",
                "java": "Ackley.java",
                "cpp": "ackley.cpp",
                "c": "ackley.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2017, 12, 23),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "301",
        "name": "Rastrigin Function Minimization",
        "description": "The Rastrigin function is a highly multimodal function that is a typical example of non-linear multimodal function. It was first proposed by Rastrigin as a 2-dimensional function and has been generalized. Finding the minimum of this function is a fairly difficult problem due to its large search space and its large number of local minima.",
        "owner": "MK Tiwari",
        "ownerName": "MK Tiwari",
        "ownerInstitution": "IIT Kharagpur",
        "cc": "🇮🇳",
        "level": "Medium",
        "type": "Multi-Modal, Continuous, Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "multi-modal", "separable"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = 10D + ∑[x_i² - 10cos(2πx_i)]",
            "constraint": "subject to -5.12 ≤ x_i ≤ 5.12. The global minimum is at x* = (0,...,0) with f(x*) = 0.",
            "codeFiles": {
                "python": "rastrigin.py",
                "java": "Rastrigin.java",
                "cpp": "rastrigin.cpp",
                "c": "rastrigin.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2017, 11, 15),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "300",
        "name": "Schwefel Function Optimization",
        "description": "The Schwefel function is complex, with many local minima. The function is deceptive in that the global minimum is geometrically distant, over the parameter space, from the next best local minima. Therefore, the search algorithms are potentially prone to convergence in the wrong direction.",
        "owner": "Manoj Thakur",
        "ownerName": "Manoj Thakur",
        "ownerInstitution": "IIT Mandi",
        "cc": "🇮🇳",
        "level": "Hard",
        "type": "Multi-Modal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "deceptive", "hard"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = 418.9829D - ∑[x_i sin(√|x_i|)]",
            "constraint": "subject to -500 ≤ x_i ≤ 500. The global minimum is at x* = (420.9687,...,420.9687) with f(x*) ≈ 0.",
            "codeFiles": {
                "python": "schwefel.py",
                "java": "Schwefel.java",
                "cpp": "schwefel.cpp",
                "c": "schwefel.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2018, 1, 10),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "299",
        "name": "Rosenbrock Valley Function",
        "description": "The Rosenbrock function, also referred to as the Valley or Banana function, is a popular test problem for gradient-based optimization algorithms. The function is unimodal, and the global minimum lies in a narrow, parabolic valley. However, even though this valley is easy to find, convergence to the minimum is difficult.",
        "owner": "Lim Soo",
        "ownerName": "Lim Soo",
        "ownerInstitution": "Stanford University",
        "cc": "🇺🇸",
        "level": "Easy",
        "type": "Unimodal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "unimodal", "valley"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = ∑[100(x_{i+1} - x_i²)² + (1 - x_i)²]",
            "constraint": "subject to -5 ≤ x_i ≤ 10. The global minimum is at x* = (1,...,1) with f(x*) = 0.",
            "codeFiles": {
                "python": "rosenbrock.py",
                "java": "Rosenbrock.java",
                "cpp": "rosenbrock.cpp",
                "c": "rosenbrock.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2017, 10, 5),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "298",
        "name": "Sphere Function Optimization",
        "description": "The Sphere function is one of the simplest optimization test functions. It is continuous, convex and unimodal. The function is usually evaluated on the hypercube x_i ∈ [-5.12, 5.12], for all i = 1, ..., D. This is an easy optimization problem and is often used to test the convergence speed of optimization algorithms.",
        "owner": "BB Rose",
        "ownerName": "BB Rose",
        "ownerInstitution": "MIT",
        "cc": "🇺🇸",
        "level": "Easy",
        "type": "Unimodal, Continuous, Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "simple", "convex"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = ∑x_i²",
            "constraint": "subject to -5.12 ≤ x_i ≤ 5.12. The global minimum is at x* = (0,...,0) with f(x*) = 0.",
            "codeFiles": {
                "python": "sphere.py",
                "java": "Sphere.java",
                "cpp": "sphere.cpp",
                "c": "sphere.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2017, 9, 20),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "297",
        "name": "Griewank Function Minimization",
        "description": "The Griewank function has many widespread local minima, which are regularly distributed. The complexity is shown in the zoomed-in plots. The function has a product term that introduces interdependence among the variables. The aim is to find the global minimum.",
        "owner": "RS Joes",
        "ownerName": "RS Joes",
        "ownerInstitution": "UC Berkeley",
        "cc": "🇺🇸",
        "level": "Medium",
        "type": "Multi-Modal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "multi-modal", "interdependent"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = 1 + (1/4000)∑x_i² - Πcos(x_i/√i)",
            "constraint": "subject to -600 ≤ x_i ≤ 600. The global minimum is at x* = (0,...,0) with f(x*) = 0.",
            "codeFiles": {
                "python": "griewank.py",
                "java": "Griewank.java",
                "cpp": "griewank.cpp",
                "c": "griewank.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2017, 12, 1),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "296",
        "name": "Levy Function Optimization",
        "description": "The Levy function is a multimodal, continuous, non-separable function. It is a challenging optimization problem with many local minima. The function is named after the mathematician Paul Lévy and is commonly used to test optimization algorithms.",
        "owner": "KK James",
        "ownerName": "KK James",
        "ownerInstitution": "Oxford University",
        "cc": "🇬🇧",
        "level": "Hard",
        "type": "Multi-Modal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "challenging", "levy"],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": "f(x) = sin²(πw₁) + ∑[(wᵢ-1)²[1+10sin²(πwᵢ+1)]] + (w_D-1)²[1+sin²(2πw_D)] where wᵢ = 1 + (xᵢ-1)/4",
            "constraint": "subject to -10 ≤ x_i ≤ 10. The global minimum is at x* = (1,...,1) with f(x*) = 0.",
            "codeFiles": {
                "python": "levy.py",
                "java": "Levy.java",
                "cpp": "levy.cpp",
                "c": "levy.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2018, 2, 14),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Additional 23 problems (variations and new functions)
additional_problem_templates = [
    {
        "name": "Zakharov Function", 
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-5, 10),
        "func": "302"  # Reuse Ackley for scoring
    },
    {
        "name": "Michalewicz Function",
        "type": "Multi-Modal, Continuous",
        "level": "Hard",
        "bounds": (0, 3.14),
        "func": "301"
    },
    {
        "name": "Dixon-Price Function",
        "type": "Unimodal, Continuous",
        "level": "Medium",
        "bounds": (-10, 10),
        "func": "298"
    },
    {
        "name": "Styblinski-Tang Function",
        "type": "Multi-Modal, Continuous",
        "level": "Medium",
        "bounds": (-5, 5),
        "func": "301"
    },
    {
        "name": "Bent Cigar Function",
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-100, 100),
        "func": "298"
    },
    {
        "name": "High Conditioned Elliptic",
        "type": "Unimodal, Continuous",
        "level": "Medium",
        "bounds": (-100, 100),
        "func": "298"
    },
    {
        "name": "Discus Function",
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-100, 100),
        "func": "298"
    },
    {
        "name": "Weierstrass Function",
        "type": "Multi-Modal, Continuous",
        "level": "Hard",
        "bounds": (-0.5, 0.5),
        "func": "302"
    },
    {
        "name": "Katsuura Function",
        "type": "Multi-Modal, Continuous",
        "level": "Hard",
        "bounds": (0, 100),
        "func": "301"
    },
    {
        "name": "HappyCat Function",
        "type": "Multi-Modal, Continuous",
        "level": "Medium",
        "bounds": (-20, 20),
        "func": "297"
    },
    {
        "name": "HGBat Function",
        "type": "Multi-Modal, Continuous",
        "level": "Medium",
        "bounds": (-15, 15),
        "func": "297"
    },
    {
        "name": "Expanded Schaffer F6",
        "type": "Multi-Modal, Continuous",
        "level": "Hard",
        "bounds": (-100, 100),
        "func": "301"
    },
    {
        "name": "Schwefel 2.21",
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-100, 100),
        "func": "298"
    },
    {
        "name": "Schwefel 2.22",
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-10, 10),
        "func": "298"
    },
    {
        "name": "Step Function",
        "type": "Discontinuous",
        "level": "Easy",
        "bounds": (-100, 100),
        "func": "298"
    },
    {
        "name": "Quartic Function",
        "type": "Unimodal, Continuous",
        "level": "Medium",
        "bounds": (-1.28, 1.28),
        "func": "298"
    },
    {
        "name": "Alpine N.1 Function",
        "type": "Multi-Modal, Continuous",
        "level": "Medium",
        "bounds": (0, 10),
        "func": "301"
    },
    {
        "name": "Alpine N.2 Function",
        "type": "Multi-Modal, Continuous",
        "level": "Medium",
        "bounds": (0, 10),
        "func": "301"
    },
    {
        "name": "Xin-She Yang N.2",
        "type": "Multi-Modal, Continuous",
        "level": "Hard",
        "bounds": (-2*3.14, 2*3.14),
        "func": "302"
    },
    {
        "name": "Xin-She Yang N.3",
        "type": "Multi-Modal, Continuous",
        "level": "Hard",
        "bounds": (-20, 20),
        "func": "302"
    },
    {
        "name": "Rotated Hyper-Ellipsoid",
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-65.536, 65.536),
        "func": "298"
    },
    {
        "name": "Sum Squares Function",
        "type": "Unimodal, Continuous",
        "level": "Easy",
        "bounds": (-10, 10),
        "func": "298"
    },
    {
        "name": "Trid Function",
        "type": "Unimodal, Continuous",
        "level": "Medium",
        "bounds": (-100, 100),
        "func": "299"
    }
]

# Create owners pool
owner_names = ["Dr. " + generate_random_name() for _ in range(15)]
owner_institutions = INSTITUTIONS[:15]

new_problems = []
for i, template in enumerate(additional_problem_templates):
    problem_id = str(295 - i)  # 295, 294, 293, ... down to 273
    owner_idx = i % len(owner_names)
    country = random.choice(COUNTRIES)
    
    problem = {
        "problemId": problem_id,
        "name": template["name"],
        "description": f"A {template['type']} optimization benchmark function used to test algorithm performance. This function presents unique challenges for optimization algorithms due to its specific characteristics.",
        "owner": f"{owner_names[owner_idx]}, {owner_institutions[owner_idx]}",
        "ownerName": owner_names[owner_idx],
        "ownerInstitution": owner_institutions[owner_idx],
        "cc": COUNTRY_FLAGS.get(country, "🌍"),
        "level": template["level"],
        "type": template["type"],
        "category": "Benchmark Functions",
        "tags": ["optimization", template["type"].split(",")[0].lower().strip()],
        "dimensions": [
            {"dimension": 20, "submissions": 0},
            {"dimension": 50, "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": f"f(x) - See documentation for {template['name']}",
            "constraint": f"subject to {template['bounds'][0]} ≤ x_i ≤ {template['bounds'][1]}",
            "codeFiles": {
                "python": f"{template['name'].lower().replace(' ', '_')}.py",
                "java": f"{template['name'].replace(' ', '')}.java",
                "cpp": f"{template['name'].lower().replace(' ', '_')}.cpp",
                "c": f"{template['name'].lower().replace(' ', '_')}.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime.utcnow() - timedelta(days=random.randint(30, 730)),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    new_problems.append(problem)

all_problems = existing_problems + new_problems

db.problems.delete_many({})
db.problems.insert_many(all_problems)
print(f"✓ Inserted {len(all_problems)} problems (7 original + 23 new)")

# ============================================================================
# 4. SEED SUBMISSIONS (10 per student per problem dimension = 900+ total)
# ============================================================================
print("\n📝 Seeding Submissions...")

submissions_data = []
submission_count = 0

# Get all students and problems
students = list(db.students.find())
problems = list(db.problems.find())

# Select 10 random problems for submissions (to make it realistic)
active_problems = random.sample(problems[:10], 7)  # Use first 7 problems for submissions

for problem in active_problems:
    problem_id = problem['problemId']
    
    # Get fitness function
    if problem_id in FITNESS_FUNCTIONS:
        fitness_func = FITNESS_FUNCTIONS[problem_id]['func']
        bounds = FITNESS_FUNCTIONS[problem_id]['bounds']
    else:
        # Use sphere function as default for new problems
        fitness_func = sphere_function
        bounds = (-10, 10)
    
    # Select 10-20 random students to submit to this problem
    num_participants = random.randint(10, 20)
    participating_students = random.sample(students, num_participants)
    
    for student in participating_students:
        student_id = str(student['_id'])
        
        # Each student submits to 1-3 dimensions
        num_dimensions = random.randint(1, 3)
        dimensions_to_submit = random.sample([20, 50, 100], num_dimensions)
        
        for dimension in dimensions_to_submit:
            # Each student makes 1-3 attempts per dimension
            num_attempts = random.randint(1, 3)
            
            for attempt in range(num_attempts):
                # Quality distribution: 10% excellent, 30% good, 60% random
                quality_roll = random.random()
                if quality_roll < 0.1:
                    quality = 'excellent'
                elif quality_roll < 0.4:
                    quality = 'good'
                else:
                    quality = 'random'
                
                solution = generate_random_solution(dimension, bounds, quality)
                score = float(fitness_func(solution))
                
                submission = {
                    "problemId": problem_id,
                    "userId": student_id,
                    "userEmail": student['email'],
                    "userName": student['name'],
                    "code": str(solution.tolist()),
                    "language": "array",
                    "dimension": dimension,
                    "status": "evaluated",
                    "score": score,
                    "executionTime": random.uniform(0.01, 0.5),
                    "memoryUsed": random.uniform(1.0, 5.0),
                    "testCasesPassed": 1,
                    "totalTestCases": 1,
                    "errorMessage": None,
                    "submittedAt": datetime.utcnow() - timedelta(days=random.randint(1, 180)),
                    "evaluatedAt": datetime.utcnow() - timedelta(days=random.randint(1, 180))
                }
                
                submissions_data.append(submission)
                submission_count += 1

db.submissions.delete_many({})
db.submissions.insert_many(submissions_data)
print(f"✓ Inserted {submission_count} submissions")

# ============================================================================
# 5. UPDATE PROBLEM RANKINGS (Calculate from submissions)
# ============================================================================
print("\n🏆 Calculating Rankings...")

from collections import defaultdict

for problem in active_problems:
    problem_id = problem['problemId']
    
    for dimension in [20, 50, 100]:
        # Get all submissions for this problem-dimension
        submissions = list(db.submissions.find({
            'problemId': problem_id,
            'dimension': dimension,
            'status': 'evaluated'
        }).sort('score', 1))  # Sort by score ascending (lower is better)
        
        # Get best score per user
        user_best_scores = {}
        for sub in submissions:
            user_id = sub['userId']
            if user_id not in user_best_scores or sub['score'] < user_best_scores[user_id]:
                user_best_scores[user_id] = sub['score']
        
        # Rank users
        sorted_users = sorted(user_best_scores.items(), key=lambda x: x[1])
        
        # Update student rankings
        for rank, (user_id, score) in enumerate(sorted_users, 1):
            db.students.update_one(
                {'_id': student_id if isinstance(student_id := user_id, object) else ObjectId(user_id)},
                {
                    '$set': {
                        f'problem_rankings.{problem_id}.dimension_ranks.{dimension}': rank,
                        f'problem_rankings.{problem_id}.best_scores.{dimension}': score,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
        
        # Update problem dimension submission count
        db.problems.update_one(
            {'problemId': problem_id, 'dimensions.dimension': dimension},
            {'$set': {'dimensions.$.submissions': len(user_best_scores)}}
        )

# Calculate overall problem ranks
from bson import ObjectId

for student in students:
    student_id = student['_id']
    problem_rankings = db.students.find_one({'_id': student_id}).get('problem_rankings', {})
    
    for problem_id, rankings in problem_rankings.items():
        dimension_ranks = rankings.get('dimension_ranks', {})
        if dimension_ranks:
            avg_rank = sum(dimension_ranks.values()) / len(dimension_ranks)
            
            # Find overall rank among all students
            all_students_avg = []
            for s in students:
                s_rankings = db.students.find_one({'_id': s['_id']}).get('problem_rankings', {})
                if problem_id in s_rankings:
                    s_dim_ranks = s_rankings[problem_id].get('dimension_ranks', {})
                    if s_dim_ranks:
                        s_avg = sum(s_dim_ranks.values()) / len(s_dim_ranks)
                        all_students_avg.append((str(s['_id']), s_avg))
            
            all_students_avg.sort(key=lambda x: x[1])
            overall_rank = next((i+1 for i, (uid, _) in enumerate(all_students_avg) if uid == str(student_id)), None)
            
            if overall_rank:
                db.students.update_one(
                    {'_id': student_id},
                    {'$set': {f'problem_rankings.{problem_id}.overall_rank': overall_rank}}
                )

# Update total submissions per problem
for problem in problems:
    total_subs = db.submissions.count_documents({'problemId': problem['problemId']})
    db.problems.update_one(
        {'_id': problem['_id']},
        {'$set': {'totalSubmissions': total_subs}}
    )

print("✓ Rankings calculated and updated")

# ============================================================================
# 6. SEED CONTESTS (30 entries)
# ============================================================================
print("\n🏅 Seeding Contests...")

contest_types = ["Conference Event", "Class Test", "Open to All"]
contest_organizers = [
    "SocProcs 2024", "ICPC 2024", "CodeChef", "HackerRank", "IEEE CIS",
    "IIT Delhi", "IIT Bombay", "MIT", "Stanford", "Tsinghua University",
    "ACM", "Google", "Microsoft", "Meta", "Amazon"
]

contests_data = []
for i in range(30):
    event_id = f"E{330 - i}"  # E330, E329, ... down to E301
    contest_type = random.choice(contest_types)
    organizer = random.choice(contest_organizers)
    country = random.choice(COUNTRIES)
    
    start_date = datetime.utcnow() + timedelta(days=random.randint(-60, 60))
    end_date = start_date + timedelta(days=random.randint(1, 14))
    
    # Select 3-7 random problems for this contest
    num_problems = random.randint(3, 7)
    contest_problems = random.sample([p['problemId'] for p in problems], num_problems)
    
    if contest_type == "Conference Event":
        price = f"${random.choice([100, 300, 500, 800, 1000, 1500, 2000])}"
    elif contest_type == "Class Test":
        price = "Higher Grade"
    else:
        price = "Free Entry"
    
    contest = {
        "eventId": event_id,
        "name": f"{organizer} Contest {random.randint(1, 100)}",
        "confHomePage": f"https://{organizer.lower().replace(' ', '')}.com/contest/{event_id}" if contest_type == "Conference Event" else None,
        "organizer": organizer,
        "cc": COUNTRY_FLAGS.get(country, "🌍"),
        "type": contest_type,
        "start": start_date.strftime("%d %b %Y"),
        "end": end_date.strftime("%d %b %Y"),
        "price": price,
        "description": f"A {contest_type} organized by {organizer} featuring {num_problems} challenging optimization problems.",
        "problems": contest_problems,
        "participants": [],
        "eventCode": f"{event_id}-{random.randint(1000, 9999)}",
        "status": "upcoming" if start_date > datetime.utcnow() else ("ongoing" if end_date > datetime.utcnow() else "completed"),
        "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
        "updated_at": datetime.utcnow()
    }
    contests_data.append(contest)

# Create contests collection if it doesn't exist
db.contests.delete_many({})
db.contests.insert_many(contests_data)
print(f"✓ Inserted {len(contests_data)} contests")

# ============================================================================
# 7. FINAL STATISTICS
# ============================================================================
print("\n" + "="*60)
print("📊 DATABASE SEEDING COMPLETED!")
print("="*60)

total_students = db.students.count_documents({})
total_admins = db.admins.count_documents({})
total_problems = db.problems.count_documents({})
total_submissions = db.submissions.count_documents({})
total_contests = db.contests.count_documents({})

print(f"""
✓ Students:     {total_students}
✓ Admins:       {total_admins}
✓ Problems:     {total_problems}
✓ Submissions:  {total_submissions}
✓ Contests:     {total_contests}

🔐 Test Login Credentials:
   Student: {students_data[0]['email']} / password123
   Admin:   admin@topranker.com / admin123

📝 Sample Problem IDs: {', '.join([p['problemId'] for p in all_problems[:5]])}

🏆 Sample Contest IDs: {', '.join([c['eventId'] for c in contests_data[:3]])}
""")

print("You can now test the frontend with real dynamic data!")
print("="*60)

client.close()
