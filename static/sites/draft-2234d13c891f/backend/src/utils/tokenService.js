const crypto = require('crypto');
const Session = require('../models/Session');

const generateToken = () => crypto.randomBytes(3).toString('hex').toUpperCase();

const rotateToken = async (sessionId) => {
  const token = generateToken();
  const secs = parseInt(process.env.TOKEN_ROTATE_SECONDS) || 15;
  const expiresAt = new Date(Date.now() + secs * 1000);
  const session = await Session.findOneAndUpdate(
    { sessionId },
    { currentToken: token, tokenExpiresAt: expiresAt },
    { new: true }
  );
  return { token, expiresAt, session };
};

const validateToken = async (sessionId, tokenToCheck) => {
  const session = await Session.findOne({ sessionId, active: true });
  if (!session) return false;
  if (session.currentToken !== tokenToCheck) return false;
  if (!session.tokenExpiresAt || new Date() > session.tokenExpiresAt) return false;
  return true;
};

module.exports = { generateToken, rotateToken, validateToken };
