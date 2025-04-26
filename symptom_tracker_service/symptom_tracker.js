const express = require('express');
const connectDB = require('./dbconnect');
const Symptom = require('./symptom_schema');
require('dotenv').config();
const mongoose = require('mongoose');


const app = express();

// Middleware
app.use(express.json());

// Connect to MongoDB 
connectDB().then(() => {
    console.log('✅ Symptom DB Connected');
}).catch(err => {
    console.error('❌ DB Connection Failed:', err);
});

// 1. POST /symptoms - Log new symptom
app.post('/symptoms', async (req, res) => {
    try {
        const { userId, symptom, severity } = req.body;

        // Basic validation
        if (!userId || !symptom || severity === undefined) {
            return res.status(400).json({
                success: false,
                message: 'userId, symptom, and severity are required'
            });
        }

        const newSymptom = await Symptom.create(req.body);

        res.status(201).json({
            success: true,
            data: newSymptom
        });
    } catch (err) {
        console.error('❌ Symptom creation error:', err.message);
        res.status(500).json({
            success: false,
            message: err.message.includes('validation')
                ? err.message
                : 'Server error'
        });
    }
});

// 2. GET /symptoms/aggregate - Analyze trends
app.get('/symptoms/aggregate', async (req, res) => {
    try {
        const userId = req.query.userId;

        if (!userId) {
            return res.status(400).json({
                success: false,
                message: "userId is required"
            });
        }

        const results = await Symptom.aggregate([
            {
                $match: {
                    userId: userId // string match
                }
            },
            {
                $group: {
                    _id: '$symptom',
                    total: { $sum: 1 },
                    avgSeverity: { $avg: '$severity' }
                }
            }
        ]);

        res.json({ success: true, data: results });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// 3. GET /symptoms/:userId - List symptoms
app.get('/symptoms/:userId', async (req, res) => {
    try {
        const symptoms = await Symptom.find({ userId: req.params.userId })
            .sort({ recordedAt: -1 })
            .lean();

        res.json({
            success: true,
            count: symptoms.length,
            data: symptoms
        });
    } catch (err) {
        console.error('❌ Fetch error:', err.message);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});



// Start server
const PORT = process.env.PORT || 5002;
app.listen(PORT, () => {
    console.log(`🚀 Symptom Tracker running on port ${PORT}`);
    console.log(`🔗 MongoDB: ${process.env.MONGO_URI.split('@')[1]}`);
});