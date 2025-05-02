// api-gateway/index.js
const express = require('express');
const axios = require('axios');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const app = express();
app.use(express.json());

// Service URLs (Docker/Kubernetes/Production compatibility)
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:5000';
const VITAL_SERVICE_URL = process.env.VITAL_SERVICE_URL || 'http://vital-signs-service:5001';
const SYMPTOM_SERVICE_URL = process.env.SYMPTOM_SERVICE_URL || 'http://symptom-tracker-service:5002';
const HEALTH_ADVISOR_SERVICE_URL = process.env.HEALTH_ADVISOR_SERVICE_URL || 'http://health-advisor-service:5003';


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

////////////////////////
// USERS SERVICE ROUTES
////////////////////////

// GET /users/:userId
app.get('/users/:userId', (req, res) => {
    proxyRequest(res, USER_SERVICE_URL, `/users/${req.params.userId}`);
});

// POST /users
app.post('/users', (req, res) => {
    proxyRequest(res, USER_SERVICE_URL, '/users', 'POST', req.body);
});

// PUT /users/:id
app.put('/users/:id', (req, res) => {
    proxyRequest(res, USER_SERVICE_URL, `/users/${req.params.id}`, 'PUT', req.body);
});

// DELETE /users/:id
app.delete('/users/:id', (req, res) => {
    proxyRequest(res, USER_SERVICE_URL, `/users/${req.params.id}`, 'DELETE');
});

/////////////////////////
// VITALS SERVICE ROUTES
/////////////////////////

// POST /vitals
app.post('/vitals', (req, res) => {
    proxyRequest(res, VITAL_SERVICE_URL, '/vitals', 'POST', req.body);
});

// GET /vitals/:user_id
app.get('/vitals/:user_id', (req, res) => {
    proxyRequest(res, VITAL_SERVICE_URL, `/vitals/${req.params.user_id}`);
});

// PUT /vitals/:record_id
app.put('/vitals/:record_id', (req, res) => {
    proxyRequest(res, VITAL_SERVICE_URL, `/vitals/${req.params.record_id}`, 'PUT', req.body);
});

//////////////////////////////
// SYMPTOMS SERVICE ROUTES
//////////////////////////////

// POST /symptoms
app.post('/symptoms', (req, res) => {
    proxyRequest(res, SYMPTOM_SERVICE_URL, '/symptoms', 'POST', req.body);
});

// GET /symptoms/aggregate?userId=xyz
app.get('/symptoms/aggregate', (req, res) => {
    const query = req.url.includes('?') ? req.url.substring(req.url.indexOf('?')) : '';
    proxyRequest(res, SYMPTOM_SERVICE_URL, `/symptoms/aggregate${query}`);
});

// GET /symptoms/:userId
app.get('/symptoms/:userId', (req, res) => {
    proxyRequest(res, SYMPTOM_SERVICE_URL, `/symptoms/${req.params.userId}`);
});

//////////////////////////////////
// HEALTH ADVISOR SERVICE ROUTES
//////////////////////////////////

// POST /predict-risk
app.post('/predict-risk', (req, res) => {
    proxyRequest(res, HEALTH_ADVISOR_SERVICE_URL, '/predict-risk', 'POST', req.body);
});

// GET /recommendations/:userId?focusArea=xyz
app.get('/recommendations/:userId', (req, res) => {
    const { focusArea } = req.query;
    const query = focusArea ? `?focusArea=${encodeURIComponent(focusArea)}` : '';
    proxyRequest(res, HEALTH_ADVISOR_SERVICE_URL, `/recommendations/${req.params.userId}${query}`);
});

////////////////////
// HEALTH CHECK
////////////////////
app.get('/', (req, res) => {
    res.send('✅ API Gateway is running');
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 API Gateway running on port ${PORT}`);
});