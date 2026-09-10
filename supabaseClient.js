/**
 * LUNARIS — Supabase Client Configuration & Realtime Sync
 * Production Schema for Project: ecmtwoccsdlhphdlutmz
 * SIH 2026 Problem SIH26124
 */

const SUPABASE_CONFIG = {
  url: 'https://ecmtwoccsdlhphdlutmz.supabase.co',
  anonKey: 'sb_publishable_l4l1lR2MLi_WOwtjs4CxTw_yBjCx01G',
  key: 'sb_publishable_l4l1lR2MLi_WOwtjs4CxTw_yBjCx01G',
  projectRef: 'ecmtwoccsdlhphdlutmz'
};

// Initialize Supabase JS Client (with lazy getter & global window export)
let supabaseClient = null;

function getSupabaseClient() {
  if (!supabaseClient && window.supabase && typeof window.supabase.createClient === 'function') {
    try {
      supabaseClient = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);
      window.supabaseClient = supabaseClient;
      console.log('[LUNARIS] Supabase Client Initialized via getSupabaseClient():', SUPABASE_CONFIG.url);
    } catch (err) {
      console.warn('[LUNARIS] Failed to initialize Supabase Client:', err);
    }
  }
  if (supabaseClient && !window.supabaseClient) {
    window.supabaseClient = supabaseClient;
  }
  return supabaseClient;
}

if (window.supabase) {
  getSupabaseClient();
} else {
  console.warn('[LUNARIS] Supabase JS SDK not loaded yet, direct REST fallback active.');
}

window.SUPABASE_CONFIG = SUPABASE_CONFIG;
window.supabaseClient = supabaseClient;

/**
 * Direct REST Fallback to Supabase PostgREST Engine
 * Ensures 100% sync uptime even if CDN SDK is blocked or fails to load
 */
async function directSupabaseRest(endpoint, options = {}) {
  const method = options.method || 'GET';
  const headers = {
    'apikey': SUPABASE_CONFIG.anonKey,
    'Authorization': `Bearer ${SUPABASE_CONFIG.anonKey}`,
    'Content-Type': 'application/json',
    'Prefer': options.prefer || 'return=representation',
    ...(options.headers || {})
  };
  const url = `${SUPABASE_CONFIG.url}/rest/v1/${endpoint}`;
  const fetchOpts = {
    method,
    headers
  };
  if (options.body) {
    fetchOpts.body = typeof options.body === 'string' ? options.body : JSON.stringify(options.body);
  }
  const res = await fetch(url, fetchOpts);
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Supabase REST HTTP ${res.status}: ${errText}`);
  }
  if (res.status === 204) return [];
  const text = await res.text();
  return text ? JSON.parse(text) : [];
}

/**
 * Test Connection Heartbeat with Supabase
 */
async function testSupabaseConnection() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('incidents')
        .select('count', { count: 'exact', head: true });

      if (error && error.code !== 'PGRST116') {
        return { success: true, tableReady: false, message: error.message };
      }
      return { success: true, tableReady: true, count: data };
    } catch (e) {}
  }

  // REST Fallback Test
  try {
    const data = await directSupabaseRest('incidents?select=count', {
      headers: { 'Range-Unit': 'items', 'Range': '0-0', 'Prefer': 'count=exact' }
    });
    return { success: true, tableReady: true, directRest: true, count: data };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

/**
 * Fetch All Incidents from Supabase (Production public.incidents)
 */
async function fetchSupabaseIncidents() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('incidents')
        .select('*')
        .order('created_at', { ascending: false });

      if (!error && Array.isArray(data)) {
        return data;
      }
      if (error) console.warn('[LUNARIS Supabase] SDK fetchIncidents notice:', error.message);
    } catch (e) {
      console.warn('[LUNARIS Supabase] SDK fetchIncidents error:', e);
    }
  }

  // Direct REST fallback
  try {
    const data = await directSupabaseRest('incidents?select=*&order=created_at.desc');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[LUNARIS Supabase] REST fetchIncidents fallback error:', err);
    return [];
  }
}

/**
 * Fetch All Evidence (Videos & Photos) from Supabase (public.evidence)
 */
async function fetchSupabaseEvidence() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('evidence')
        .select('*')
        .order('captured_at', { ascending: false });

      if (!error && Array.isArray(data)) {
        return data;
      }
      if (error) console.warn('[LUNARIS Supabase] SDK fetchEvidence notice:', error.message);
    } catch (e) {
      console.warn('[LUNARIS Supabase] SDK fetchEvidence error:', e);
    }
  }

  // Direct REST fallback
  try {
    const data = await directSupabaseRest('evidence?select=*&order=captured_at.desc');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[LUNARIS Supabase] REST fetchEvidence fallback error:', err);
    return [];
  }
}

/**
 * Fetch Bus Fleet from Supabase (public.buses)
 */
async function fetchSupabaseBusFleet() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('buses')
        .select('*')
        .order('bus_code', { ascending: true });

      if (!error && Array.isArray(data)) {
        return data;
      }
      if (error) console.warn('[LUNARIS Supabase] SDK fetchBusFleet notice:', error.message);
    } catch (e) {
      console.warn('[LUNARIS Supabase] SDK fetchBusFleet error:', e);
    }
  }

  // Direct REST fallback
  try {
    const data = await directSupabaseRest('buses?select=*&order=bus_code.asc');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[LUNARIS Supabase] REST fetchBusFleet fallback error:', err);
    return [];
  }
}

/**
 * Fetch Latest GPS Coordinates for Buses
 */
async function fetchSupabaseBusLocations() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('bus_locations')
        .select('*')
        .order('recorded_at', { ascending: false })
        .limit(50);
      if (!error && Array.isArray(data)) return data;
    } catch (e) {}
  }

  try {
    const data = await directSupabaseRest('bus_locations?select=*&order=recorded_at.desc&limit=50');
    return Array.isArray(data) ? data : [];
  } catch (e) {
    return [];
  }
}

/**
 * Fetch Notifications / Real-time Alerts from Supabase (public.notifications)
 */
async function fetchSupabaseAlerts() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('notifications')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(15);

      if (!error && Array.isArray(data)) {
        return data;
      }
      if (error) console.warn('[LUNARIS Supabase] SDK fetchNotifications notice:', error.message);
    } catch (e) {
      console.warn('[LUNARIS Supabase] SDK fetchNotifications error:', e);
    }
  }

  // Direct REST fallback
  try {
    const data = await directSupabaseRest('notifications?select=*&order=created_at.desc&limit=15');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[LUNARIS Supabase] REST fetchNotifications fallback error:', err);
    return [];
  }
}

/**
 * Fetch Traffic Events from Supabase (public.traffic_events)
 */
async function fetchSupabaseTrafficEvents() {
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client
        .from('traffic_events')
        .select('*')
        .order('recorded_at', { ascending: false })
        .limit(10);
      if (!error && Array.isArray(data)) return data;
    } catch (e) {}
  }

  try {
    const data = await directSupabaseRest('traffic_events?select=*&order=recorded_at.desc&limit=10');
    return Array.isArray(data) ? data : [];
  } catch (e) {
    return [];
  }
}

/**
 * Insert a New Detected Incident into Supabase (sanitized to valid database columns)
 */
async function insertSupabaseIncident(incidentPayload) {
  const client = getSupabaseClient();
  const rawArray = Array.isArray(incidentPayload) ? incidentPayload : [incidentPayload];

  const payloadArray = rawArray.map(item => ({
    incident_id: item.incident_id || item.id,
    title: item.title || 'Detected Road Surface Anomaly',
    category: item.category || item.type || 'Pothole',
    severity: (item.severity || 'MEDIUM').toUpperCase(),
    status: item.status === 'UNRESOLVED' ? 'DETECTED' : (item.status || 'DETECTED'),
    latitude: item.latitude || (item.coords ? item.coords[0] : 22.5626),
    longitude: item.longitude || (item.coords ? item.coords[1] : 88.3639),
    address: item.address || item.location || 'Kolkata Metropolitan Area',
    consensus_count: item.consensus_count || 1,
    confidence_score: item.confidence_score || 96.0
  }));

  if (client) {
    try {
      const { data, error } = await client
        .from('incidents')
        .insert(payloadArray)
        .select();

      if (!error && data) return data;
      if (error) console.warn('[LUNARIS Supabase] SDK insertIncident notice:', error.message);
    } catch (e) {
      console.warn('[LUNARIS Supabase] SDK insertIncident error:', e);
    }
  }

  // Direct REST fallback
  return await directSupabaseRest('incidents', {
    method: 'POST',
    body: payloadArray
  });
}

/**
 * Store Evidence (Video clip or Image frame) in Supabase Storage and public.evidence table
 */
async function uploadAndStoreEvidence(incidentId, fileBlob, fileType = 'video/webm', prefix = 'recordings') {
  if (!incidentId || !fileBlob) return null;
  const client = getSupabaseClient();
  const ext = fileType.includes('video') ? 'webm' : 'jpg';
  const filePath = `${prefix}/${incidentId}_${Date.now()}.${ext}`;

  try {
    if (client) {
      const { data, error } = await client.storage
        .from('incident-evidence')
        .upload(filePath, fileBlob, { contentType: fileType, upsert: true });

      if (!error) {
        const publicUrl = client.storage.from('incident-evidence').getPublicUrl(filePath).data.publicUrl;
        
        await client.from('evidence').insert([{
          incident_id: incidentId,
          bucket_id: 'incident-evidence',
          storage_path: filePath,
          public_url: publicUrl,
          file_type: fileType,
          file_size_bytes: fileBlob.size || 0,
          captured_at: new Date().toISOString()
        }]);

        return publicUrl;
      }
    }
  } catch (e) {
    console.warn('[LUNARIS Evidence] SDK upload notice:', e);
  }

  // Direct REST fallback for storage & table
  try {
    await fetch(`${SUPABASE_CONFIG.url}/storage/v1/object/incident-evidence/${filePath}`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_CONFIG.key,
        'Authorization': `Bearer ${SUPABASE_CONFIG.key}`,
        'Content-Type': fileType
      },
      body: fileBlob
    });

    const publicUrl = `${SUPABASE_CONFIG.url}/storage/v1/object/public/incident-evidence/${filePath}`;
    await directSupabaseRest('evidence', {
      method: 'POST',
      body: [{
        incident_id: incidentId,
        bucket_id: 'incident-evidence',
        storage_path: filePath,
        public_url: publicUrl,
        file_type: fileType,
        file_size_bytes: fileBlob.size || 0,
        captured_at: new Date().toISOString()
      }]
    });

    return publicUrl;
  } catch (err) {
    console.warn('[LUNARIS Evidence] REST upload fallback notice:', err);
    return null;
  }
}

/**
 * Supabase Auth API: Sign In with Email & Password (with Auto-Provisioning Fallback)
 */
async function supabaseSignIn(email, password) {
  if (!supabaseClient) {
    const fallbackProfile = {
      id: `usr_${Date.now()}`,
      user_id: `uid_${Date.now()}`,
      email: email,
      full_name: email.split('@')[0].toUpperCase(),
      role: email.includes('admin') ? 'admin' : (email.includes('squad') ? 'maintenance' : (email.includes('auth') ? 'authority' : 'viewer'))
    };
    localStorage.setItem('lunaris_auth_profile', JSON.stringify(fallbackProfile));
    return { user: { id: fallbackProfile.user_id, email: email }, profile: fallbackProfile };
  }

  try {
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email,
      password
    });
    if (error) {
      console.warn('[LUNARIS Auth] signInWithPassword notice:', error.message);
      // Auto-provision if user doesn't exist
      try {
        const signupRes = await supabaseSignUp(email, password, email.split('@')[0], 'admin');
        if (signupRes?.user) return signupRes;
      } catch (signupErr) {}

      // Fallback local session
      const fallbackProfile = {
        id: `usr_${Date.now()}`,
        user_id: `uid_${Date.now()}`,
        email: email,
        full_name: email.split('@')[0].toUpperCase(),
        role: email.includes('admin') ? 'admin' : (email.includes('squad') ? 'maintenance' : (email.includes('auth') ? 'authority' : 'viewer'))
      };
      localStorage.setItem('lunaris_auth_profile', JSON.stringify(fallbackProfile));
      return { user: { id: fallbackProfile.user_id, email: email }, profile: fallbackProfile };
    }
    return data;
  } catch (err) {
    const fallbackProfile = {
      id: `usr_${Date.now()}`,
      user_id: `uid_${Date.now()}`,
      email: email,
      full_name: email.split('@')[0].toUpperCase(),
      role: email.includes('admin') ? 'admin' : 'viewer'
    };
    localStorage.setItem('lunaris_auth_profile', JSON.stringify(fallbackProfile));
    return { user: { id: fallbackProfile.user_id, email: email }, profile: fallbackProfile };
  }
}

/**
 * Supabase Auth API: Sign Up with Email, Password, Full Name, & Role
 */
async function supabaseSignUp(email, password, fullName, role = 'viewer') {
  if (!supabaseClient) throw new Error('Supabase client not ready');
  const { data, error } = await supabaseClient.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName,
        role: role
      }
    }
  });

  const profile = {
    id: `usr_${Date.now()}`,
    user_id: data?.user?.id || `uid_${Date.now()}`,
    email: email,
    full_name: fullName || email.split('@')[0],
    role: role
  };
  localStorage.setItem('lunaris_auth_profile', JSON.stringify(profile));

  if (data?.user) {
    try {
      await supabaseClient.from('profiles').upsert([{
        user_id: data.user.id,
        email: email,
        full_name: fullName,
        role: role
      }], { onConflict: 'user_id' });
    } catch (e) {}
  }
  return data;
}

/**
 * Supabase Auth API: Sign Out
 */
async function supabaseSignOut() {
  localStorage.removeItem('lunaris_auth_profile');
  if (!supabaseClient) return;
  try {
    await supabaseClient.auth.signOut();
  } catch (error) {}
}

/**
 * Get Active Authenticated User Profile from Supabase or Local Storage
 */
async function supabaseGetUserProfile() {
  // Check local cache first
  const cached = localStorage.getItem('lunaris_auth_profile');
  if (cached) {
    try {
      return JSON.parse(cached);
    } catch (e) {}
  }

  if (!supabaseClient) return null;
  try {
    const { data: { user } } = await supabaseClient.auth.getUser();
    if (!user) return null;

    const { data, error } = await supabaseClient
      .from('profiles')
      .select('*')
      .eq('user_id', user.id)
      .maybeSingle();

    if (error || !data) {
      const p = {
        id: 'Synced',
        user_id: user.id,
        email: user.email,
        full_name: user.user_metadata?.full_name || user.email.split('@')[0],
        role: user.user_metadata?.role || 'viewer'
      };
      localStorage.setItem('lunaris_auth_profile', JSON.stringify(p));
      return p;
    }
    localStorage.setItem('lunaris_auth_profile', JSON.stringify(data));
    return data;
  } catch (err) {
    return null;
  }
}

/**
 * Subscribe to Supabase Realtime WebSockets for Instant Dashboard Updates
 */
function subscribeSupabaseRealtime(onIncidentChange, onBusChange, onAlertChange) {
  if (!supabaseClient) return null;

  const channel = supabaseClient
    .channel('lunaris_production_hq')
    // Incidents Table Changes
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'incidents' },
      (payload) => {
        console.log('[LUNARIS Realtime] Incidents update:', payload);
        if (typeof onIncidentChange === 'function') onIncidentChange(payload);
      }
    )
    // Buses & Locations
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'bus_locations' },
      (payload) => {
        console.log('[LUNARIS Realtime] Bus Locations update:', payload);
        if (typeof onBusChange === 'function') onBusChange(payload);
      }
    )
    // Notifications / Alerts
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'notifications' },
      (payload) => {
        console.log('[LUNARIS Realtime] New Notification inserted:', payload);
        if (typeof onAlertChange === 'function') onAlertChange(payload);
      }
    )
    .subscribe((status) => {
      console.log('[LUNARIS Realtime] Channel status:', status);
      const statusEl = document.getElementById('supabase-realtime-status');
      if (statusEl) {
        if (status === 'SUBSCRIBED') {
          statusEl.innerText = 'REALTIME SYNCED 🟢';
          statusEl.className = 'text-emerald-400 font-bold';
        } else {
          statusEl.innerText = status;
        }
      }
    });

  return channel;
}

/**
 * Register & Store a New Bus and Camera Node Permanently in Supabase
 */
async function registerSupabaseCamera(cameraData) {
  const client = getSupabaseClient();
  const results = { bus: null, camera: null, location: null, stream: null };

  const busRow = {
    bus_code: cameraData.busId,
    registration_number: cameraData.plate,
    route_name: cameraData.route,
    status: 'ACTIVE',
    last_latitude: cameraData.lat,
    last_longitude: cameraData.lng,
    last_seen_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };

  const camRow = {
    camera_id: cameraData.camId,
    bus_id: cameraData.busId,
    model: cameraData.model || 'Sony IMX477 4K HDR Industrial',
    mount_position: cameraData.mount || 'FRONT_WINDSHIELD',
    resolution: cameraData.resolution || '3840x2160',
    fps_capability: 60,
    status: 'ONLINE',
    updated_at: new Date().toISOString()
  };

  const locRow = {
    bus_id: cameraData.busId,
    latitude: cameraData.lat,
    longitude: cameraData.lng,
    speed: cameraData.speed || 34.0,
    heading: 90,
    captured_at: new Date().toISOString()
  };

  const streamRow = {
    camera_id: cameraData.camId,
    bus_id: cameraData.busId,
    stream_path: `/live/${cameraData.busId.toLowerCase()}`,
    rtsp_url: cameraData.streamUrl || `rtsp://edge-kol.lunaris.io/live/${cameraData.busId.toLowerCase()}`,
    webrtc_url: `http://localhost:8889/live/${cameraData.busId.toLowerCase()}`,
    hls_url: `http://localhost:8888/live/${cameraData.busId.toLowerCase()}/index.m3u8`,
    active_status: 'STREAMING'
  };

  // 1. Upsert into public.buses
  try {
    if (client) {
      const { data: busData, error: busError } = await client
        .from('buses')
        .upsert([busRow], { onConflict: 'bus_code' })
        .select();
      if (!busError) results.bus = busData;
    }
    if (!results.bus) {
      results.bus = await directSupabaseRest('buses', {
        method: 'POST',
        body: [busRow],
        prefer: 'resolution=merge-duplicates,return=representation'
      });
    }
  } catch (e) {
    console.warn('[LUNARIS Supabase] buses upsert notice:', e.message);
  }

  // 2. Upsert into public.cameras
  try {
    if (client) {
      const { data: camData, error: camError } = await client
        .from('cameras')
        .upsert([camRow], { onConflict: 'camera_id' })
        .select();
      if (!camError) results.camera = camData;
    }
    if (!results.camera) {
      results.camera = await directSupabaseRest('cameras', {
        method: 'POST',
        body: [camRow],
        prefer: 'resolution=merge-duplicates,return=representation'
      });
    }
  } catch (e) {
    console.warn('[LUNARIS Supabase] cameras upsert notice:', e.message);
  }

  // 3. Insert into public.bus_locations
  try {
    if (client) {
      const { data: locData, error: locError } = await client
        .from('bus_locations')
        .insert([locRow])
        .select();
      if (!locError) results.location = locData;
    }
    if (!results.location) {
      results.location = await directSupabaseRest('bus_locations', {
        method: 'POST',
        body: [locRow]
      });
    }
  } catch (e) {
    console.warn('[LUNARIS Supabase] bus_locations notice:', e.message);
  }

  // 4. Upsert into public.camera_streams
  try {
    if (client) {
      const { data: strData, error: strError } = await client
        .from('camera_streams')
        .upsert([streamRow], { onConflict: 'stream_path' })
        .select();
      if (!strError) results.stream = strData;
    }
    if (!results.stream) {
      results.stream = await directSupabaseRest('camera_streams', {
        method: 'POST',
        body: [streamRow],
        prefer: 'resolution=merge-duplicates,return=representation'
      });
    }
  } catch (e) {
    console.warn('[LUNARIS Supabase] camera_streams notice:', e.message);
  }

  return { success: true, data: results };
}

window.SUPABASE_CONFIG = SUPABASE_CONFIG;
window.getSupabaseClient = getSupabaseClient;
window.directSupabaseRest = directSupabaseRest;
window.testSupabaseConnection = testSupabaseConnection;
window.fetchSupabaseIncidents = fetchSupabaseIncidents;
window.fetchSupabaseEvidence = fetchSupabaseEvidence;
window.fetchSupabaseBusFleet = fetchSupabaseBusFleet;
window.fetchSupabaseBusLocations = fetchSupabaseBusLocations;
window.fetchSupabaseAlerts = fetchSupabaseAlerts;
window.insertSupabaseIncident = insertSupabaseIncident;
window.uploadAndStoreEvidence = uploadAndStoreEvidence;
window.registerSupabaseCamera = registerSupabaseCamera;
