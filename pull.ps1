$repo    = 'c:\Users\SUBHADEEP NANDI\OneDrive\Desktop\LUNARIS'
$apiUrl  = 'https://api.github.com/repos/subhadeepnandi43-sys/LUNARIS---AI_URBAN_INTELLIGENCE/git/trees/main?recursive=1'
$baseRaw = 'https://raw.githubusercontent.com/subhadeepnandi43-sys/LUNARIS---AI_URBAN_INTELLIGENCE/main'

Write-Host '[SYNC] Fetching file list from GitHub (subhadeepnandi43-sys)...' -ForegroundColor Cyan
$tree = (Invoke-RestMethod -Uri $apiUrl -Headers @{'User-Agent'='PowerShell'} -UseBasicParsing).tree | Where-Object { $_.type -eq 'blob' }
Write-Host ("[SYNC] " + $tree.Count + " files found in repo") -ForegroundColor Cyan

$u = 0; $a = 0; $s = 0; $e = 0
$webClient = New-Object System.Net.WebClient

foreach ($item in $tree) {
    $p = $item.path
    if ($p -eq 'serve.ps1' -or $p -match '^assets/' -or $p -match 'real_pothole_dataset/' -or $p -match 'demo_output/' -or $p -match '\.pt$' -or $p -match '\.zip$') {
        $s++
        continue
    }
    $dest = Join-Path $repo ($p -replace '/','\')
    $dd = Split-Path $dest -Parent
    if (-not (Test-Path $dd)) { New-Item -ItemType Directory -Path $dd -Force | Out-Null }
    $rawUrl = "$baseRaw/$p"
    try {
        if (Test-Path $dest) {
            $localSize = (Get-Item $dest).Length
            if ($localSize -eq $item.size) {
                $s++
                continue
            }
            $tmp = "$dest.tmp"
            $webClient.DownloadFile($rawUrl, $tmp)
            $h1 = (Get-FileHash $tmp -Algorithm MD5).Hash
            $h2 = (Get-FileHash $dest -Algorithm MD5).Hash
            if ($h1 -ne $h2) {
                Move-Item $tmp $dest -Force
                Write-Host "  UPDATED: $p" -ForegroundColor Green
                $u++
            } else {
                Remove-Item $tmp -Force
                $s++
            }
        } else {
            $webClient.DownloadFile($rawUrl, $dest)
            Write-Host "  NEW: $p" -ForegroundColor Cyan
            $a++
        }
    } catch {
        Write-Host "  ERROR: $p" -ForegroundColor Red
        $e++
    }
}
Write-Host "[SYNC DONE] Updated: $u | New: $a | Skipped: $s | Errors: $e" -ForegroundColor Green