const mongoose = require('mongoose');

const s = new mongoose.Schema({
  student:   { type: mongoose.Schema.Types.ObjectId, ref: 'Student', required: true },
  session:   { type: mongoose.Schema.Types.ObjectId, ref: 'Session', required: true },
  sessionId: { type: String, required: true },
  deviceId:  { type: String, required: true },
  rssiValue: { type: Number, required: true },
  tokenUsed: { type: String, required: true },
  ipAddress: { type: String, default: '' },
  status:    { type: String, default: 'present' },
}, { timestamps: true });

s.index({ student: 1, session: 1 }, { unique: true });

module.exports = mongoose.model('Attendance', s);
