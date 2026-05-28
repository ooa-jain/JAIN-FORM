const mongoose = require('mongoose');
const { v4: uuidv4 } = require('uuid');

const s = new mongoose.Schema({
  sessionId:      { type: String, default: () => uuidv4(), unique: true },
  teacher:        { type: mongoose.Schema.Types.ObjectId, ref: 'Teacher', required: true },
  subject:        { type: String, required: true },
  className:      { type: String, required: true },
  startTime:      { type: Date, default: Date.now },
  endTime:        { type: Date, required: true },
  windowMinutes:  { type: Number, default: 5 },
  rssiThreshold:  { type: Number, default: -65 },
  active:         { type: Boolean, default: true },
  currentToken:   { type: String, default: null },
  tokenExpiresAt: { type: Date, default: null },
}, { timestamps: true });

module.exports = mongoose.model('Session', s);
