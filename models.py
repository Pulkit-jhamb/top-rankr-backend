from datetime import datetime
from bson import ObjectId

class Student:
    @staticmethod
    def create(db, data):
        student = {
            "name": data.get("name"),
            "email": data.get("email").lower(),
            "password": data.get("password"),
            "role": "student",
            "institution": data.get("institution", ""),
            "country": data.get("country", ""),
            "rating": 0,
            "problems_solved": 0,
            "contests_participated": 0,
            "problem_rankings": {},  # Store rankings per problem: {problemId: {rank: int, best_score: float, dimension_ranks: {20: rank, 50: rank, 100: rank}}}
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.students.insert_one(student)
        student["_id"] = result.inserted_id
        return student
    
    @staticmethod
    def find_by_email(db, email):
        return db.students.find_one({"email": email.lower()})
    
    @staticmethod
    def find_by_id(db, student_id):
        return db.students.find_one({"_id": ObjectId(student_id)})
    
    @staticmethod
    def update_stats(db, student_id, problems_solved=None, rating=None):
        update_data = {"updated_at": datetime.utcnow()}
        if problems_solved is not None:
            update_data["problems_solved"] = problems_solved
        if rating is not None:
            update_data["rating"] = rating
        
        return db.students.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": update_data}
        )

class Admin:
    @staticmethod
    def create(db, data):
        admin = {
            "name": data.get("name"),
            "email": data.get("email").lower(),
            "password": data.get("password"),
            "role": "admin",
            "permissions": data.get("permissions", ["manage_contests", "manage_problems", "manage_users"]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = db.admins.insert_one(admin)
        admin["_id"] = result.inserted_id
        return admin
    
    @staticmethod
    def find_by_email(db, email):
        return db.admins.find_one({"email": email.lower()})
    
    @staticmethod
    def find_by_id(db, admin_id):
        return db.admins.find_one({"_id": ObjectId(admin_id)})

class Problem:
    @staticmethod
    def create(db, data):
        """
        Create a new problem in the database
        """
        problem = {
            "problemId": data.get("problemId"),
            "name": data.get("name"),
            "description": data.get("description"),
            "owner": data.get("owner"),
            "ownerName": data.get("ownerName", ""),
            "ownerInstitution": data.get("ownerInstitution", ""),
            "cc": data.get("cc", "🌍"),
            "level": data.get("level", "Medium"),
            "type": data.get("type", "Optimization"),
            "category": data.get("category", "Uncategorized"),
            "tags": data.get("tags", []),
            "dimensions": data.get("dimensions", [
                {"dimension": 20, "submissions": 0},
                {"dimension": 50, "submissions": 0},
                {"dimension": 100, "submissions": 0}
            ]),
            "fitnessFunction": {
                "formula": data.get("formula", ""),
                "constraint": data.get("constraint", ""),
                "codeFiles": data.get("codeFiles", {
                    "python": "",
                    "java": "",
                    "cpp": "",
                    "c": ""
                })
            },
            "totalSubmissions": 0,
            "totalSolved": 0,
            "acceptanceRate": 0.0,
            "submissionDate": data.get("submissionDate", datetime.utcnow()),
            "status": data.get("status", "active"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.problems.insert_one(problem)
        problem["_id"] = result.inserted_id
        return problem
    
    @staticmethod
    def find_by_id(db, problem_id):
        """
        Find problem by problemId (string)
        """
        return db.problems.find_one({"problemId": problem_id})
    
    @staticmethod
    def find_all(db, filters=None, skip=0, limit=10):
        """
        Find all problems with optional filters
        """
        query = filters or {}
        if query.get('level') == 'All':
            query.pop('level')
        
        problems = list(db.problems.find(query).skip(skip).limit(limit).sort("created_at", -1))
        total = db.problems.count_documents(query)
        
        # Add participation counts for each problem
        for problem in problems:
            problem_id = problem.get('problemId')
            
            # Calculate dimension-wise participations
            if 'dimensions' in problem:
                for dim in problem['dimensions']:
                    dimension_value = dim.get('dimension')
                    # Count unique students who have submitted for this dimension
                    dim['submissions'] = db.students.count_documents({
                        f'problem_rankings.{problem_id}.dimension_ranks.{dimension_value}': {'$exists': True}
                    })
            
            # Calculate total problem participations
            problem['totalSubmissions'] = db.students.count_documents({
                f'problem_rankings.{problem_id}.overall_rank': {'$exists': True}
            })
        
        return problems, total
    
    @staticmethod
    def update(db, problem_id, data):
        """
        Update problem details
        """
        update_data = {
            "updated_at": datetime.utcnow()
        }
        
        allowed_fields = [
            "name", "description", "owner", "level", "type", 
            "category", "tags", "dimensions", "fitnessFunction", "status"
        ]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        return db.problems.update_one(
            {"problemId": problem_id},
            {"$set": update_data}
        )
    
    @staticmethod
    def increment_submissions(db, problem_id, dimension=None):
        """
        Increment submission count for a problem
        """
        update_query = {
            "$inc": {"totalSubmissions": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
        
        if dimension:
            update_query["$inc"][f"dimensions.$[elem].submissions"] = 1
            array_filters = [{"elem.dimension": dimension}]
            return db.problems.update_one(
                {"problemId": problem_id},
                update_query,
                array_filters=array_filters
            )
        
        return db.problems.update_one(
            {"problemId": problem_id},
            update_query
        )
    
    @staticmethod
    def delete(db, problem_id):
        """
        Delete a problem (soft delete by setting status to inactive)
        """
        return db.problems.update_one(
            {"problemId": problem_id},
            {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
        )

class Submission:
    @staticmethod
    def create(db, data):
        """
        Create a new submission
        """
        submission = {
            "problemId": data.get("problemId"),
            "userId": data.get("userId"),
            "userEmail": data.get("userEmail"),
            "userName": data.get("userName", ""),
            "code": data.get("code"),
            "language": data.get("language"),
            "dimension": data.get("dimension"),
            "status": "pending",
            "score": None,
            "executionTime": None,
            "memoryUsed": None,
            "testCasesPassed": 0,
            "totalTestCases": 0,
            "errorMessage": None,
            "submittedAt": datetime.utcnow(),
            "evaluatedAt": None
        }
        
        result = db.submissions.insert_one(submission)
        submission["_id"] = result.inserted_id
        return submission
    
    @staticmethod
    def find_by_id(db, submission_id):
        """
        Find submission by ID
        """
        return db.submissions.find_one({"_id": ObjectId(submission_id)})
    
    @staticmethod
    def find_by_user(db, user_id, problem_id=None, limit=10):
        """
        Find submissions by user
        """
        query = {"userId": user_id}
        if problem_id:
            query["problemId"] = problem_id
        
        return list(db.submissions.find(query).sort("submittedAt", -1).limit(limit))
    
    @staticmethod
    def find_by_problem(db, problem_id, dimension=None, status=None, limit=100):
        """
        Find submissions for a problem
        """
        query = {"problemId": problem_id}
        if dimension:
            query["dimension"] = dimension
        if status:
            query["status"] = status
        
        return list(db.submissions.find(query).sort("score", 1).limit(limit))
    
    @staticmethod
    def update_evaluation(db, submission_id, score, status="evaluated", error_message=None):
        """
        Update submission after evaluation
        """
        update_data = {
            "status": status,
            "score": score,
            "evaluatedAt": datetime.utcnow()
        }
        
        if error_message:
            update_data["errorMessage"] = error_message
        
        return db.submissions.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": update_data}
        )
    
    @staticmethod
    def get_leaderboard(db, problem_id, dimension, limit=100):
        """
        Get leaderboard for a problem dimension
        """
        return list(db.submissions.find({
            "problemId": problem_id,
            "dimension": dimension,
            "status": "evaluated",
            "score": {"$ne": None}
        }).sort("score", 1).limit(limit))
    
    @staticmethod
    def get_user_best_score(db, user_id, problem_id, dimension):
        """
        Get user's best score for a problem dimension
        """
        result = db.submissions.find_one({
            "userId": user_id,
            "problemId": problem_id,
            "dimension": dimension,
            "status": "evaluated",
            "score": {"$ne": None}
        }, sort=[("score", 1)])
        
        return result["score"] if result else None
