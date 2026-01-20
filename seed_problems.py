"""
Script to seed dummy problems data into MongoDB
Run this script once to populate the problems collection
"""

from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
MONGO_URI = "mongodb+srv://softwareproject011:software12345678@cluster1.iwwtbfy.mongodb.net/?appName=Cluster1"

try:
    client = MongoClient(MONGO_URI)
    db = client['topranker']
    print("✓ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    exit(1)

# Dummy problems data
problems_data = [
    {
        "problemId": "302",
        "name": "Ackley Function Optimization",
        "description": "The Ackley function is a widely used benchmark function for testing optimization algorithms. It is characterized by a nearly flat outer region and a large hole at the center. The function poses a risk for optimization algorithms, particularly hill-climbing algorithms, to be trapped in one of its many local minima.",
        "owner": "JC Bansal, SAU, New Delhi",
        "ownerName": "JC Bansal",
        "ownerInstitution": "SAU, New Delhi",
        "cc": "🇮🇳",
        "level": "Easy",
        "type": "Multi-Modal, Continuous, Differentiable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "multi-modal", "benchmark"],
        "dimensions": [
            {"dimension": 20, "submissions": 36},
            {"dimension": 50, "submissions": 34},
            {"dimension": 100, "submissions": 25}
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
        "totalSubmissions": 95,
        "totalSolved": 42,
        "acceptanceRate": 44.2,
        "submissionDate": datetime(2017, 12, 23),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "301",
        "name": "Rastrigin Function Minimization",
        "description": "The Rastrigin function is a highly multimodal function that is a typical example of non-linear multimodal function. It was first proposed by Rastrigin as a 2-dimensional function and has been generalized. Finding the minimum of this function is a fairly difficult problem due to its large search space and its large number of local minima.",
        "owner": "MK Tiwari, IIT Kharagpur",
        "ownerName": "MK Tiwari",
        "ownerInstitution": "IIT Kharagpur",
        "cc": "🇮🇳",
        "level": "Medium",
        "type": "Multi-Modal, Continuous, Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "multi-modal", "separable"],
        "dimensions": [
            {"dimension": 20, "submissions": 28},
            {"dimension": 50, "submissions": 22},
            {"dimension": 100, "submissions": 18}
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
        "totalSubmissions": 68,
        "totalSolved": 31,
        "acceptanceRate": 45.6,
        "submissionDate": datetime(2017, 11, 15),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "300",
        "name": "Schwefel Function Optimization",
        "description": "The Schwefel function is complex, with many local minima. The function is deceptive in that the global minimum is geometrically distant, over the parameter space, from the next best local minima. Therefore, the search algorithms are potentially prone to convergence in the wrong direction.",
        "owner": "Manoj Thakur, IIT Mandi",
        "ownerName": "Manoj Thakur",
        "ownerInstitution": "IIT Mandi",
        "cc": "🇮🇳",
        "level": "Hard",
        "type": "Multi-Modal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "deceptive", "hard"],
        "dimensions": [
            {"dimension": 20, "submissions": 15},
            {"dimension": 50, "submissions": 12},
            {"dimension": 100, "submissions": 8}
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
        "totalSubmissions": 35,
        "totalSolved": 12,
        "acceptanceRate": 34.3,
        "submissionDate": datetime(2018, 1, 10),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "299",
        "name": "Rosenbrock Valley Function",
        "description": "The Rosenbrock function, also referred to as the Valley or Banana function, is a popular test problem for gradient-based optimization algorithms. The function is unimodal, and the global minimum lies in a narrow, parabolic valley. However, even though this valley is easy to find, convergence to the minimum is difficult.",
        "owner": "Lim Soo, Stanford University",
        "ownerName": "Lim Soo",
        "ownerInstitution": "Stanford University",
        "cc": "🇺🇸",
        "level": "Easy",
        "type": "Unimodal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "unimodal", "valley"],
        "dimensions": [
            {"dimension": 20, "submissions": 42},
            {"dimension": 50, "submissions": 38},
            {"dimension": 100, "submissions": 30}
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
        "totalSubmissions": 110,
        "totalSolved": 68,
        "acceptanceRate": 61.8,
        "submissionDate": datetime(2017, 10, 5),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "298",
        "name": "Sphere Function Optimization",
        "description": "The Sphere function is one of the simplest optimization test functions. It is continuous, convex and unimodal. The function is usually evaluated on the hypercube x_i ∈ [-5.12, 5.12], for all i = 1, ..., D. This is an easy optimization problem and is often used to test the convergence speed of optimization algorithms.",
        "owner": "BB Rose, MIT",
        "ownerName": "BB Rose",
        "ownerInstitution": "MIT",
        "cc": "🇺🇸",
        "level": "Easy",
        "type": "Unimodal, Continuous, Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "simple", "convex"],
        "dimensions": [
            {"dimension": 20, "submissions": 55},
            {"dimension": 50, "submissions": 48},
            {"dimension": 100, "submissions": 40}
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
        "totalSubmissions": 143,
        "totalSolved": 98,
        "acceptanceRate": 68.5,
        "submissionDate": datetime(2017, 9, 20),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "297",
        "name": "Griewank Function Minimization",
        "description": "The Griewank function has many widespread local minima, which are regularly distributed. The complexity is shown in the zoomed-in plots. The function has a product term that introduces interdependence among the variables. The aim is to find the global minimum.",
        "owner": "RS Joes, UC Berkeley",
        "ownerName": "RS Joes",
        "ownerInstitution": "UC Berkeley",
        "cc": "🇺🇸",
        "level": "Medium",
        "type": "Multi-Modal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "multi-modal", "interdependent"],
        "dimensions": [
            {"dimension": 20, "submissions": 32},
            {"dimension": 50, "submissions": 28},
            {"dimension": 100, "submissions": 22}
        ],
        "fitnessFunction": {
            "formula": "f(x) = 1 + (1/4000)∑x_i² - ∏cos(x_i/√i)",
            "constraint": "subject to -600 ≤ x_i ≤ 600. The global minimum is at x* = (0,...,0) with f(x*) = 0.",
            "codeFiles": {
                "python": "griewank.py",
                "java": "Griewank.java",
                "cpp": "griewank.cpp",
                "c": "griewank.c"
            }
        },
        "totalSubmissions": 82,
        "totalSolved": 38,
        "acceptanceRate": 46.3,
        "submissionDate": datetime(2017, 12, 1),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "problemId": "296",
        "name": "Levy Function Optimization",
        "description": "The Levy function is a multimodal, continuous, non-separable function. It is a challenging optimization problem with many local minima. The function is named after the mathematician Paul Lévy and is commonly used to test optimization algorithms.",
        "owner": "KK James, Oxford University",
        "ownerName": "KK James",
        "ownerInstitution": "Oxford University",
        "cc": "🇬🇧",
        "level": "Hard",
        "type": "Multi-Modal, Continuous, Non-Separable",
        "category": "Benchmark Functions",
        "tags": ["optimization", "challenging", "levy"],
        "dimensions": [
            {"dimension": 20, "submissions": 18},
            {"dimension": 50, "submissions": 14},
            {"dimension": 100, "submissions": 10}
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
        "totalSubmissions": 42,
        "totalSolved": 15,
        "acceptanceRate": 35.7,
        "submissionDate": datetime(2018, 2, 14),
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

# Insert problems into database
try:
    # Clear existing problems (optional - comment out if you want to keep existing data)
    # db.problems.delete_many({})
    
    # Insert new problems
    result = db.problems.insert_many(problems_data)
    print(f"✓ Successfully inserted {len(result.inserted_ids)} problems!")
    
    # Display inserted problems
    print("\nInserted Problems:")
    for problem in problems_data:
        print(f"  - {problem['problemId']}: {problem['name']} ({problem['level']})")
    
    print(f"\nTotal problems in database: {db.problems.count_documents({})}")
    
except Exception as e:
    print(f"✗ Error inserting problems: {e}")

finally:
    client.close()
    print("\n✓ Database connection closed")
