module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Content-Type', 'application/json');
  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }
  res.status(200).json({
    status: 'ONLINE',
    service: 'LUNARIS Web Server (Vercel Production)',
    platform: 'Vercel Cloud Edge',
    structure: 'modular (frontend, backend, ai-detection, live-camera, database-supabase, main)',
    timestamp: new Date().toISOString()
  });
};
