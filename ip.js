// Vercel Serverless Function: คืนค่า IP สาธารณะของผู้เรียก (ไม่เก็บอะไรไว้เลย)
// อุปกรณ์ที่ใช้ Wi-Fi เดียวกันมักมี IP สาธารณะเดียวกัน จึงใช้จัดกลุ่ม "ใกล้ฉัน"
module.exports = (req, res) => {
  const fwd = (req.headers['x-forwarded-for'] || '').split(',')[0].trim();
  const ip = fwd || req.socket.remoteAddress || '';
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).json({ ip });
};
