const jwt = require('jsonwebtoken');

const auth = (roles = []) => (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.status(401).json({ success: false, message: 'Access token required' });
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    if (roles.length && !roles.includes(decoded.role))
      return res.status(403).json({ success: false, message: 'Insufficient permissions' });
    next();
  } catch (err) {
    res.status(401).json({ success: false, message: err.name === 'TokenExpiredError' ? 'Token expired' : 'Invalid token' });
  }
};

module.exports = auth;
