// user_management.js
const express = require('express');
const connectDB = require('./dbconnect.js');
const Patient = require('./patient_schema.js');
require('dotenv').config();

const app = express();

// Use built-in middleware (modern Express way, no need for body-parser)
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Connect to MongoDB
connectDB().then(() => {
    console.log('✅ Connected to DB, starting server...');
}).catch(err => {
    console.error('❌ Failed to connect to DB:', err);
});

// 1. POST /users - Create new patient
app.post('/users', async (req, res) => {
    const { firstName, lastName, age, gender, email, phone } = req.body;

    try {
        if (!firstName || !lastName || !age) {
            return res.status(400).json({ message: 'First name, last name, and age are required' });
        }

        const patient = new Patient({
            firstName,
            lastName,
            age,
            gender: gender || 'prefer-not-to-say',
            contact: { email, phone }
        });

        await patient.save();
        res.status(201).json({ message: 'Patient created successfully', patient });
    } catch (err) {
        console.error('Create error:', err.message);
        res.status(500).json({ message: 'Server error' });
    }
});

// 2. GET /users/:id - Get patient details
app.get('/users/:id', async (req, res) => {
    try {
        const patient = await Patient.findById(req.params.id);
        if (!patient) return res.status(404).json({ message: 'Patient not found' });
        res.status(200).json({ patient });
    } catch (err) {
        console.error('Get error:', err.message);
        res.status(500).json({ message: 'Server error' });
    }
});

// 3. PUT /users/:id - Update patient
app.put('/users/:id', async (req, res) => {
    try {
        const patient = await Patient.findByIdAndUpdate(req.params.id, req.body, { new: true });
        if (!patient) return res.status(404).json({ message: 'Patient not found' });
        res.status(200).json({ message: 'Patient updated successfully', patient });
    } catch (err) {
        console.error('Update error:', err.message);
        res.status(500).json({ message: 'Server error' });
    }
});

// 4. DELETE /users/:id - Delete patient
app.delete('/users/:id', async (req, res) => {
    try {
        const patient = await Patient.findByIdAndDelete(req.params.id);
        if (!patient) return res.status(404).json({ message: 'Patient not found' });
        res.status(200).json({ message: 'Patient deleted successfully', patient });
    } catch (err) {
        console.error('Delete error:', err.message);
        res.status(500).json({ message: 'Server error' });
    }
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`🚀 User management service running on port ${PORT}`);
});
