module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Content-Type', 'application/json');
  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }
  res.status(200).json({
    supabaseUrl: 'https://ecmtwoccsdlhphdlutmz.supabase.co',
    supabaseKey: 'sb_publishable_l4l1lR2MLi_WOwtjs4CxTw_yBjCx01G',
    projectRef: 'ecmtwoccsdlhphdlutmz'
  });
};
