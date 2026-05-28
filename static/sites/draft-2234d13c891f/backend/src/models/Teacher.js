const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const s = new mongoose.Schema({
  name:       { type: String, required: true },
  email:      { type: String, required: true, unique: true, lowercase: true },
  password:   { type: String, required: true },
  department: { type: String, default: '' },
}, { timestamps: true });

s.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  this.password = await bcrypt.hash(this.password, 10);
  next();
});
s.methods.comparePassword = function(p) { return bcrypt.compare(p, this.password); };

module.exports = mongoose.model('Teacher', s);
