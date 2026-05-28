require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const connectDB = require('./config/db');

const app = express();
connectDB();

app.use(helmet());
app.use(cors({ origin: '*' }));
app.use(express.json());
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 200 }));
app.use((req, _, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

app.use('/api/auth',       require('./routes/auth'));
app.use('/api/sessions',   require('./routes/sessions'));
app.use('/api/attendance', require('./routes/attendance'));
app.get('/health', (_, res) => res.json({ status: 'ok', time: new Date() }));
app.use((_, res) => res.status(404).json({ success: false, message: 'Route not found' }));
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ success: false, message: 'Internal server error' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`\n🚀 Server: http://localhost:${PORT}`);
  console.log(`🔗 Health: http://localhost:${PORT}/health\n`);
});
