# GigBridge API Documentation

Base URL: `http://localhost:5000`

## Authentication Endpoints

### Client Authentication

#### Send OTP to Client
```
POST /client/send-otp
Content-Type: application/json

{
  "email": "client@example.com"
}

Response:
{
  "message": "OTP sent"
}
```

#### Verify Client OTP
```
POST /client/verify-otp
Content-Type: application/json

{
  "email": "client@example.com",
  "otp": "123456"
}

Response:
{
  "message": "OTP verified"
}
```

#### Client Signup
```
POST /client/signup
Content-Type: application/json

{
  "name": "John Doe",
  "username": "johndoe",
  "email": "client@example.com",
  "password": "securepassword"
}

Response:
{
  "message": "Client registered successfully",
  "client_id": 1
}
```

#### Client Login
```
POST /client/login
Content-Type: application/json

{
  "email": "client@example.com",
  "password": "securepassword"
}

Response:
{
  "message": "Login successful",
  "client": {
    "id": 1,
    "email": "client@example.com",
    "name": "John Doe"
  }
}
```

### Freelancer Authentication

#### Send OTP to Freelancer
```
POST /freelancer/send-otp
Content-Type: application/json

{
  "email": "freelancer@example.com"
}

Response:
{
  "message": "OTP sent"
}
```

#### Verify Freelancer OTP
```
POST /freelancer/verify-otp
Content-Type: application/json

{
  "email": "freelancer@example.com",
  "otp": "123456"
}

Response:
{
  "message": "OTP verified"
}
```

#### Freelancer Signup
```
POST /freelancer/signup
Content-Type: application/json

{
  "name": "Jane Smith",
  "username": "janesmith",
  "email": "freelancer@example.com",
  "password": "securepassword"
}

Response:
{
  "message": "Freelancer registered successfully",
  "freelancer_id": 1
}
```

#### Freelancer Login
```
POST /freelancer/login
Content-Type: application/json

{
  "email": "freelancer@example.com",
  "password": "securepassword"
}

Response:
{
  "message": "Login successful",
  "freelancer": {
    "id": 1,
    "email": "freelancer@example.com",
    "name": "Jane Smith"
  }
}
```

## Profile Endpoints

### Client Profile

#### Create/Update Client Profile
```
POST /client/profile
Content-Type: application/json

{
  "email": "client@example.com",
  "company_name": "ABC Corp",
  "industry": "Technology",
  "phone": "+91-9876543210",
  "location": "Mumbai, India"
}

Response:
{
  "message": "Profile created successfully"
}
```

### Freelancer Profile

#### Create/Update Freelancer Profile
```
POST /freelancer/profile
Content-Type: application/json

{
  "email": "freelancer@example.com",
  "tagline": "Full Stack Developer",
  "category": "Developer",
  "bio": "Experienced developer with 5+ years",
  "skills": "React, Node.js, Python",
  "hourly_rate": 50,
  "availability": "Available",
  "portfolio_link": "https://portfolio.com",
  "phone": "+91-9876543210",
  "location": "Bangalore, India",
  "profile_picture": "https://example.com/photo.jpg"
}

Response:
{
  "message": "Profile created successfully"
}
```

#### Update Freelancer Availability
```
POST /freelancer/update-availability
Content-Type: application/json

{
  "email": "freelancer@example.com",
  "availability": "Busy"
}

Response:
{
  "message": "Availability updated successfully"
}
```

## Freelancer Search & Discovery

#### Search Freelancers
```
GET /freelancers/search?category=Developer&query=react&min_rate=20&max_rate=100

Query Parameters:
- category (optional): Filter by category
- query (optional): Search term
- skills (optional): Comma-separated skills
- min_rate (optional): Minimum hourly rate
- max_rate (optional): Maximum hourly rate
- location (optional): Location filter
- availability (optional): Availability status

Response:
{
  "freelancers": [
    {
      "id": 1,
      "name": "Jane Smith",
      "email": "freelancer@example.com",
      "tagline": "Full Stack Developer",
      "category": "Developer",
      "hourly_rate": 50,
      "availability": "Available",
      "location": "Bangalore, India",
      "skills": "React, Node.js, Python",
      "rating": 4.8
    }
  ]
}
```

#### Get All Freelancers
```
GET /freelancers/all

Response:
{
  "freelancers": [...]
}
```

#### Get Freelancer by ID
```
GET /freelancers/1

Response:
{
  "freelancer": {
    "id": 1,
    "name": "Jane Smith",
    "email": "freelancer@example.com",
    "tagline": "Full Stack Developer",
    "bio": "Experienced developer with 5+ years",
    "skills": "React, Node.js, Python",
    "hourly_rate": 50,
    "availability": "Available",
    "portfolio_link": "https://portfolio.com",
    "location": "Bangalore, India",
    "rating": 4.8
  }
}
```

## Messaging

#### Send Message (Client to Freelancer)
```
POST /client/message/send
Content-Type: application/json

{
  "client_email": "client@example.com",
  "freelancer_email": "freelancer@example.com",
  "message": "Hi, I'd like to discuss a project"
}

Response:
{
  "message": "Message sent successfully"
}
```

#### Send Message (Freelancer to Client)
```
POST /freelancer/message/send
Content-Type: application/json

{
  "freelancer_email": "freelancer@example.com",
  "client_email": "client@example.com",
  "message": "Sure, I'd be happy to help!"
}

Response:
{
  "message": "Message sent successfully"
}
```

#### Get Message History
```
GET /message/history?user1=client@example.com&user2=freelancer@example.com

Response:
{
  "messages": [
    {
      "sender": "client@example.com",
      "receiver": "freelancer@example.com",
      "message": "Hi, I'd like to discuss a project",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "sender": "freelancer@example.com",
      "receiver": "client@example.com",
      "message": "Sure, I'd be happy to help!",
      "timestamp": "2024-01-15T10:35:00"
    }
  ]
}
```

#### Get Client Message Threads
```
GET /client/messages/threads?client_email=client@example.com

Response:
{
  "threads": [
    {
      "freelancer_email": "freelancer@example.com",
      "freelancer_name": "Jane Smith",
      "last_message": "Sure, I'd be happy to help!",
      "timestamp": "2024-01-15T10:35:00",
      "unread": 0
    }
  ]
}
```

## Hiring

#### Hire Freelancer
```
POST /client/hire
Content-Type: application/json

{
  "client_email": "client@example.com",
  "freelancer_email": "freelancer@example.com",
  "project_title": "Website Development",
  "project_description": "Build a responsive website",
  "budget": 50000,
  "deadline": "2024-02-15"
}

Response:
{
  "message": "Hire request sent successfully",
  "request_id": 1
}
```

#### Get Freelancer Hire Inbox
```
GET /freelancer/hire/inbox?email=freelancer@example.com

Response:
{
  "requests": [
    {
      "id": 1,
      "client_email": "client@example.com",
      "client_name": "John Doe",
      "project_title": "Website Development",
      "project_description": "Build a responsive website",
      "budget": 50000,
      "deadline": "2024-02-15",
      "status": "pending",
      "timestamp": "2024-01-15T10:00:00"
    }
  ]
}
```

#### Respond to Hire Request
```
POST /freelancer/hire/respond
Content-Type: application/json

{
  "request_id": 1,
  "status": "accepted",
  "message": "I'd be happy to work on this project!"
}

Response:
{
  "message": "Response recorded successfully"
}
```

#### Get Client Job Requests
```
GET /client/job-requests?client_email=client@example.com

Response:
{
  "requests": [
    {
      "id": 1,
      "freelancer_email": "freelancer@example.com",
      "freelancer_name": "Jane Smith",
      "project_title": "Website Development",
      "status": "accepted",
      "timestamp": "2024-01-15T10:00:00"
    }
  ]
}
```

## Saved Lists

#### Save Freelancer (Client)
```
POST /client/save-freelancer
Content-Type: application/json

{
  "client_email": "client@example.com",
  "freelancer_email": "freelancer@example.com"
}

Response:
{
  "message": "Freelancer saved successfully"
}
```

#### Get Saved Freelancers
```
GET /client/saved-freelancers?client_email=client@example.com

Response:
{
  "saved": [
    {
      "freelancer_email": "freelancer@example.com",
      "freelancer_name": "Jane Smith",
      "category": "Developer",
      "hourly_rate": 50
    }
  ]
}
```

#### Save Client (Freelancer)
```
POST /freelancer/save-client
Content-Type: application/json

{
  "freelancer_email": "freelancer@example.com",
  "client_email": "client@example.com"
}

Response:
{
  "message": "Client saved successfully"
}
```

#### Get Saved Clients
```
GET /freelancer/saved-clients?email=freelancer@example.com

Response:
{
  "saved": [
    {
      "client_email": "client@example.com",
      "client_name": "John Doe",
      "company": "ABC Corp"
    }
  ]
}
```

## Statistics

#### Get Freelancer Stats
```
GET /freelancer/stats?email=freelancer@example.com

Response:
{
  "stats": {
    "total_jobs": 15,
    "completed_jobs": 12,
    "active_jobs": 3,
    "rating": 4.8,
    "total_earnings": 250000
  }
}
```

#### Get Client Notifications
```
GET /client/notifications?client_email=client@example.com

Response:
{
  "notifications": [
    {
      "type": "message",
      "message": "New message from Jane Smith",
      "timestamp": "2024-01-15T10:35:00",
      "read": false
    }
  ]
}
```

## Error Responses

All endpoints return error responses in the following format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (missing fields, validation errors)
- `401` - Unauthorized (authentication failed)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Notes

1. All POST requests require `Content-Type: application/json` header
2. Timestamps are in ISO 8601 format
3. Email addresses are used as primary identifiers for users
4. OTP verification is required before signup
5. All endpoints support CORS for cross-origin requests
