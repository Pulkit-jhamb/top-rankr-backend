#!/usr/bin/env python3
"""
Test script for admin workflow:
1. Submit a contribution (as student)
2. Admin accepts contribution and creates problem
3. Admin adds problem to existing contest
4. Admin creates new contest with problems
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:3999/api"

# Test credentials (you'll need to create these in your DB or use existing ones)
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "password123"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"

def login(email, password, role="student"):
    """Login and return token"""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password,
        "role": role
    })
    if resp.status_code == 200:
        return resp.json()["token"]
    else:
        print(f"❌ Login failed for {email}: {resp.text}")
        return None

def test_submit_contribution(student_token):
    """Test: Student submits a problem contribution"""
    print("\n📝 TEST 1: Submit Contribution")
    
    contribution = {
        "name": "Test Sphere Function",
        "level": "Easy",
        "description": "Simple sphere function for testing: sum of squares of all variables",
        "fitnessFormula": "f(x) = sum(xi^2) for i=1..n",
        "constraint": "-5.12 ≤ xi ≤ 5.12"
    }
    
    resp = requests.post(
        f"{BASE_URL}/problems/contribute",
        json=contribution,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    if resp.status_code == 201:
        contrib_id = resp.json()["id"]
        print(f"✅ Contribution submitted! ID: {contrib_id}")
        return contrib_id
    else:
        print(f"❌ Failed to submit contribution: {resp.text}")
        return None

def test_list_contributions(admin_token):
    """Test: Admin lists pending contributions"""
    print("\n📋 TEST 2: List Pending Contributions")
    
    resp = requests.get(
        f"{BASE_URL}/admin/contributions",
        params={"status": "pending"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if resp.status_code == 200:
        contribs = resp.json()["data"]
        print(f"✅ Found {len(contribs)} pending contribution(s)")
        if contribs:
            print(f"   First: {contribs[0]['name']}")
            return contribs[0]["_id"]
        return None
    else:
        print(f"❌ Failed to list contributions: {resp.text}")
        return None

def test_accept_contribution(admin_token, contrib_id):
    """Test: Admin accepts contribution and creates problem"""
    print("\n✅ TEST 3: Accept Contribution & Create Problem")
    
    accept_data = {
        "problemId": f"TEST-{datetime.now().strftime('%H%M%S')}",
        "level": "Easy",
        "type": "Minimization",
        "category": "Test Functions",
        "dimensions": [10, 20, 30],
        "boundsMin": -5.12,
        "boundsMax": 5.12,
        "globalMinimum": 0,
        "formula": "np.sum(x**2)",
        "constraint": "-5.12 ≤ xi ≤ 5.12"
    }
    
    resp = requests.post(
        f"{BASE_URL}/admin/contributions/{contrib_id}/accept",
        json=accept_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if resp.status_code == 200:
        print(f"✅ Contribution accepted! Problem ID: {accept_data['problemId']}")
        return accept_data['problemId']
    else:
        print(f"❌ Failed to accept contribution: {resp.text}")
        return None

def test_create_contest(admin_token, problem_ids):
    """Test: Admin creates new contest with problems"""
    print("\n🏆 TEST 4: Create Contest with Problems")
    
    now = datetime.now()
    contest_data = {
        "eventId": f"TEST-CONTEST-{now.strftime('%H%M%S')}",
        "name": "Test Optimization Contest",
        "organizer": "Test Lab",
        "type": "Open",
        "status": "active",
        "prize": 1000,
        "startDate": now.isoformat(),
        "endDate": (now + timedelta(days=7)).isoformat(),
        "problems": problem_ids,
        "eventCode": ""
    }
    
    resp = requests.post(
        f"{BASE_URL}/admin/contests",
        json=contest_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if resp.status_code == 201:
        contest_id = resp.json()["id"]
        print(f"✅ Contest created! Event ID: {contest_data['eventId']}")
        print(f"   Problems: {', '.join(problem_ids)}")
        return contest_data['eventId']
    else:
        print(f"❌ Failed to create contest: {resp.text}")
        return None

def test_add_problem_to_contest(admin_token, contest_id, problem_id):
    """Test: Admin adds problem to existing contest"""
    print("\n➕ TEST 5: Add Problem to Existing Contest")
    
    resp = requests.post(
        f"{BASE_URL}/admin/contests/{contest_id}/add-problem",
        json={"problemId": problem_id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if resp.status_code == 200:
        print(f"✅ Problem {problem_id} added to contest {contest_id}")
        return True
    else:
        print(f"❌ Failed to add problem to contest: {resp.text}")
        return False

def test_create_problem_directly(admin_token):
    """Test: Admin creates problem directly (not from contribution)"""
    print("\n🔧 TEST 6: Create Problem Directly")
    
    problem_data = {
        "problemId": f"DIRECT-{datetime.now().strftime('%H%M%S')}",
        "name": "Direct Test Problem",
        "level": "Medium",
        "type": "Minimization",
        "category": "Direct Creation",
        "tags": ["test", "direct"],
        "description": "Problem created directly by admin",
        "status": "active",
        "dimensions": [10, 20],
        "formula": "np.sum(x**2)",
        "constraint": "-10 ≤ xi ≤ 10",
        "boundsMin": -10,
        "boundsMax": 10,
        "globalMinimum": 0
    }
    
    resp = requests.post(
        f"{BASE_URL}/admin/problems",
        json=problem_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if resp.status_code == 201:
        print(f"✅ Problem created directly! ID: {problem_data['problemId']}")
        return problem_data['problemId']
    else:
        print(f"❌ Failed to create problem: {resp.text}")
        return None

def main():
    print("=" * 60)
    print("🧪 ADMIN WORKFLOW TEST SUITE")
    print("=" * 60)
    
    # Login
    print("\n🔐 Logging in...")
    student_token = login(STUDENT_EMAIL, STUDENT_PASSWORD, "student")
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")
    
    if not student_token or not admin_token:
        print("\n❌ Login failed. Please ensure test users exist in DB:")
        print(f"   Student: {STUDENT_EMAIL}")
        print(f"   Admin: {ADMIN_EMAIL}")
        return
    
    print("✅ Both users logged in successfully")
    
    # Test workflow
    problem_ids = []
    
    # 1. Submit contribution
    contrib_id = test_submit_contribution(student_token)
    
    # 2. List contributions
    if not contrib_id:
        contrib_id = test_list_contributions(admin_token)
    
    # 3. Accept contribution
    if contrib_id:
        problem_id = test_accept_contribution(admin_token, contrib_id)
        if problem_id:
            problem_ids.append(problem_id)
    
    # 4. Create problem directly
    direct_problem_id = test_create_problem_directly(admin_token)
    if direct_problem_id:
        problem_ids.append(direct_problem_id)
    
    # 5. Create contest with problems
    if problem_ids:
        contest_id = test_create_contest(admin_token, problem_ids)
        
        # 6. Add another problem to the contest
        if contest_id and len(problem_ids) > 1:
            test_add_problem_to_contest(admin_token, contest_id, problem_ids[1])
    
    print("\n" + "=" * 60)
    print("✅ TEST SUITE COMPLETED")
    print("=" * 60)
    print("\n📊 Summary:")
    print(f"   - Contributions submitted: {1 if contrib_id else 0}")
    print(f"   - Problems created: {len(problem_ids)}")
    print(f"   - Contests created: {1 if 'contest_id' in locals() else 0}")
    print("\n💡 Next steps:")
    print("   1. Check admin panel → Contributions tab")
    print("   2. Verify problem appears in Problems page")
    print("   3. Check contest has all problems")
    print("   4. Try typing in Add Contest/Problem forms (should not lose focus)")

if __name__ == "__main__":
    main()
