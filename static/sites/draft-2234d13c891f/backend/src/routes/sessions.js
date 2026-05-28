const router = require('express').Router();
const Joi = require('joi');
const Session = require('../models/Session');
const Attendance = require('../models/Attendance');
const auth = require('../middleware/auth');
const { rotateToken } = require('../utils/tokenService');

// Start session (teacher)
router.post('/start', auth(['teacher']), async (req, res) => {
  const { error, value } = Joi.object({
    subject:        Joi.string().max(100).required(),
    class_name:     Joi.string().max(50).required(),
    window_minutes: Joi.number().min(1).max(60).default(5),
    rssi_threshold: Joi.number().min(-100).max(-30).default(-65),
  }).validate(req.body);
  if (error) return res.status(400).json({ success: false, message: error.details[0].message });

  try {
    await Session.updateMany({ teacher: req.user.id, active: true }, { active: false, endTime: new Date() });

    const endTime = new Date(Date.now() + value.window_minutes * 60 * 1000);
    const session = await Session.create({
      teacher: req.user.id, subject: value.subject, className: value.class_name,
      endTime, windowMinutes: value.window_minutes, rssiThreshold: value.rssi_threshold,
    });

    const { token, expiresAt } = await rotateToken(session.sessionId);

    setTimeout(async () => {
      await Session.findOneAndUpdate({ sessionId: session.sessionId, active: true }, { active: false });
    }, value.window_minutes * 60 * 1000);

    res.status(201).json({
      success: true,
      session: {
        session_id: session.sessionId, subject: session.subject,
        class_name: session.className, start_time: session.startTime,
        end_time: endTime, window_minutes: value.window_minutes,
        rssi_threshold: value.rssi_threshold,
      },
      token: { value: token, expires_at: expiresAt },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// Stop session (teacher)
router.post('/:id/stop', auth(['teacher']), async (req, res) => {
  try {
    const session = await Session.findOneAndUpdate(
      { sessionId: req.params.id, teacher: req.user.id, active: true },
      { active: false, endTime: new Date() }, { new: true }
    );
    if (!session) return res.status(404).json({ success: false, message: 'Active session not found' });
    res.json({ success: true, message: 'Session stopped' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// Get/rotate token (teacher polls every ~13s)
router.get('/:id/token', auth(['teacher']), async (req, res) => {
  try {
    const session = await Session.findOne({ sessionId: req.params.id, active: true });
    if (!session) return res.status(404).json({ success: false, message: 'Session not found' });

    let token = session.currentToken;
    let expiresAt = session.tokenExpiresAt;

    if (!token || !expiresAt || new Date() >= expiresAt) {
      const result = await rotateToken(req.params.id);
      token = result.token;
      expiresAt = result.expiresAt;
    }
    res.json({ success: true, token, expires_at: expiresAt });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// Get attendance list (teacher)
router.get('/:id/attendance', auth(['teacher']), async (req, res) => {
  try {
    const records = await Attendance.find({ sessionId: req.params.id })
      .populate('student', 'name rollNumber').sort({ createdAt: 1 });
    const session = await Session.findOne({ sessionId: req.params.id });
    res.json({
      success: true, session,
      attendance: records.map(r => ({
        name: r.student.name, roll_number: r.student.rollNumber,
        rssi_value: r.rssiValue, device_id: r.deviceId,
        timestamp: r.createdAt, status: r.status,
      })),
      count: records.length,
    });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// Check active session (student)
router.get('/active', auth(['student', 'teacher']), async (req, res) => {
  try {
    const session = await Session.findOne({ active: true, endTime: { $gt: new Date() } })
      .populate('teacher', 'name').sort({ createdAt: -1 });
    if (!session) return res.json({ success: true, active: false });
    res.json({
      success: true, active: true,
      session: {
        session_id: session.sessionId, subject: session.subject,
        class_name: session.className, end_time: session.endTime,
        rssi_threshold: session.rssiThreshold, teacher_name: session.teacher?.name,
      },
    });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

module.exports = router;
