require('dotenv').config();
const mongoose = require('mongoose');
const Teacher = require('../models/Teacher');
const Student = require('../models/Student');

const seed = async () => {
  console.log('🔄 Connecting to MongoDB Atlas...');
  await mongoose.connect(process.env.MONGO_URI);
  console.log('✅ Connected!');

  await Teacher.deleteMany({});
  await Student.deleteMany({});
  console.log('🗑️  Cleared old data');

  await Teacher.create({
    name: 'Prof. Rajan Kumar',
    email: 'rajan@college.edu',
    password: 'teacher123',
    department: 'Computer Science',
  });
  console.log('✅ Teacher: rajan@college.edu / teacher123');

  const students = [
    { name: 'Arjun Sharma', rollNumber: 'CS001', email: 'arjun@college.edu', deviceId: 'DEV-AABBCC001' },
    { name: 'Priya Patel',  rollNumber: 'CS002', email: 'priya@college.edu',  deviceId: 'DEV-AABBCC002' },
    { name: 'Rohit Kumar',  rollNumber: 'CS003', email: 'rohit@college.edu',  deviceId: 'DEV-AABBCC003' },
    { name: 'Sneha Iyer',   rollNumber: 'CS004', email: 'sneha@college.edu',  deviceId: 'DEV-AABBCC004' },
    { name: 'Kavya Nair',   rollNumber: 'CS005', email: 'kavya@college.edu',  deviceId: 'DEV-AABBCC005' },
    { name: 'Vikram Das',   rollNumber: 'CS006', email: 'vikram@college.edu', deviceId: 'DEV-AABBCC006' },
  ];

  for (const s of students) {
    await Student.create({ ...s, password: 'student123', deviceRegisteredAt: new Date() });
    console.log(`✅ Student: ${s.email} / student123`);
  }

  console.log('\n🌱 Seed complete!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('Teacher : rajan@college.edu / teacher123');
  console.log('Student : arjun@college.edu / student123');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  await mongoose.disconnect();
  process.exit(0);
};

seed().catch(err => {
  console.error('❌ Seed failed:', err.message);
  console.error('👉 Make sure you are on mobile hotspot, not college WiFi');
  process.exit(1);
});
