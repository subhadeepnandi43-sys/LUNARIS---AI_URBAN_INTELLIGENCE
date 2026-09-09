$port = 8080
$root = 'c:\Users\SUBHADEEP NANDI\OneDrive\Desktop\LUNARIS'
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
$listener.Start()

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  LUNARIS AI Urban Intelligence - Localhost Dev Server" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " [OK] Server running at: http://localhost:$port/" -ForegroundColor Green
Write-Host "      - Dashboard:       http://localhost:$port/" -ForegroundColor Gray
Write-Host "      - Login Portal:    http://localhost:$port/login" -ForegroundColor Gray
Write-Host "      - Live Camera:     http://localhost:$port/live-monitoring" -ForegroundColor Gray
Write-Host "      - Mobile Edge AI:  http://localhost:$port/mobile-camera" -ForegroundColor Gray
Write-Host "      - Health Check:    http://localhost:$port/api/health" -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Cyan

$mimeTypes = @{
    '.html'  = 'text/html; charset=UTF-8'
    '.js'    = 'application/javascript; charset=UTF-8'
    '.css'   = 'text/css; charset=UTF-8'
    '.json'  = 'application/json; charset=UTF-8'
    '.png'   = 'image/png'
    '.jpg'   = 'image/jpeg'
    '.jpeg'  = 'image/jpeg'
    '.gif'   = 'image/gif'
    '.svg'   = 'image/svg+xml'
    '.ico'   = 'image/x-icon'
    '.woff'  = 'font/woff'
    '.woff2' = 'font/woff2'
    '.ttf'   = 'font/ttf'
}

$searchDirs = @(
    (Join-Path $root 'frontend'),
    (Join-Path $root 'live-camera'),
    (Join-Path $root 'assets'),
    $root
)

while ($listener.IsListening) {
    try {
        $ctx = $listener.GetContext()
        $req = $ctx.Request
        $res = $ctx.Response

        $res.AddHeader('Access-Control-Allow-Origin', '*')
        $res.AddHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        $res.AddHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        $res.AddHeader('Cache-Control', 'no-cache, no-store, must-revalidate')
        $res.AddHeader('Pragma', 'no-cache')
        $res.AddHeader('Expires', '0')

        if ($req.HttpMethod -eq 'OPTIONS') {
            $res.StatusCode = 204
            $res.OutputStream.Close()
            continue
        }

        $urlPath = $req.Url.LocalPath

        if ($urlPath -eq '/api/health') {
            $res.ContentType = 'application/json; charset=UTF-8'
            $res.StatusCode = 200
            $payload = '{"status":"ONLINE","service":"LUNARIS Web Server","port":8080,"structure":"modular"}'
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
            $res.OutputStream.Close()
            Write-Host "[200 API] /api/health" -ForegroundColor Green
            continue
        }

        if ($urlPath -eq '/api/config') {
            $res.ContentType = 'application/json; charset=UTF-8'
            $res.StatusCode = 200
            $payload = '{"supabaseUrl":"https://ecmtwoccsdlhphdlutmz.supabase.co","supabaseKey":"sb_publishable_l4l1lR2MLi_WOwtjs4CxTw_yBjCx01G","projectRef":"ecmtwoccsdlhphdlutmz"}'
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
            $res.OutputStream.Close()
            Write-Host "[200 API] /api/config" -ForegroundColor Green
            continue
        }

        if ($urlPath.StartsWith('/api/ai/')) {
            try {
                $targetAiUrl = "http://127.0.0.1:8001" + $req.Url.PathAndQuery
                $aiReq = [System.Net.HttpWebRequest]::Create($targetAiUrl)
                $aiReq.Method = $req.HttpMethod
                $aiReq.Timeout = 4000
                if ($req.HasEntityBody) {
                    $req.InputStream.CopyTo($aiReq.GetRequestStream())
                }
                $aiRes = $aiReq.GetResponse()
                $res.StatusCode = [int]$aiRes.StatusCode
                $res.ContentType = $aiRes.ContentType
                $aiStream = $aiRes.GetResponseStream()
                $aiStream.CopyTo($res.OutputStream)
                $aiRes.Close()
                $res.OutputStream.Close()
                Write-Host "[AI PROXY 200] $urlPath" -ForegroundColor Green
            } catch {
                $res.ContentType = 'application/json; charset=UTF-8'
                $res.StatusCode = 503
                $errPayload = '{"error":"AI Inference Service Offline"}'
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($errPayload)
                $res.OutputStream.Write($bytes, 0, $bytes.Length)
                $res.OutputStream.Close()
                Write-Host "[AI PROXY 503] $urlPath" -ForegroundColor Yellow
            }
            continue
        }

        if ($urlPath -eq '/' -or $urlPath -eq '') { $urlPath = '/index.html' }
        if ($urlPath -eq '/login') { $urlPath = '/login.html' }
        if ($urlPath -eq '/live-monitoring') { $urlPath = '/live_monitoring.html' }
        if ($urlPath -eq '/mobile-camera') { $urlPath = '/mobile_camera.html' }

        $targetFile = $null
        foreach ($dir in $searchDirs) {
            $candidate = Join-Path $dir $urlPath.TrimStart('/')
            if (Test-Path $candidate -PathType Leaf) {
                $targetFile = $candidate
                break
            }
        }

        if ($targetFile) {
            $ext = [System.IO.Path]::GetExtension($targetFile).ToLower()
            $mime = if ($mimeTypes.ContainsKey($ext)) { $mimeTypes[$ext] } else { 'application/octet-stream' }
            $res.ContentType = $mime
            $res.StatusCode = 200
            $bytes = [System.IO.File]::ReadAllBytes($targetFile)
            $res.OutputStream.Write($bytes, 0, $bytes.Length)
            Write-Host "[200] $urlPath" -ForegroundColor Green
        } else {
            $res.StatusCode = 404
            $msg = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found: $urlPath")
            $res.OutputStream.Write($msg, 0, $msg.Length)
            Write-Host "[404] $urlPath" -ForegroundColor Red
        }
        $res.OutputStream.Close()
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    }
}
