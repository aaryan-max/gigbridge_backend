const express = require('express');
const Razorpay = require('razorpay');
const sqlite3 = require('sqlite3').verbose();
const crypto = require('crypto');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

// --- CONFIGURATION ---
const RAZORPAY_KEY_ID = 'rzp_test_SBgxmNNjKl5492'; 
const RAZORPAY_KEY_SECRET = 't3wpE44WAsSO4nlklR6dvnx2'; // Your Secret

const razorpay = new Razorpay({
    key_id: RAZORPAY_KEY_ID,
    key_secret: RAZORPAY_KEY_SECRET
});

// --- DATABASE SETUP ---
const db = new sqlite3.Database('./payments.db');
db.serialize(() => {
    db.run("CREATE TABLE IF NOT EXISTS transactions (order_id TEXT PRIMARY KEY, amount INTEGER, status TEXT)");
});

// --- API 1: CREATE ORDER ---
app.post('/create-order', async (req, res) => {
    try {
        const options = {
            amount: req.body.amount * 100, // Convert to paise
            currency: "INR",
            receipt: "receipt_" + Date.now()
        };
        
        const order = await razorpay.orders.create(options);
        
        db.run("INSERT INTO transactions (order_id, amount, status) VALUES (?, ?, ?)", 
            [order.id, options.amount, 'PENDING'], 
            (err) => {
                if (err) return res.status(500).json({ error: err.message });
                console.log(`[DB] New Order Created: ${order.id}`);
                res.json(order);
            }
        );
    } catch (error) {
        console.error("Razorpay Error:", error);
        res.status(500).send(error);
    }
});

// --- API 2: VERIFY PAYMENT ---
app.post('/verify-payment', (req, res) => {
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = req.body;

    const body = razorpay_order_id + "|" + razorpay_payment_id;
    const expectedSignature = crypto
        .createHmac('sha256', RAZORPAY_KEY_SECRET)
        .update(body.toString())
        .digest('hex');

    if (expectedSignature === razorpay_signature) {
        db.run("UPDATE transactions SET status = ? WHERE order_id = ?", 
            ['SUCCESS', razorpay_order_id], 
            (err) => {
                if(err) return res.status(500).send("DB Error");
                console.log(`[DB] Payment Verified! Order ${razorpay_order_id} is now SUCCESS.`);
                res.json({ status: "ok", message: "Payment verified successfully" });
            }
        );
    } else {
        res.status(400).json({ status: "error", message: "Invalid Signature" });
    }
});

// LISTENING ON PORT 5000
app.listen(5000, () => console.log('✅ Server running on http://localhost:5000'));