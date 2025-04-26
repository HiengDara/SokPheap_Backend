const mongoose = require('mongoose');

const symptomSchema = new mongoose.Schema({
    userId: {
        type: String,
        required: [true, 'User ID is required'],
        index: true
    },
    symptom: {
        type: String,
        required: [true, 'Symptom description is required'],
        trim: true,
        maxlength: [100, 'Cannot exceed 100 characters'],
        text: true // Enable text search
    },
    severity: {
        type: Number,
        required: true,
        min: [1, 'Minimum severity is 1'],
        max: [10, 'Maximum severity is 10']
    },
    duration: {
        type: String,
        enum: {
            values: ['acute', 'chronic', 'recurring'],
            message: 'Invalid duration type'
        },
        default: 'acute'
    },
    notes: String,
    recordedAt: {
        type: Date,
        default: Date.now
    }
}, {
    timestamps: true,
    toJSON: { virtuals: true }
});

// Compound index for faster queries
symptomSchema.index({ userId: 1, recordedAt: -1 });

module.exports = mongoose.model('Symptom', symptomSchema);