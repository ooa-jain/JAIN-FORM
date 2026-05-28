const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const s = new mongoose.Schema({
  name:               { type: String, required: true },
  rollNumber:         { type: String, required: true, unique: true },
  email:              { type: String, required: true, unique: true, lowercase: true },
  password:           { type: String, required: true },
  deviceId:           { type: String, default: null, sparse: true },
  deviceRegisteredAt: { type: Date, default: null },
}, { timestamps: true });

s.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 10);
  next();
});
s.methods.comparePassword = function(p) { return bcrypt.compare(p, this.password); };

module.exports = mongoose.model('Student', s);
