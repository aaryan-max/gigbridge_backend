# GigBridge CLI - Setup and Usage

## 🚀 Quick Start

### Step 1: Start the Server
**Option A: Easy Way (Recommended)**
```bash
# Double-click this file OR run in terminal
start_server.bat
```

**Option B: Manual Way**
```bash
# Open terminal and run:
python start_server.py
```

**Option C: Direct Flask**
```bash
python app.py
```

### Step 2: Run CLI (in separate terminal)
```bash
python cli_test.py
```

---

## 🔧 What Each File Does

| File | Purpose |
|------|---------|
| `start_server.py` | Smart server startup with checks |
| `start_server.bat` | Windows batch file for easy startup |
| `app.py` | Main Flask application |
| `cli_test.py` | Command-line interface |

---

## 📋 Features Available

### ✅ **Freelancer Features**
- **Profile Management**: Create/update profile with years/months experience
- **Availability Status**: 🟢 Available, 🟡 Busy, 🔴 On Leave
- **Portfolio Management**: Add and view portfolio items
- **Hire Requests**: View and respond to job offers
- **Messaging**: Chat with clients
- **Earnings**: Track income and performance
- **Verification Status**: Check KYC status

### ✅ **Client Features**  
- **Freelancer Search**: Find freelancers by category/budget
- **Hire Management**: Send job offers and track progress
- **Messaging**: Chat with freelancers
- **Ratings**: Rate completed work
- **Saved Freelancers**: Bookmark favorite freelancers

---

## 🎯 New Features Added

### 1. **Enhanced Experience Input**
- **Before**: Single integer (e.g., "3 years")
- **After**: Years + Months (e.g., "3 years 6 months")
- **Validation**: Age-based experience limits

### 2. **Dynamic Project Count**
- Shows completed projects in real-time
- Calculated dynamically from database

### 3. **Availability Status System**
- **AVAILABLE**: 🟢 Can receive hire requests
- **BUSY**: 🟡 Can receive hire requests (warning shown)
- **ON_LEAVE**: 🔴 Cannot receive hire requests (blocked)

### 4. **Improved Error Handling**
- Clear server connection messages
- Better portfolio loading with detailed errors
- Helpful troubleshooting tips

---

## 🛠️ Troubleshooting

### ❌ "Server Connection Error"
**Problem**: Flask server not running  
**Solution**: 
1. Open NEW terminal window
2. Run: `start_server.bat` or `python start_server.py`
3. Wait for server to start
4. Try CLI again

### ❌ "Portfolio Loading Error"  
**Problem**: Server not responding  
**Solution**: Same as above - start server first

### ❌ "Port 5000 already in use"
**Solution**: 
1. Close other applications using port 5000
2. Or restart your computer
3. Try again

---

## 📱 Example CLI Session

```
====== GIGBRIDGE ======
1. Login
2. Sign Up
3. Continue as Client
4. Continue as Freelancer
5. Exit
Choose option: 4

Plan: BASIC
Job Applies Used: 0 / 10

--- FREELANCER DASHBOARD ---
1. Create/Update Profile
2. View My Profile
3. View Hire Requests
...
17. Update Availability Status
18. Exit
19. Logout
Choose: 2

--- FREELANCER DETAILS ---
ID: 1
Name: John Doe
Experience: 3 years 6 months
Projects Completed: 12
Availability: 🟢 Available
```

---

## 🔄 Development Workflow

1. **Start Server**: `python start_server.py`
2. **Test CLI**: `python cli_test.py` 
3. **Make Changes**: Edit code files
4. **Restart Server**: Stop and restart server to see changes

---

## 📞 Support

If you encounter issues:
1. Check server is running first
2. Verify all files exist in `gigbridge_backend` folder
3. Ensure Python dependencies are installed
4. Check for port conflicts (5000)

**Server Status Check**: Visit http://127.0.0.1:5000/freelancers/1 in browser
