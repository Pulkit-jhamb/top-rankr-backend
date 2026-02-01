"""
Script to create database indexes for better query performance
Run this once to optimize database queries
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
import os

MONGO_URI = "mongodb+srv://softwareproject011:software12345678@cluster1.iwwtbfy.mongodb.net/?appName=Cluster1"

try:
    client = MongoClient(MONGO_URI)
    db = client['topranker']
    print("✓ Connected to MongoDB Atlas")
    
    # Create indexes for contests collection
    print("\nCreating indexes for contests collection...")
    db.contests.create_index([("type", ASCENDING)])
    print("✓ Created index on 'type'")
    
    db.contests.create_index([("status", ASCENDING)])
    print("✓ Created index on 'status'")
    
    db.contests.create_index([("eventId", ASCENDING)], unique=True)
    print("✓ Created unique index on 'eventId'")
    
    # Create indexes for students collection
    print("\nCreating indexes for students collection...")
    db.students.create_index([("email", ASCENDING)], unique=True)
    print("✓ Created unique index on 'email'")
    
    db.students.create_index([("rating", DESCENDING)])
    print("✓ Created index on 'rating' (descending)")
    
    db.students.create_index([("country", ASCENDING)])
    print("✓ Created index on 'country'")
    
    db.students.create_index([("institution", ASCENDING)])
    print("✓ Created index on 'institution'")
    
    # Create indexes for problems collection
    print("\nCreating indexes for problems collection...")
    db.problems.create_index([("problemId", ASCENDING)], unique=True)
    print("✓ Created unique index on 'problemId'")
    
    db.problems.create_index([("level", ASCENDING)])
    print("✓ Created index on 'level'")
    
    db.problems.create_index([("ownerName", ASCENDING)])
    print("✓ Created index on 'ownerName'")
    
    # Create indexes for submissions collection
    print("\nCreating indexes for submissions collection...")
    db.submissions.create_index([("userId", ASCENDING)])
    print("✓ Created index on 'userId'")
    
    db.submissions.create_index([("problemId", ASCENDING)])
    print("✓ Created index on 'problemId'")
    
    db.submissions.create_index([("userId", ASCENDING), ("problemId", ASCENDING)])
    print("✓ Created compound index on 'userId' and 'problemId'")
    
    db.submissions.create_index([("submittedAt", DESCENDING)])
    print("✓ Created index on 'submittedAt' (descending)")
    
    print("\n✅ All indexes created successfully!")
    print("\nListing all indexes:")
    
    for collection_name in ['contests', 'students', 'problems', 'submissions']:
        print(f"\n{collection_name} indexes:")
        for index in db[collection_name].list_indexes():
            print(f"  - {index['name']}: {index['key']}")
    
    client.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
