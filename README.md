# GigBridge - Freelancer & Client Platform

GigBridge is a full-stack platform connecting freelancers with clients. The project is organized as a monorepo with separate frontend and backend applications.

## Project Structure

```
gigbridge/
├── backend/          # Flask backend API
│   ├── app.py        # Main Flask application
│   ├── database.py   # Database operations
│   ├── requirements.txt
│   └── ...
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── services/  # API service layer
│   │   └── context/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Technology Stack

### Backend
- **Flask** - Python web framework
- **SQLite** - Database
- **Flask-CORS** - Cross-origin resource sharing
- **Sentence Transformers** - Semantic search
- **Google Generative AI** - AI chatbot

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Installation & Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your email credentials
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# The default API URL is already configured for local development
```

## Running the Application

You need to run both backend and frontend servers simultaneously.

### Terminal 1 - Backend (Port 5000)

```bash
cd backend
python app.py
```

The backend will start on `http://localhost:5000`

### Terminal 2 - Frontend (Port 5173)

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5173`

Open your browser and navigate to `http://localhost:5173`

## Environment Variables

### Backend (.env)
- `GIGBRIDGE_SENDER_EMAIL` - Gmail address for sending OTPs
- `GIGBRIDGE_APP_PASSWORD` - Gmail app password (not your regular password)
- `GOOGLE_CLIENT_ID` - Google OAuth client ID (optional)
- `GOOGLE_CLIENT_SECRET` - Google OAuth secret (optional)

### Frontend (.env)
- `VITE_API_BASE_URL` - Backend API URL (default: http://localhost:5000)

## API Endpoints

### Authentication
- `POST /client/send-otp` - Send OTP to client email
- `POST /client/verify-otp` - Verify client OTP
- `POST /client/signup` - Client signup
- `POST /client/login` - Client login
- `POST /freelancer/send-otp` - Send OTP to freelancer email
- `POST /freelancer/verify-otp` - Verify freelancer OTP
- `POST /freelancer/signup` - Freelancer signup
- `POST /freelancer/login` - Freelancer login

### Freelancers
- `GET /freelancers/search` - Search freelancers with filters
- `GET /freelancers/all` - Get all freelancers
- `GET /freelancers/:id` - Get freelancer by ID
- `POST /freelancer/profile` - Create/update freelancer profile
- `POST /freelancer/update-availability` - Update availability
- `GET /freelancer/stats` - Get freelancer statistics

### Clients
- `POST /client/profile` - Create/update client profile
- `POST /client/hire` - Hire a freelancer
- `GET /client/job-requests` - Get client job requests
- `GET /client/saved-freelancers` - Get saved freelancers

### Messages
- `POST /client/message/send` - Send message from client
- `POST /freelancer/message/send` - Send message from freelancer
- `GET /message/history` - Get message history

## Features

### Implemented
- User authentication (email/password + OTP verification)
- Client and freelancer registration
- Profile creation and management
- Browse and search freelancers
- Semantic search for freelancers
- Messaging system
- Hire request system
- Saved freelancers/clients
- Admin panel
- KYC verification

### Frontend Integration Status
- Authentication flows (signup/login)
- Browse artists with API integration
- Centralized API service layer
- Error handling and loading states
- Protected routes
- Context-based state management

## Development Notes

### CORS Configuration
The backend has CORS enabled to accept requests from the frontend running on port 5173. The configuration allows all origins in development mode.

### API Service Layer
All API calls in the frontend are centralized in the `frontend/src/services/` directory:
- `api.js` - Base API client with error handling
- `authService.js` - Authentication endpoints
- `freelancerService.js` - Freelancer operations
- `clientService.js` - Client operations
- `messageService.js` - Messaging operations

### Database
The backend uses SQLite databases:
- `client.db` - Client data
- `freelancer.db` - Freelancer data

Tables are created automatically on first run.

## Building for Production

### Frontend

```bash
cd frontend
npm run build
```

This creates an optimized production build in `frontend/dist/`.

### Backend

For production deployment:
1. Set proper environment variables
2. Use a production WSGI server (e.g., Gunicorn)
3. Configure CORS to allow only your production domain
4. Use a production database (PostgreSQL recommended)

## Troubleshooting

### CORS Errors
- Ensure backend is running on port 5000
- Check that CORS is enabled in `backend/app.py`
- Verify `VITE_API_BASE_URL` in frontend `.env`

### API Connection Issues
- Verify both servers are running
- Check firewall settings
- Ensure ports 5000 and 5173 are not in use by other applications

### OTP Not Sending
- Verify Gmail credentials in backend `.env`
- Enable "Less secure app access" or use App Password for Gmail
- Check SMTP settings in `backend/app.py`

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is proprietary and confidential.
