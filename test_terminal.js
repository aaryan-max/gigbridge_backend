// test_terminal.js
const axios = require('axios');
const crypto = require('crypto');

const SERVER_URL = 'http://localhost:3000';

// MUST MATCH THE SECRET IN SERVER.JS
const MY_SECRET_KEY = 't3wpE44WAsSO4nlklR6dvnx2'; // <--- PASTE SAME SECRET HERE

async function runTest() {
    console.log("--- 🚀 STARTING TERMINAL TEST ---");

    try {
        // 1. Create Order
        console.log("\n1. Requesting Order...");
        const orderRes = await axios.post(`${SERVER_URL}/create-order`, { amount: 500 });
        const orderId = orderRes.data.id;
        console.log(`   ✅ Order ID received: ${orderId}`);

        // 2. Simulate Payment (Fake Payment ID, Real Signature)
        const fakePaymentId = "pay_test_" + Date.now();
        
        // Calculate correct signature manually
        const generatedSignature = crypto
            .createHmac('sha256', MY_SECRET_KEY)
            .update(orderId + "|" + fakePaymentId)
            .digest('hex');

        // 3. Verify Payment
        console.log(`\n2. Verifying Payment (ID: ${fakePaymentId})...`);
        const verifyRes = await axios.post(`${SERVER_URL}/verify-payment`, {
            razorpay_order_id: orderId,
            razorpay_payment_id: fakePaymentId,
            razorpay_signature: generatedSignature
        });

        if (verifyRes.data.status === 'ok') {
            console.log(`   🎉 SUCCESS: ${verifyRes.data.message}`);
        } else {
            console.log(`   ❌ FAILED: ${verifyRes.data.message}`);
        }

    } catch (error) {
        console.error("   ❌ ERROR:", error.response ? error.response.data : error.message);
    }
}

runTest();