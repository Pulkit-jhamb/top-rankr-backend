"""
models.py — TopRanker Data Models
Provides CRUD helpers for Student and Admin collections.
"""

from datetime import datetime, timezone
from bson import ObjectId


def _now_utc() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Student:
    COLLECTION = 'students'

    # Required fields for creating a student
    REQUIRED_FIELDS = ('name', 'email', 'password')

    @staticmethod
    def create(db, data: dict) -> dict:
        # FIX: validate required fields before attempting insertion
        missing = [f for f in Student.REQUIRED_FIELDS if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # FIX: datetime.utcnow() is deprecated in Python 3.12+; use timezone-aware UTC
        now = _now_utc()
        doc = {
            'name':             data['name'],
            'email':            data['email'].lower().strip(),
            'password':         data['password'],
            'role':             'student',
            'country':          data.get('country', ''),
            'institution':      data.get('institution', ''),
            'rating':           0.0,
            # FIX: field was inconsistently named 'problems_solved' in some
            # places and relied upon as a count elsewhere; initialise it here
            # to 0 (integer) so arithmetic on it is always safe.
            'problems_solved':  0,
            # problem_rankings shape:
            # { problemId: { best_scores, best_fx, ranks, total_participants } }
            'problem_rankings': {},
            'created_at':       now,
            'updated_at':       now,
        }
        result = db[Student.COLLECTION].insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc

    @staticmethod
    def find_by_email(db, email: str):
        if not email:
            return None
        return db[Student.COLLECTION].find_one({'email': email.lower().strip()})

    @staticmethod
    def find_by_id(db, user_id: str):
        try:
            return db[Student.COLLECTION].find_one({'_id': ObjectId(user_id)})
        except Exception:
            return None

    @staticmethod
    def update_timestamp(db, user_id: str):
        """Convenience helper to touch updated_at without a full document read."""
        try:
            db[Student.COLLECTION].update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'updated_at': _now_utc()}},
            )
        except Exception:
            pass


class Admin:
    COLLECTION = 'admins'

    REQUIRED_FIELDS = ('name', 'email', 'password')

    @staticmethod
    def create(db, data: dict) -> dict:
        # FIX: validate required fields before attempting insertion
        missing = [f for f in Admin.REQUIRED_FIELDS if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        now = _now_utc()
        doc = {
            'name':        data['name'],
            'email':       data['email'].lower().strip(),
            'password':    data['password'],
            'role':        'admin',
            'permissions': data.get('permissions', []),
            'created_at':  now,
            'updated_at':  now,
        }
        result = db[Admin.COLLECTION].insert_one(doc)
        doc['_id'] = result.inserted_id
        return doc

    @staticmethod
    def find_by_email(db, email: str):
        if not email:
            return None
        return db[Admin.COLLECTION].find_one({'email': email.lower().strip()})

    @staticmethod
    def find_by_id(db, user_id: str):
        try:
            return db[Admin.COLLECTION].find_one({'_id': ObjectId(user_id)})
        except Exception:
            return None