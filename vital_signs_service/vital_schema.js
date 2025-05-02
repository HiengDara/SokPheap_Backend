const mongoose = require('mongoose');

const VitalSignsSchema = new mongoose.Schema({
    user_id: { type: String, required: true },
    systolic_bp: { type: Number, required: true },
    diastolic_bp: { type: Number, required: true },
    heart_rate: { type: Number, required: true },
    blood_glucose: { type: Number },
    temperature: { type: Number },
    recorded_at: { type: Date, default: Date.now }
});

module.exports = mongoose.model('VitalSign', VitalSignsSchema);
