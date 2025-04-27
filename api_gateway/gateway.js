// api-gateway/index.js
const express = require('express');
const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const app = express();
app.use(express.json());

// Service URLs (Docker/Kubernetes/Production compatibility)
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://localhost:5000';
const VITAL_SERVICE_URL = process.env.VITAL_SERVICE_URL || 'http://localhost:5001';
const SYMPTOM_SERVICE_URL = process.env.SYMPTOM_SERVICE_URL || 'http://localhost:5002';
const HEALTH_ADVISOR_SERVICE_URL = process.env.HEALTH_ADVISOR_SERVICE_URL || 'http://localhost:5003';

// Simple proxy handler
const proxyRequest = async (res, serviceUrl, path, method = 'GET', data = null) => {
    try {
        const response = await axios({
            method,
            url: `${serviceUrl}${path}`,
            data
        });
        res.status(response.status).json(response.data);
    } catch (error) {
        console.error(`❌ Error proxying request to ${serviceUrl}${path}:`, error.message);
        if (error.response) {
            res.status(error.response.status).json(error.response.data);
        } else {
            res.status(500).json({ message: "Internal server error" });
        }
    }
};

// Routes
app.get('/users/:userId', (req, res) => {
    const { userId } = req.params;
    proxyRequest(res, USER_SERVICE_URL, `/users/${userId}`);
});

app.get('/vitals/:userId', (req, res) => {
    const { userId } = req.params;
    proxyRequest(res, VITAL_SERVICE_URL, `/vitals/${userId}`);
});

app.get('/symptoms/:userId', (req, res) => {
    const { userId } = req.params;
    proxyRequest(res, SYMPTOM_SERVICE_URL, `/symptoms/${userId}`);
});

app.post('/predict-risk', (req, res) => {
    proxyRequest(res, HEALTH_ADVISOR_SERVICE_URL, '/predict-risk', 'POST', req.body);
});

app.get('/recommendations/:userId', (req, res) => {
    const { userId } = req.params;
    const { focusArea } = req.query;
    const queryString = focusArea ? `?focusArea=${encodeURIComponent(focusArea)}` : '';
    proxyRequest(res, HEALTH_ADVISOR_SERVICE_URL, `/recommendations/${userId}${queryString}`);
});

// Health check
app.get('/', (req, res) => {
    res.send('✅ API Gateway is running');
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 API Gateway running on port ${PORT}`);
});
