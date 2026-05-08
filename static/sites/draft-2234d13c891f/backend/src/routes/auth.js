const router = require('express').Router();
const jwt = require('jsonwebtoken');
const Joi = require('joi');
const Teacher = require('../models/Teacher');
const Student = require('../models/Student');

router.post('/login', async (req, res) => {
  const { error, value } = Joi.object({
    email:    Joi.string().email().required(),
    password: Joi.string().min(6).required(),
    role:     Joi.string().valid('teacher', 'student').required(),
  }).validate(req.body);
  if (error) return res.status(400).json({ success: false, message: error.details[0].message });

  try {
    const Model = value.role === 'teacher' ? Teacher : Student;
    const user = await Model.findOne({ email: value.email });
    if (!user || !(await user.comparePassword(value.password)))
      return res.status(401).json({ success: false, message: 'Invalid email or password' });

    const payload = {
      id: user._id, name: user.name, email: user.email, role: value.role,
      ...(value.role === 'student' && { deviceId: user.deviceId, rollNumber: user.rollNumber }),
    };
    const token = jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: process.env.JWT_EXPIRES_IN });
    res.json({ success: true, token, user: payload });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

router.post('/register-device', async (req, res) => {
  const { error, value } = Joi.object({
    student_id: Joi.string().required(),
    device_id:  Joi.string().max(128).required(),
  }).validate(req.body);
  if (error) return res.status(400).json({ success: false, message: error.details[0].message });

  try {
    const existing = await Student.findOne({ deviceId: value.device_id, _id: { $ne: value.student_id } });
    if (existing) return res.status(409).json({ success: false, message: 'Device already registered to another student' });
    await Student.findByIdAndUpdate(value.student_id, { deviceId: value.device_id, deviceRegisteredAt: new Date() });
    res.json({ success: true, message: 'Device registered successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

module.exports = router;
