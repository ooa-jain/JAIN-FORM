const router = require('express').Router();
const Joi = require('joi');
const Session = require('../models/Session');
const Student = require('../models/Student');
const Attendance = require('../models/Attendance');
const RejectedAttempt = require('../models/RejectedAttempt');
const auth = require('../middleware/auth');
const { validateToken } = require('../utils/tokenService');

router.post('/mark', auth(['student']), async (req, res) => {
  const { error, value } = Joi.object({
    session_id: Joi.string().required(),
    token:      Joi.string().length(6).required(),
    rssi:       Joi.number().min(-120).max(0).required(),
    device_id:  Joi.string().max(128).required(),
  }).validate(req.body);
  if (error) return res.status(400).json({ success: false, message: error.details[0].message });

  const ip = req.ip;
  const reject = async (reason) => {
    await RejectedAttempt.create({
      studentId: req.user.id, sessionId: value.session_id, reason,
      deviceId: value.device_id, rssiValue: value.rssi, tokenUsed: value.token, ipAddress: ip,
    }).catch(console.error);
    console.warn(`[REJECT] ${req.user.name}: ${reason}`);
    return res.status(403).json({ success: false, message: reason });
  };

  try {
    // CHECK 1: Session active
    const session = await Session.findOne({ sessionId: value.session_id, active: true, endTime: { $gt: new Date() } });
    if (!session) return reject('Session is not active or has expired');

    // CHECK 2: Token valid
    const tokenOk = await validateToken(value.session_id, value.token);
    if (!tokenOk) return reject('Invalid or expired token. Tokens rotate every 15 seconds.');

    // CHECK 3: RSSI proximity
    if (value.rssi < session.rssiThreshold)
      return reject(`Signal too weak (${value.rssi} dBm). Must be ≥ ${session.rssiThreshold} dBm. Move closer.`);

    // CHECK 4: Device registered to this student
    const student = await Student.findById(req.user.id);
    if (!student.deviceId) return reject('No device registered. Register your device first.');
    if (student.deviceId !== value.device_id) return reject('Device not registered to your account. Proxy detected.');

    // CHECK 5: Not already marked
    const already = await Attendance.findOne({ student: req.user.id, sessionId: value.session_id });
    if (already) return res.status(409).json({ success: false, message: 'Attendance already marked for this session' });

    // ALL PASSED
    const record = await Attendance.create({
      student: req.user.id, session: session._id, sessionId: value.session_id,
      deviceId: value.device_id, rssiValue: value.rssi, tokenUsed: value.token,
      ipAddress: ip, status: 'present',
    });

    console.log(`[MARKED] ${student.name} (${student.rollNumber}) — ${session.subject}`);
    res.status(201).json({
      success: true, message: 'Attendance marked successfully',
      record: {
        student_name: student.name, roll_number: student.rollNumber,
        session_id: value.session_id, subject: session.subject,
        timestamp: record.createdAt, status: 'present',
      },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// Student's own history
router.get('/my', auth(['student']), async (req, res) => {
  try {
    const records = await Attendance.find({ student: req.user.id })
      .populate({ path: 'session', populate: { path: 'teacher', select: 'name' } })
      .sort({ createdAt: -1 });
    res.json({
      success: true, total: records.length,
      records: records.map(r => ({
        id: r._id, subject: r.session?.subject, class_name: r.session?.className,
        teacher_name: r.session?.teacher?.name, rssi_value: r.rssiValue,
        timestamp: r.createdAt, status: r.status,
      })),
    });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// Full report (teacher)
router.get('/report/:session_id', auth(['teacher']), async (req, res) => {
  try {
    const present = await Attendance.find({ sessionId: req.params.session_id })
      .populate('student', 'name rollNumber');
    const all = await Student.find({}, 'name rollNumber');
    const presentIds = new Set(present.map(r => r.student._id.toString()));
    const absent = all.filter(s => !presentIds.has(s._id.toString()));
    res.json({
      success: true,
      present: present.map(r => ({ name: r.student.name, roll_number: r.student.rollNumber, rssi_value: r.rssiValue, timestamp: r.createdAt })),
      absent: absent.map(s => ({ name: s.name, roll_number: s.rollNumber })),
      present_count: present.length, absent_count: absent.length, total: all.length,
    });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

module.exports = router;
