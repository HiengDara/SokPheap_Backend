const express = require('express');
const dotenv = require('dotenv');
const bodyParser = require('body-parser');
const connectDB = require('./dbconnect');
const VitalSign = require('./vital_schema');

dotenv.config();
const app = express();
app.use(bodyParser.json());

// Connect to MongoDB
connectDB();

// POST /vitals
app.post('/vitals', async (req, res) => {
    const vital = req.body;

    // No user verification logic here
    try {
        const newVital = new VitalSign(vital);
        const saved = await newVital.save();
        res.json({ message: 'Vitals recorded', data: saved });
    } catch (err) {
        res.status(400).json({ detail: `MongoDB error: ${err.message}` });
    }
});

// GET /vitals/:user_id
app.get('/vitals/:user_id', async (req, res) => {
    try {
        const results = await VitalSign.find({ user_id: req.params.user_id }).sort({ recorded_at: -1 });
        if (results.length === 0) {
            return res.status(404).json({ detail: 'No vitals found for this user' });
        }
        res.json({ data: results });
    } catch (err) {
        res.status(500).json({ detail: 'MongoDB query failed' });
    }
});

// PUT /vitals/:record_id
app.put('/vitals/:record_id', async (req, res) => {
    try {
        const updated = await VitalSign.findByIdAndUpdate(req.params.record_id, req.body, {
            new: true,
            runValidators: true
        });

        if (!updated) {
            return res.status(404).json({ detail: 'Vital record not found' });
        }

        res.json({ message: 'Vitals updated', data: updated });
    } catch (err) {
        res.status(400).json({ detail: `Update failed: ${err.message}` });
    }
});

// Startup
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
    console.log(`🚀 Server running on http://localhost:${PORT}`);
});
