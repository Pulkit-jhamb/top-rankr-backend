"""
Script to seed 10 original TopRanker fitness function problems into MongoDB.
These are custom-designed problems — not available on Google, GPT, or any benchmark library.
Global minima (f*) are stored server-side only and hidden from participants.
Run once to populate the problems collection.
"""

import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone
import math

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://TopRankr:TopRankr@cluster0.yzozjgg.mongodb.net/?appName=Cluster0"
)

try:
    client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    # Ping to confirm connection before proceeding
    client.admin.command("ping")
    db = client['topranker']
    print("✓ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    exit(1)

# ──────────────────────────────────────────────
# 10 Original TopRanker Fitness Functions
# ──────────────────────────────────────────────
problems_data = [
    {
        "problemId": "TR-001",
        "name": "Cascading Tide",
        "description": (
            "Each variable is circularly coupled to its neighbour through a sine interaction term. "
            "The landscape appears smoothly wavy from a distance but conceals a single tight basin of attraction. "
            "Algorithms that treat variables as independent will converge extremely slowly. "
            "The circular coupling (x_{D+1} = x_1) means boundary variables interact with the first, "
            "making the problem non-separable throughout the entire domain. "
            "Effective solutions require strategies that model inter-variable dependencies, "
            "such as covariance-based or ensemble learning approaches."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Easy",
        "type": "Unimodal, Coupled Sinusoidal, Smooth, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["coupled", "sinusoidal", "non-separable", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "f(x) = sum_{i=1}^{D} [ (x_i - 1/i)^2 + 0.3 * sin(3*pi * x_i * x_{i+1}) ]\n"
                "where x_{D+1} = x_1  (circular coupling)\n"
                "Domain: x_i in [-5, 5]\n"
                "Global minimum: f* hidden (known to platform only)"
            ),
            "constraint": "x_i in [-5, 5] for all i. No additional constraints.",
            "bounds": {"min": -5, "max": 5},
            "trap": "Sine coupling terms create misleading gradient directions near the centre.",
            "globalMinimumHint": "Near x_i ~ 1/i for each i, but exact f* is withheld.",
            "codeFiles": {
                "python": "TR001_cascading_tide.py",
                "java": "TR001CascadingTide.java",
                "cpp": "TR001_cascading_tide.cpp",
                "c": "TR001_cascading_tide.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-002",
        "name": "Phantom Plateau",
        "description": (
            "Across 90% of the search space the function surface is nearly flat, "
            "with gradient magnitudes indistinguishable from zero. "
            "A narrow, steep funnel then drops sharply to the global minimum. "
            "Gradient-based and quasi-Newton methods stall on the plateau and never reach the funnel. "
            "Only algorithms with strong exploration diversity — random restarts, large population spread, "
            "or Lévy-flight-style jumps — can accidentally land close enough to the funnel to detect it. "
            "A strong test of exploration vs exploitation balance."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Easy",
        "type": "Unimodal, Flat Region, Gradient-Sparse, Deceptive",
        "category": "Original TR Functions",
        "tags": ["plateau", "gradient-sparse", "exploration", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "f(x) = sigmoid(0.5 * sum(x_i^2))  -  exp(-0.01 * sum((x_i - 2)^2))\n"
                "where sigmoid(z) = 1 / (1 + exp(-z))\n"
                "Domain: x_i in [-10, 10]\n"
                "Global minimum: f* hidden"
            ),
            "constraint": "x_i in [-10, 10] for all i. No additional constraints.",
            "bounds": {"min": -10, "max": 10},
            "trap": "Enormous flat plateau — gradient signal is near zero across most of the domain.",
            "globalMinimumHint": "Global min is near x_i = 2 for all i, but f* is withheld.",
            "codeFiles": {
                "python": "TR002_phantom_plateau.py",
                "java": "TR002PhantomPlateau.java",
                "cpp": "TR002_phantom_plateau.cpp",
                "c": "TR002_phantom_plateau.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-003",
        "name": "Spiral Sink",
        "description": (
            "This function combines a rotated ellipsoidal base with angular sinusoidal ridges defined "
            "in polar coordinates of consecutive variable pairs. The ridges spiral around the origin, "
            "making any axis-aligned search strategy (standard PSO, basic GA without crossover rotation) "
            "completely ineffective — moves along x or y axes always cross ridges rather than following valleys. "
            "Solvers must use rotationally invariant operators such as CMA-ES or rotated differential evolution "
            "to navigate the spiral structure toward the sink at the origin."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Medium",
        "type": "Multimodal, Rotation-Dependent, Asymmetric, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["rotation", "polar", "multimodal", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "For each consecutive pair (x_i, x_{i+1}):\n"
                "  theta_i = arctan(x_{i+1} / (x_i + 1e-9))\n"
                "  r_i     = sqrt(x_i^2 + x_{i+1}^2)\n"
                "f(x) = sum_{i=1}^{D-1} [ r_i^2 + 2*sin^2(3*theta_i + r_i) + 0.1*(x_i - x_{i+1})^2 ]\n"
                "Domain: x_i in [-6, 6]\n"
                "Global minimum: x_i = 0 for all i,  f* hidden"
            ),
            "constraint": "x_i in [-6, 6] for all i. No additional constraints.",
            "bounds": {"min": -6, "max": 6},
            "trap": "Axis-aligned moves always cross spiral ridges — rotationally invariant operators required.",
            "globalMinimumHint": "Global min is at the origin, but f* exact value is withheld.",
            "codeFiles": {
                "python": "TR003_spiral_sink.py",
                "java": "TR003SpiralSink.java",
                "cpp": "TR003_spiral_sink.cpp",
                "c": "TR003_spiral_sink.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-004",
        "name": "Mirage Basin",
        "description": (
            "Three strong false basins are strategically embedded in the landscape. "
            "In early iterations, these false basins exhibit lower function values at their rims "
            "than the true global minimum appears to offer from a distance, luring most population-based "
            "algorithms into premature convergence. Only sustained long-range exploration beyond 200 iterations "
            "reveals that the true basin is deeper. Algorithms with aggressive early exploitation "
            "(greedy selection, low mutation, high elitism) will reliably fail. "
            "Tests diversity-preservation mechanisms under deceptive fitness landscapes."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Medium",
        "type": "Deceptive, False Global Attractors, Multimodal, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["deceptive", "false-minima", "multimodal", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "A = sum(x_i^2)\n"
                "B = sum(cos(2*pi*x_i / 3))\n"
                "C = sum(sin(pi*x_i) * x_{i+1})   [circular: x_{D+1} = x_1]\n"
                "f(x) = A/D  -  1.5*exp(-0.1*A)  +  0.8*B  +  0.4*|C|\n"
                "Domain: x_i in [-8, 8]\n"
                "Global minimum: f* hidden (near-origin cluster)"
            ),
            "constraint": "x_i in [-8, 8] for all i. No additional constraints.",
            "bounds": {"min": -8, "max": 8},
            "trap": "3 false basins look better than the true minimum in early search — only long exploration reveals truth.",
            "globalMinimumHint": "True minimum is near the origin cluster, exact location withheld.",
            "codeFiles": {
                "python": "TR004_mirage_basin.py",
                "java": "TR004MirageBasin.java",
                "cpp": "TR004_mirage_basin.cpp",
                "c": "TR004_mirage_basin.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-005",
        "name": "Recursive Ripple",
        "description": (
            "The fitness landscape is constructed by superimposing cosine waves at four exponentially "
            "increasing frequency levels (scales 1, 2, 4, 8), producing a self-similar, fractal-like surface. "
            "At every zoom level the landscape looks structurally identical — there is no dominant scale "
            "an algorithm can exploit. Coarse-grained search finds the right region but cannot pinpoint "
            "the minimum; fine-grained local search finds a minimum at the wrong scale. "
            "Only multi-resolution algorithms that simultaneously operate at multiple scales — "
            "such as memetic algorithms or multi-swarm PSO — are effective."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Medium",
        "type": "Multimodal, Self-Similar, Fractal-Like, Separable",
        "category": "Original TR Functions",
        "tags": ["fractal", "multi-scale", "multimodal", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "f(x) = sum_{k=1}^{4} [ (1/2^k) * sum_{i=1}^{D} cos(2^k * pi * x_i + k) ]\n"
                "       + 0.05 * sum(x_i^2)\n"
                "Domain: x_i in [-4, 4]\n"
                "Global minimum: f* hidden\n"
                "Warning: x_i = 0 for all i is a LOCAL minimum, not the global one."
            ),
            "constraint": "x_i in [-4, 4] for all i. No additional constraints.",
            "bounds": {"min": -4, "max": 4},
            "trap": "Fractal-like surface — same structure at every resolution. x=0 is a decoy local min.",
            "globalMinimumHint": "Global min location is non-obvious and withheld.",
            "codeFiles": {
                "python": "TR005_recursive_ripple.py",
                "java": "TR005RecursiveRipple.java",
                "cpp": "TR005_recursive_ripple.cpp",
                "c": "TR005_recursive_ripple.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-006",
        "name": "Tidal Lock",
        "description": (
            "The unconstrained global minimum of the base function lies well outside the feasible region. "
            "A sharp quadratic penalty wall forces the true constrained optimum onto the boundary where "
            "two constraints simultaneously become active. This boundary region is geometrically steep and narrow. "
            "Algorithms that ignore constraints or handle them with soft penalties will repeatedly be pushed "
            "into infeasible space and penalised. Only algorithms with proper constraint-handling — "
            "epsilon-constraint, feasibility tournaments, or Lagrangian relaxation — can find the boundary optimum. "
            "A critical test for real-world constrained optimization."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Hard",
        "type": "Constrained, Penalty-Heavy, Coupled, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["constrained", "penalty", "boundary", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "Objective:\n"
                "  f(x) = sum((x_i - 3)^2) + sum(sin(x_i * x_{i+1}))\n"
                "Subject to:\n"
                "  g1: sum(x_i^2) <= D * 4\n"
                "  g2: |x_i - x_{i+1}| <= 1.5  for all i = 1..D-1\n"
                "Penalty (applied if violated):\n"
                "  f = f + 1e5 * max(0, g1_violation)^2\n"
                "      + 1e5 * sum(max(0, g2_violation_i)^2)\n"
                "Domain: x_i in [-7, 7]\n"
                "Global minimum: f* hidden (on constraint boundary)"
            ),
            "constraint": "x_i in [-7, 7]. Two inequality constraints active at optimum.",
            "bounds": {"min": -7, "max": 7},
            "trap": "True optimum is on the constraint boundary — interior search always misses it.",
            "globalMinimumHint": "Optimum lies where both g1 and g2 are simultaneously active. f* withheld.",
            "codeFiles": {
                "python": "TR006_tidal_lock.py",
                "java": "TR006TidalLock.java",
                "cpp": "TR006_tidal_lock.cpp",
                "c": "TR006_tidal_lock.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-007",
        "name": "Vortex Core",
        "description": (
            "An extremely ill-conditioned ellipsoidal function (condition number ~10^5) is combined with "
            "a fixed rotation matrix (seeded per dimension D) and a multimodal sinusoidal overlay. "
            "The rotation matrix is provided in the problem download and is different for D=20, D=50, D=100. "
            "Because the elongated basin does not align with any standard coordinate axis, "
            "every axis-aligned algorithm (coordinate descent, axis-aligned PSO, standard DE) fails entirely. "
            "The sinusoidal overlay adds local optima along the elongated basin, preventing simple "
            "gradient descent from reaching the end. Requires CMA-ES or rotation-aware operators."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Hard",
        "type": "Multimodal, Rotation-Dependent, Ill-Conditioned, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["ill-conditioned", "rotation", "vortex", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "R  = fixed rotation matrix  (numpy seed=42, shape DxD — download from problem page)\n"
                "y  = R @ x\n"
                "f(x) = y[0]^2  +  1e5 * sum(y[1:]^2)  +  sum(0.5 * sin(4*pi*y_i) * y_i^2)\n"
                "Domain: x_i in [-5, 5]\n"
                "Global minimum: f* hidden"
            ),
            "constraint": "x_i in [-5, 5] for all i. Rotation matrix R must be downloaded.",
            "bounds": {"min": -5, "max": 5},
            "trap": "Condition number ~10^5 + rotation hides basin direction from axis-aligned solvers.",
            "globalMinimumHint": "Global min is near origin in rotated space. Exact f* withheld.",
            "codeFiles": {
                "python": "TR007_vortex_core.py",
                "java": "TR007VortexCore.java",
                "cpp": "TR007_vortex_core.cpp",
                "c": "TR007_vortex_core.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-008",
        "name": "Hollow Crown",
        "description": (
            "The global minimum does not exist at a single point — it lies along a D-dimensional hyper-ring "
            "of radius sqrt(D). Most algorithms detect the ring rapidly and converge onto it, "
            "but then drift around it indefinitely without settling. "
            "A subtle, low-weight symmetry-breaking term (0.01 * (x_1 - sqrt(D)/2)^2) selects exactly "
            "one point on the ring as the true global minimum, but this term is small enough that "
            "algorithms routinely overlook it and treat any ring point as equally good. "
            "Tests whether an algorithm can exploit weak secondary signals while maintaining ring-level convergence."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Hard",
        "type": "Multimodal, Ring-Shaped Optimum, Symmetry-Breaking, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["ring-optimum", "symmetry", "multimodal", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "R_target = sqrt(D)\n"
                "r(x)     = sqrt(sum(x_i^2))\n"
                "f(x) = (r(x) - R_target)^4\n"
                "       + 0.1 * sum_{i=1}^{D-1} (x_i - x_{i+1})^2\n"
                "       + 0.01 * (x_1 - sqrt(D)/2)^2\n"
                "Domain: x_i in [-8, 8]\n"
                "Global minimum: f* hidden (single point on the hyper-ring)"
            ),
            "constraint": "x_i in [-8, 8] for all i. No additional constraints.",
            "bounds": {"min": -8, "max": 8},
            "trap": "Optimum is on a ring — algorithms converge to the ring but drift along it. Symmetry breaker is tiny and easy to miss.",
            "globalMinimumHint": "Exact point on ring and f* are withheld. Symmetry breaker involves x_1.",
            "codeFiles": {
                "python": "TR008_hollow_crown.py",
                "java": "TR008HollowCrown.java",
                "cpp": "TR008_hollow_crown.cpp",
                "c": "TR008_hollow_crown.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-009",
        "name": "Phase Shift Labyrinth",
        "description": (
            "The sinusoidal frequency and phase of each variable scale with D, meaning the landscape "
            "is structurally different for D=20, D=50, and D=100. A solution that performs well at D=20 "
            "is not just unhelpful at D=100 — it is actively misleading, scoring worse than random initialisation. "
            "Participants cannot reuse strategies or warm-start solutions across dimensions. "
            "Each dimension must be treated as a completely independent problem. "
            "A direct challenge to any transfer-learning or cross-dimensional warm-start approach. "
            "Also tests whether solvers can handle variable-frequency landscapes without fixed-step assumptions."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Hard",
        "type": "Multimodal, Phase-Coupled, Dimension-Variant, Non-Separable",
        "category": "Original TR Functions",
        "tags": ["phase-shift", "dimension-variant", "multimodal", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "phi_i = 2*pi*i / D          (phase shift, depends on D)\n"
                "omega_i = 1 + i/D           (frequency scale, depends on D)\n"
                "f(x) = sum_{i=1}^{D} [ x_i^2 * (1 + 0.5*sin(omega_i * x_i + phi_i)) ]\n"
                "       + 0.3 * (sum(x_i) / D)^2\n"
                "Domain: x_i in [-6, 6]\n"
                "Global minimum: f* ~ 0 but location shifts per D — all three must be solved independently."
            ),
            "constraint": "x_i in [-6, 6] for all i. No additional constraints.",
            "trap": "Phase and frequency shift with D — D=20 solution actively misleads D=100 search.",
            "globalMinimumHint": "Near-zero but exact location varies by D. f* for each D is withheld.",
            "codeFiles": {
                "python": "TR009_phase_shift_labyrinth.py",
                "java": "TR009PhaseShiftLabyrinth.java",
                "cpp": "TR009_phase_shift_labyrinth.cpp",
                "c": "TR009_phase_shift_labyrinth.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },

    {
        "problemId": "TR-010",
        "name": "Abyss Gate",
        "description": (
            "The most adversarial function in the TopRanker original set. "
            "It is specifically designed so that the gradient direction, the swarm centroid attraction, "
            "and the top-10 local optima discovered by any standard algorithm all point away from "
            "the true global minimum. The mean-variance structure causes high-fitness solutions to cluster "
            "in a deception zone near the boundary of the domain, while the true minimum lies in a "
            "low-variance, near-zero-mean region that looks uninteresting at first glance. "
            "Only algorithms with aggressive diversity preservation, random long-range jumps, "
            "or explicit deception-resistance (e.g. fitness sharing, novelty search) can escape. "
            "Highest difficulty in the set — suitable as the final competition problem."
        ),
        "owner": "TopRanker Team",
        "ownerName": "TopRanker",
        "ownerInstitution": "TopRanker.com",
        "cc": "🌐",
        "level": "Hard",
        "type": "Multimodal, Fully Deceptive, Non-Separable, Adversarial",
        "category": "Original TR Functions",
        "tags": ["adversarial", "deceptive", "non-separable", "original"],
        "dimensions": [
            {"dimension": 20,  "submissions": 0},
            {"dimension": 50,  "submissions": 0},
            {"dimension": 100, "submissions": 0}
        ],
        "fitnessFunction": {
            "formula": (
                "S = sum(x_i) / D                              (mean)\n"
                "Q = sum((x_i - S)^2)                         (variance)\n"
                "T = sum(sin(x_i^2 - x_{i+1}))               (circular: x_{D+1}=x_1)\n"
                "U = |sum((-1)^i * x_i)|                      (alternating sum)\n"
                "f(x) = -exp(-0.5*Q) * cos(2*pi*S)\n"
                "       + 0.5 * T\n"
                "       + 0.1 * U\n"
                "Domain: x_i in [-pi, pi]\n"
                "Global minimum: f* hidden — location is deeply non-intuitive."
            ),
            "constraint": "x_i in [-pi, pi] for all i. No additional constraints.",
            "bounds": {"min": -math.pi, "max": math.pi},
            "trap": "Gradient, swarm centroid, and top local optima all point AWAY from global min. True min is in a deception shadow.",
            "globalMinimumHint": "True min is in a low-variance, near-zero-mean region. Exact f* and location withheld.",
            "codeFiles": {
                "python": "TR010_abyss_gate.py",
                "java": "TR010AbyssGate.java",
                "cpp": "TR010_abyss_gate.cpp",
                "c": "TR010_abyss_gate.c"
            }
        },
        "totalSubmissions": 0,
        "totalSolved": 0,
        "acceptanceRate": 0.0,
        "submissionDate": datetime(2024, 1, 1),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
]

# ──────────────────────────────────────────────
# Insert into MongoDB
# ──────────────────────────────────────────────
try:
    result = db.problems.insert_many(problems_data)
    print(f"✓ Successfully inserted {len(result.inserted_ids)} original problems!\n")

    print("Inserted Problems:")
    for p in problems_data:
        print(f"  - {p['problemId']}: {p['name']} ({p['level']})")

    print(f"\nTotal problems in database: {db.problems.count_documents({})}")

except Exception as e:
    print(f"✗ Error inserting problems: {e}")

finally:
    client.close()
    print("\n✓ Database connection closed")