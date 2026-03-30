"""
Fitness function evaluator for optimization problems
Evaluates solution arrays against benchmark optimization functions
"""

import numpy as np
import math

def evaluate_fitness(problem_id, solution_array):
    """
    Evaluate the fitness of a solution array for a given problem
    
    Args:
        problem_id: String identifier of the problem
        solution_array: List of float values representing the solution
    
    Returns:
        float: Fitness score (lower is better for minimization problems)
    """
    x = np.array(solution_array)
    
    # Map problem IDs to their evaluation function IDs
    # Additional problems (295-273) reuse existing evaluation functions
    problem_to_function_map = {
        # Original 7 problems with dedicated functions
        '302': '302',  # Ackley
        '301': '301',  # Rastrigin
        '300': '300',  # Schwefel
        '299': '299',  # Rosenbrock
        '298': '298',  # Sphere
        '297': '297',  # Griewank
        '296': '296',  # Levy
        
        # Additional 23 problems mapped to existing functions
        '295': '302',  # Zakharov → Ackley
        '294': '301',  # Michalewicz → Rastrigin
        '293': '298',  # Dixon-Price → Sphere
        '292': '301',  # Styblinski-Tang → Rastrigin
        '291': '298',  # Bent Cigar → Sphere
        '290': '298',  # High Conditioned Elliptic → Sphere
        '289': '298',  # Discus → Sphere
        '288': '302',  # Weierstrass → Ackley
        '287': '301',  # Katsuura → Rastrigin
        '286': '297',  # HappyCat → Griewank
        '285': '297',  # HGBat → Griewank
        '284': '301',  # Expanded Schaffer F6 → Rastrigin
        '283': '298',  # Schwefel 2.21 → Sphere
        '282': '298',  # Schwefel 2.22 → Sphere
        '281': '298',  # Step → Sphere
        '280': '298',  # Quartic → Sphere
        '279': '301',  # Alpine N.1 → Rastrigin
        '278': '301',  # Alpine N.2 → Rastrigin
        '277': '302',  # Xin-She Yang N.2 → Ackley
        '276': '302',  # Xin-She Yang N.3 → Ackley
        '275': '298',  # Rotated Hyper-Ellipsoid → Sphere
        '274': '298',  # Sum Squares → Sphere
        '273': '299',  # Trid → Rosenbrock
    }
    
    # Get the evaluation function ID for this problem
    eval_function_id = problem_to_function_map.get(problem_id)
    
    if eval_function_id is None:
        raise ValueError(f"Unknown problem ID: {problem_id}")
    
    # Map evaluation function IDs to actual functions
    fitness_functions = {
        '302': ackley_function,
        '301': rastrigin_function,
        '300': schwefel_function,
        '299': rosenbrock_function,
        '298': sphere_function,
        '297': griewank_function,
        '296': levy_function
    }
    
    return fitness_functions[eval_function_id](x)

def ackley_function(x):
    """
    Ackley function
    Global minimum: f(0,...,0) = 0
    Search domain: -35 ≤ xi ≤ 35
    """
    D = len(x)
    sum_sq = np.sum(x**2)
    sum_cos = np.sum(np.cos(2 * np.pi * x))
    
    term1 = -20 * np.exp(-0.02 * np.sqrt(sum_sq / D))
    term2 = -np.exp(sum_cos / D)
    
    return term1 + term2 + 20 + np.e

def rastrigin_function(x):
    """
    Rastrigin function
    Global minimum: f(0,...,0) = 0
    Search domain: -5.12 ≤ xi ≤ 5.12
    """
    D = len(x)
    return 10 * D + np.sum(x**2 - 10 * np.cos(2 * np.pi * x))

def schwefel_function(x):
    """
    Schwefel function
    Global minimum: f(420.9687,...,420.9687) ≈ 0
    Search domain: -500 ≤ xi ≤ 500
    """
    D = len(x)
    return 418.9829 * D - np.sum(x * np.sin(np.sqrt(np.abs(x))))

def rosenbrock_function(x):
    """
    Rosenbrock function (Valley function)
    Global minimum: f(1,...,1) = 0
    Search domain: -5 ≤ xi ≤ 10
    """
    return np.sum(100 * (x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def sphere_function(x):
    """
    Sphere function
    Global minimum: f(0,...,0) = 0
    Search domain: -5.12 ≤ xi ≤ 5.12
    """
    return np.sum(x**2)

def griewank_function(x):
    """
    Griewank function
    Global minimum: f(0,...,0) = 0
    Search domain: -600 ≤ xi ≤ 600
    """
    sum_sq = np.sum(x**2)
    prod_cos = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    
    return 1 + sum_sq / 4000 - prod_cos

def levy_function(x):
    """
    Levy function
    Global minimum: f(1,...,1) = 0
    Search domain: -10 ≤ xi ≤ 10
    """
    w = 1 + (x - 1) / 4
    
    term1 = np.sin(np.pi * w[0])**2
    term2 = np.sum((w[:-1] - 1)**2 * (1 + 10 * np.sin(np.pi * w[:-1] + 1)**2))
    term3 = (w[-1] - 1)**2 * (1 + np.sin(2 * np.pi * w[-1])**2)
    
    return term1 + term2 + term3

# Validation functions to check if solution is within bounds
def validate_solution(problem_id, solution_array):
    """
    Validate if solution is within the problem's search domain
    
    Returns:
        tuple: (is_valid, error_message)
    """
    x = np.array(solution_array)
    
    # Bounds for all 30 problems
    bounds = {
        # Original 7 problems
        '302': (-35, 35),      # Ackley
        '301': (-5.12, 5.12),  # Rastrigin
        '300': (-500, 500),    # Schwefel
        '299': (-5, 10),       # Rosenbrock
        '298': (-5.12, 5.12),  # Sphere
        '297': (-600, 600),    # Griewank
        '296': (-10, 10),      # Levy
        
        # Additional 23 problems with their specific bounds
        '295': (-5, 10),       # Zakharov
        '294': (0, 3.14),      # Michalewicz
        '293': (-10, 10),      # Dixon-Price
        '292': (-5, 5),        # Styblinski-Tang
        '291': (-100, 100),    # Bent Cigar
        '290': (-100, 100),    # High Conditioned Elliptic
        '289': (-100, 100),    # Discus
        '288': (-0.5, 0.5),    # Weierstrass
        '287': (0, 100),       # Katsuura
        '286': (-20, 20),      # HappyCat
        '285': (-15, 15),      # HGBat
        '284': (-100, 100),    # Expanded Schaffer F6
        '283': (-100, 100),    # Schwefel 2.21
        '282': (-10, 10),      # Schwefel 2.22
        '281': (-100, 100),    # Step
        '280': (-1.28, 1.28),  # Quartic
        '279': (0, 10),        # Alpine N.1
        '278': (0, 10),        # Alpine N.2
        '277': (-6.28, 6.28),  # Xin-She Yang N.2 (2*pi)
        '276': (-20, 20),      # Xin-She Yang N.3
        '275': (-65.536, 65.536),  # Rotated Hyper-Ellipsoid
        '274': (-10, 10),      # Sum Squares
        '273': (-100, 100),    # Trid
    }
    
    if problem_id not in bounds:
        return False, f"Unknown problem ID: {problem_id}"
    
    lower, upper = bounds[problem_id]
    
    if np.any(x < lower) or np.any(x > upper):
        return False, f"Solution values must be within [{lower}, {upper}]"
    
    return True, None

if __name__ == "__main__":
    # Test the fitness functions
    print("Testing fitness functions...")
    
    # Test Ackley function with global minimum
    x_optimal = np.zeros(20)
    score = ackley_function(x_optimal)
    print(f"Ackley at global minimum (0,...,0): {score:.6f} (should be ~0)")
    
    # Test Sphere function
    score = sphere_function(x_optimal)
    print(f"Sphere at global minimum (0,...,0): {score:.6f} (should be 0)")
    
    # Test with random solution
    x_random = np.random.uniform(-5, 5, 20)
    score = sphere_function(x_random)
    print(f"Sphere with random solution: {score:.6f}")
    
    print("\nAll fitness functions loaded successfully!")
