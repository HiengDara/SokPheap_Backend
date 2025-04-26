const mongoose = require('mongoose');

const patientSchema = new mongoose.Schema({
  firstName: {
    type: String,
    required: [true, 'First name is required'],
    trim: true,
    maxlength: [50, 'First name cannot exceed 50 characters']
  },
  lastName: {
    type: String,
    required: [true, 'Last name is required'],
    trim: true,
    maxlength: [50, 'Last name cannot exceed 50 characters']
  },
  age: {
    type: Number,
    required: true,
    min: [0, 'Age must be positive'],
    max: [120, 'Age must be reasonable']
  },
  gender: {
    type: String,
    enum: ['male', 'female', 'other', 'prefer-not-to-say'],
    required: true
  },
  contact: {
    email: {
      type: String,
      trim: true,
      lowercase: true,
      validate: {
        validator: (v) => /^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/.test(v),
        message: 'Invalid email format'
      }
    },
    phone: {
      type: String,
      validate: {
        validator: (v) => /^\+?[0-9]{10,15}$/.test(v),
        message: 'Phone number must be 10-15 digits'
      }
    }
  },
  address: {
    street: String,
    city: String,
    postalCode: String,
    country: {
      type: String,
      default: 'Cambodia'
    }
  },
  isActive: {
    type: Boolean,
    default: true
  },
  registeredBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Admin'
  }
}, {
  timestamps: true,  // Adds createdAt and updatedAt fields
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Add index for faster search
patientSchema.index({ firstName: 'text', lastName: 'text' });

// Virtual for full name
patientSchema.virtual('fullName').get(function () {
  return `${this.firstName} ${this.lastName}`;
});

// Query helper for active patients
patientSchema.query.active = function () {
  return this.where({ isActive: true });
};

module.exports = mongoose.model('Patient', patientSchema);