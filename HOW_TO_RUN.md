# 🚀 How to Run GigBridge Backend

## Prerequisites

Make sure you have Python 3.7+ installed on your system.

## Step 1: Install Required Packages

Open your terminal/command prompt and run:

```bash
pip install flask requests werkzeug
```

Or if you prefer, create a `requirements.txt` file and install:

```bash
pip install -r requirements.txt
```

## Step 2: Start the Backend Server

Open **Terminal 1** (or Command Prompt) and navigate to the project folder:

```bash
cd "C:\Users\Sarthak Sawant\Desktop\sss\gigbridge_backend"
```

Then run:

```bash
python app.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

**Keep this terminal window open!** The server must be running for the CLI to work.

## Step 3: Run the CLI Client (in a NEW Terminal)

Open **Terminal 2** (a new terminal window) and navigate to the same folder:

```bash
cd "C:\Users\Sarthak Sawant\Desktop\sss\gigbridge_backend"
```

Then run:

```bash
python cli_test.py
```

## Step 4: Use the Application

You'll see a menu like this:

```
====== GIGBRIDGE ======
1. Login
2. Sign Up
3. Continue as Client
4. Continue as Freelancer
5. Exit
```

### Quick Start Guide:

1. **Sign Up as Client:**
   - Choose option `2` → `1` (Client)
   - Enter your name, email, password
   - Check your email for OTP
   - Enter OTP to complete signup

2. **Sign Up as Freelancer:**
   - Choose option `2` → `2` (Freelancer)
   - Enter your name, email, password
   - Check your email for OTP
   - Enter OTP to complete signup

3. **Login:**
   - Choose option `1` → Select role (1 for Client, 2 for Freelancer)
   - Enter email and password

4. **Client Dashboard Features:**
   - View All Freelancers
   - Search Freelancers (by category and budget)
   - View My Jobs
   - Saved Freelancers
   - Notifications
   - WhatsApp-like Chat

5. **Freelancer Dashboard Features:**
   - Create/Update Profile
   - View Hire Requests (Inbox)
   - Accept/Reject Jobs
   - Chat with Clients

## 📝 Important Notes

- **Two Terminal Windows Required:** 
  - Terminal 1: Backend server (`app.py`) - MUST stay running
  - Terminal 2: CLI client (`cli_test.py`) - This is where you interact

- **Email Setup:** 
  - The app sends OTP emails. Make sure your email credentials are configured in `app.py` (lines 24-25) or set environment variables:
    - `GIGBRIDGE_SENDER_EMAIL`
    - `GIGBRIDGE_APP_PASSWORD`

- **Database Files:**
  - `client.db` - Stores client data
  - `freelancer.db` - Stores freelancer data, messages, jobs, notifications
  - These are created automatically on first run

## 🐛 Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'flask'`
- **Solution:** Run `pip install flask requests werkzeug`

**Problem:** `Address already in use`
- **Solution:** Another process is using port 5000. Either stop that process or change the port in `app.py` (line 906): `app.run(debug=True, port=5001)`

**Problem:** Can't connect to server
- **Solution:** Make sure `app.py` is running in Terminal 1 before running `cli_test.py`

**Problem:** Email not sending
- **Solution:** Check email credentials in `app.py` or set environment variables. The app will still work without email, but OTP won't be sent.

## 🎯 Quick Test

1. Start server: `python app.py`
2. In new terminal: `python cli_test.py`
3. Choose option `2` (Sign Up) → `1` (Client)
4. Enter details and check email for OTP
5. Complete signup and explore the dashboard!

---

**Happy Coding! 🎉**
