const mongoose = require('mongoose');

const s = new mongoose.Schema({
  studentId: { type: mongoose.Schema.Types.ObjectId, ref: 'Student', default: null },
  sessionId: { type: String, default: null },
  reason:    { type: String, required: true },
  deviceId:  { type: String, default: null },
  rssiValue: { type: Number, default: null },
  tokenUsed: { type: String, default: null },
  ipAddress: { type: String, default: '' },
}, { timestamps: true });

module.exports = mongoose.model('RejectedAttempt', s);
