# TopRanker Backend - Authentication System

## Overview

Flask backend with MongoDB Atlas integration for the TopRanker competitive programming platform.

## Features

- User authentication (Student & Admin roles)
- JWT token-based authorization
- Password hashing with Werkzeug
- MongoDB Atlas integration
- CORS enabled for frontend communication

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables

The backend uses the following configuration (already set in app.py):

- MongoDB URI: `mongodb+srv://softwareproject011:software12345678@cluster1.iwwtbfy.mongodb.net/?appName=Cluster1`
- Database: `topranker`
- Port: `3999`

### 3. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:3999`

## API Endpoints

### Authentication Routes (prefix: `/api/auth`)

#### 1. Sign Up

**POST** `/api/auth/signup`

**Request Body:**

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "role": "student",
  "institution": "MIT",
  "country": "USA"
}
```

**Response (201):**

```json
{
  "message": "User created successfully",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student"
  }
}
```

#### 2. Login

**POST** `/api/auth/login`

**Request Body:**

```json
{
  "email": "john@example.com",
  "password": "password123",
  "role": "student"
}
```

**Response (200):**

```json
{
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student"
  }
}
```

#### 3. Verify Token

**GET** `/api/auth/verify`

**Headers:**

```
Authorization: Bearer <token>
```

**Response (200):**

```json
{
  "valid": true,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student"
  }
}
```

### Health Check

**GET** `/health`

**Response:**

```json
{
  "status": "ok",
  "mongodb": "connected"
}
```

## Database Collections

### Students Collection

```javascript
{
  "_id": ObjectId,
  "name": String,
  "email": String (unique, lowercase),
  "password": String (hashed),
  "role": "student",
  "institution": String,
  "country": String,
  "rating": Number (default: 0),
  "problems_solved": Number (default: 0),
  "contests_participated": Number (default: 0),
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### Admins Collection

```javascript
{
  "_id": ObjectId,
  "name": String,
  "email": String (unique, lowercase),
  "password": String (hashed),
  "role": "admin",
  "permissions": Array<String>,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

## Security Features

- Passwords are hashed using Werkzeug's `generate_password_hash`
- JWT tokens expire after 7 days
- Email addresses are stored in lowercase
- CORS enabled for cross-origin requests
- Token validation middleware for protected routes

## Error Handling

- 400: Bad Request (missing data)
- 401: Unauthorized (invalid credentials/token)
- 404: Not Found (user not found)
- 409: Conflict (user already exists)
- 500: Internal Server Error (database connection failed)
