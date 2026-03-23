# GigBridge Quick Start Guide

Get GigBridge running in 5 minutes!

## Prerequisites

- Python 3.8+
- Node.js 16+
- Git

## Step 1: Clone Repository

```bash
git clone https://github.com/aaryan-max/gigbridge_backend.git gigbridge
cd gigbridge
```

## Step 2: Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your email credentials (optional for testing)
# nano .env  # or use any text editor
```

## Step 3: Frontend Setup (2 minutes)

```bash
# Navigate to frontend (from project root)
cd ../frontend

# Install dependencies
npm install

# Environment file already configured for local development
```

## Step 4: Run the Application

Open **two terminal windows**:

### Terminal 1 - Backend
```bash
cd backend

# Activate venv if not already active
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Start backend
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

### Terminal 2 - Frontend
```bash
cd frontend

# Start frontend
npm run dev
```

You should see:
```
VITE ready in XXX ms
➜  Local:   http://localhost:5173/
```

## Step 5: Open in Browser

Navigate to: **http://localhost:5173**

You should see the GigBridge homepage!

## Quick Commands

### Using Scripts (Easier!)

**Mac/Linux:**
```bash
# Terminal 1
./start-backend.sh

# Terminal 2
./start-frontend.sh
```

**Windows:**
```bash
# Terminal 1
start-backend.bat

# Terminal 2
start-frontend.bat
```

## Testing the Integration

1. Click "Sign Up" → Choose "Client" or "Freelancer"
2. Fill in the form
3. Click "Send OTP" (check terminal for OTP if email not configured)
4. Enter OTP and complete signup
5. Login with your credentials
6. Browse artists to see data from backend

## Troubleshooting

### "Module not found" error (Backend)
```bash
pip install -r requirements.txt
```

### "Cannot find module" error (Frontend)
```bash
npm install
```

### CORS error in browser
- Make sure backend is running on port 5000
- Check that both servers are running

### Port already in use
```bash
# Backend (port 5000)
lsof -ti:5000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :5000   # Windows

# Frontend (port 5173)
lsof -ti:5173 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :5173   # Windows
```

### OTP not received
- Check backend terminal for the OTP code
- Or configure email in `backend/.env`

## What's Next?

- Read [README.md](./README.md) for detailed information
- Check [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for API details
- See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for development patterns

## Project Structure

```
gigbridge/
├── backend/          # Flask API (port 5000)
│   └── app.py       # Main application
├── frontend/        # React app (port 5173)
│   └── src/
│       ├── components/
│       └── services/  # API integration
└── README.md
```

## Default URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **API Docs**: See API_DOCUMENTATION.md

## Environment Variables

### Required for Full Functionality

**backend/.env:**
```env
GIGBRIDGE_SENDER_EMAIL=your-email@gmail.com
GIGBRIDGE_APP_PASSWORD=your-app-password
```

**frontend/.env:**
```env
VITE_API_BASE_URL=http://localhost:5000
```

## Stopping the Application

Press `Ctrl+C` in both terminal windows to stop the servers.

## Next Development Steps

1. Configure email in backend/.env for OTP
2. Explore the API endpoints
3. Customize frontend components
4. Add new features

Happy coding! 🚀
