# Frontend-Backend Integration Guide

## Overview

This document explains how the GigBridge frontend and backend are integrated, including the API service architecture, state management, and best practices.

## Architecture

### Backend (Flask API)
- **Location**: `/backend`
- **Port**: 5000
- **Framework**: Flask with Flask-CORS
- **Database**: SQLite (client.db, freelancer.db)

### Frontend (React SPA)
- **Location**: `/frontend`
- **Port**: 5173
- **Framework**: React 18 with Vite
- **Routing**: React Router v6
- **State**: Context API

## API Service Layer

The frontend uses a centralized API service layer located in `frontend/src/services/`.

### Core API Client (`api.js`)

The base API client provides:
- Automatic JSON parsing
- Unified error handling
- Request/response interceptors
- ApiError class for consistent error handling

```javascript
import { api, ApiError } from './services';

try {
  const data = await api.get('/freelancers/all');
  console.log(data);
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message, error.status);
  }
}
```

### Service Modules

#### 1. authService.js
Handles authentication operations:
- `sendOTP(email, role)` - Send OTP to email
- `verifyOTP(email, otp, role)` - Verify OTP code
- `signup(userData, role)` - Register new user
- `login(email, password, role)` - Authenticate user

#### 2. freelancerService.js
Manages freelancer operations:
- `searchFreelancers(params)` - Search with filters
- `getAllFreelancers()` - Get all freelancers
- `getFreelancerById(id)` - Get single freelancer
- `createProfile(profileData)` - Create/update profile
- `updateAvailability(email, availability)` - Update status
- `getStats(email)` - Get statistics
- `saveClient(freelancerEmail, clientEmail)` - Save client
- `getSavedClients(freelancerEmail)` - Get saved list
- `changePassword(email, oldPassword, newPassword)` - Update password

#### 3. clientService.js
Manages client operations:
- `createProfile(profileData)` - Create/update profile
- `sendMessage(clientEmail, freelancerEmail, message)` - Send message
- `hireFreelancer(hireData)` - Send hire request
- `getMessageThreads(clientEmail)` - Get conversations
- `getJobRequests(clientEmail)` - Get job requests
- `getJobs(clientEmail)` - Get active jobs
- `saveFreelancer(clientEmail, freelancerEmail)` - Save freelancer
- `getSavedFreelancers(clientEmail)` - Get saved list
- `getNotifications(clientEmail)` - Get notifications

#### 4. messageService.js
Handles messaging:
- `getHistory(user1Email, user2Email)` - Get conversation
- `sendFreelancerMessage(freelancerEmail, clientEmail, message)` - Send as freelancer
- `sendClientMessage(clientEmail, freelancerEmail, message)` - Send as client

## Component Integration Examples

### Authentication Flow

```jsx
import { useState } from 'react';
import { authService } from '../services';

function SignupComponent({ role }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    otp: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOTP = async () => {
    setLoading(true);
    try {
      await authService.sendOTP(formData.email, role);
      alert('OTP sent!');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authService.verifyOTP(formData.email, formData.otp, role);
      await authService.signup({
        name: formData.name,
        email: formData.email,
        password: formData.password
      }, role);
      // Redirect to login
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSignup}>
      {error && <div className="error">{error}</div>}
      {/* Form fields */}
      <button type="button" onClick={handleSendOTP}>Send OTP</button>
      <button type="submit" disabled={loading}>
        {loading ? 'Signing up...' : 'Sign Up'}
      </button>
    </form>
  );
}
```

### Fetching Data with Loading States

```jsx
import { useState, useEffect } from 'react';
import { freelancerService } from '../services';

function FreelancerList() {
  const [freelancers, setFreelancers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await freelancerService.getAllFreelancers();
        setFreelancers(data.freelancers || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {freelancers.map(f => (
        <div key={f.id}>{f.name}</div>
      ))}
    </div>
  );
}
```

### Search with Filters

```jsx
import { useState, useEffect } from 'react';
import { freelancerService } from '../services';

function FreelancerSearch() {
  const [filters, setFilters] = useState({
    category: '',
    query: '',
    min_rate: '',
    max_rate: '',
    location: '',
    availability: ''
  });
  const [results, setResults] = useState([]);

  const handleSearch = async () => {
    try {
      const data = await freelancerService.searchFreelancers(filters);
      setResults(data.freelancers || []);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  useEffect(() => {
    handleSearch();
  }, [filters]);

  return (
    <div>
      <input
        value={filters.query}
        onChange={(e) => setFilters({...filters, query: e.target.value})}
        placeholder="Search..."
      />
      {/* Display results */}
    </div>
  );
}
```

## State Management

### AuthContext

The application uses React Context for authentication state:

```jsx
import { useAuth } from '../context/AuthContext';

function Component() {
  const { user, loginClient, logout, markProfileCompleted } = useAuth();

  const handleLogin = async () => {
    const response = await authService.login(email, password, 'client');
    loginClient({
      email,
      role: 'client',
      ...response
    });
  };

  return (
    <div>
      {user.isAuthenticated ? (
        <>
          <p>Welcome {user.email}</p>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
    </div>
  );
}
```

### User Data Storage

User authentication data is stored in:
- `localStorage.client_auth` - Authentication flag
- `localStorage.user_data` - User details (email, role, etc.)
- `localStorage.client_profile_done` - Profile completion status

## Environment Configuration

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:5000
```

Access in code:
```javascript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

### Backend (.env)

```env
GIGBRIDGE_SENDER_EMAIL=your-email@gmail.com
GIGBRIDGE_APP_PASSWORD=your-app-password
```

## CORS Configuration

The backend has CORS enabled for all origins in development:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
  r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
  }
})
```

For production, restrict to specific domain:
```python
CORS(app, resources={r"/*": {"origins": "https://yourdomain.com"}})
```

## Error Handling Best Practices

### 1. Display User-Friendly Messages

```jsx
const [error, setError] = useState('');

try {
  await api.post('/endpoint', data);
} catch (err) {
  if (err.status === 400) {
    setError('Please check your input');
  } else if (err.status === 401) {
    setError('Authentication failed');
  } else {
    setError('Something went wrong. Please try again.');
  }
}
```

### 2. Handle Network Errors

```jsx
try {
  await api.get('/endpoint');
} catch (err) {
  if (err.status === 0) {
    setError('Cannot connect to server. Please check your connection.');
  } else {
    setError(err.message);
  }
}
```

### 3. Loading States

```jsx
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  setError('');
  try {
    await api.post('/endpoint', data);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};

return (
  <button disabled={loading} onClick={handleSubmit}>
    {loading ? 'Processing...' : 'Submit'}
  </button>
);
```

## Protected Routes

Use protected route components to restrict access:

```jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children, requireCompleted = true }) {
  const { user } = useAuth();

  if (!user.isAuthenticated) {
    return <Navigate to="/login/client" replace />;
  }

  if (requireCompleted && !user.profileCompleted) {
    return <Navigate to="/client/profile-setup" replace />;
  }

  return children;
}
```

## API Response Formats

### Success Response
```json
{
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response
```json
{
  "error": "Error message"
}
```

### List Response
```json
{
  "freelancers": [...],
  "total": 50
}
```

## Testing Integration

### 1. Test Backend is Running
```bash
curl http://localhost:5000/freelancers/all
```

### 2. Test CORS
Open browser console on `http://localhost:5173` and run:
```javascript
fetch('http://localhost:5000/freelancers/all')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

### 3. Test Authentication Flow
1. Open signup page
2. Enter email and click "Send OTP"
3. Check backend logs for OTP
4. Enter OTP and complete signup
5. Login with credentials
6. Verify redirect to dashboard

## Common Issues & Solutions

### Issue: CORS Error
**Solution**:
- Ensure backend has CORS enabled
- Check backend is running on port 5000
- Verify VITE_API_BASE_URL is correct

### Issue: 404 Not Found
**Solution**:
- Check endpoint path is correct
- Ensure backend route exists
- Verify HTTP method (GET/POST)

### Issue: Network Error
**Solution**:
- Verify both servers are running
- Check firewall settings
- Ensure ports 5000 and 5173 are not blocked

### Issue: OTP Not Received
**Solution**:
- Check email credentials in backend .env
- Enable "App Password" in Gmail
- Check SMTP settings in app.py

## Production Deployment

### Frontend
1. Update `.env` with production API URL
2. Build: `npm run build`
3. Deploy `dist/` folder to static hosting

### Backend
1. Use production WSGI server (Gunicorn)
2. Configure CORS for production domain only
3. Use PostgreSQL instead of SQLite
4. Set secure environment variables

### Example: Gunicorn Configuration
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Additional Resources

- [API Documentation](./API_DOCUMENTATION.md)
- [README](./README.md)
- [React Router Docs](https://reactrouter.com/)
- [Flask-CORS Docs](https://flask-cors.readthedocs.io/)
