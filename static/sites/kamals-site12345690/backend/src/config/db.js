const mongoose = require('mongoose');

const connectDB = async () => {
  const uri = process.env.MONGO_URI;
  if (!uri) {
    console.error('❌ MONGO_URI missing in .env');
    process.exit(1);
  }
  for (let i = 5; i > 0; i--) {
    try {
      const conn = await mongoose.connect(uri);
      console.log(`✅ MongoDB connected: ${conn.connection.host}`);
      return;
    } catch (err) {
      console.error(`❌ MongoDB failed: ${err.message}`);
      if (i === 1) process.exit(1);
      console.log(`🔄 Retrying in 5s... (${i - 1} left)`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
};

module.exports = connectDB;
