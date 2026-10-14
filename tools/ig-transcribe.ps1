param(
  [Parameter(Mandatory=$true)][string]$Url,
  [int]$MaxMb = 18
)
# Extract the SPOKEN SCRIPT (guion) of an Instagram reel, exactly like the IREAL
# Scrapbook does: scrape the reel to get a fresh videoUrl, download the .mp4, and
# let Gemini 2.5 Flash WATCH it and return a structured JSON (transcript + hook + CTA).
# Pure PowerShell + Invoke-RestMethod. No node, no SDK. Reads keys from the profile .env.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$envFile = Join-Path $PSScriptRoot '..\.env'
function GetEnv($n){
  $line = (Get-Content $envFile -ErrorAction SilentlyContinue | Where-Object { $_ -match "^\s*$n\s*=" } | Select-Object -First 1)
  if ($line) { return (($line -split '=',2)[1]).Trim().Trim('"').Trim("'") }
  return $null
}
$apify = GetEnv 'APIFY_API_TOKEN'
$gem = GetEnv 'GEMINI_API_KEY'; if (-not $gem) { $gem = GetEnv 'GOOGLE_API_KEY' }
if (-not $apify) { Write-Output 'ERROR: APIFY_API_TOKEN missing in profile .env'; exit 1 }
if (-not $gem)   { Write-Output 'ERROR: GEMINI_API_KEY missing in profile .env'; exit 1 }

# 1) Scrape the reel to get a FRESH videoUrl (Instagram CDN links expire fast).
$reelUrl = ($Url -split '\?')[0]
$scrapeBody = @{ username = @($reelUrl); resultsLimit = 1 } | ConvertTo-Json
try {
  $r = Invoke-RestMethod -Method Post -Uri "https://api.apify.com/v2/acts/apify~instagram-reel-scraper/run-sync-get-dataset-items?token=$apify" -ContentType 'application/json' -Body $scrapeBody -TimeoutSec 180
} catch { Write-Output ("ERROR: scrape failed: " + $_.Exception.Message); exit 1 }
$item = @($r) | Where-Object { -not $_.error } | Select-Object -First 1
if (-not $item) { Write-Output 'ERROR: reel restricted/unavailable or no data returned'; exit 1 }

$videoUrl = $item.videoUrl
if (-not $videoUrl) { Write-Output 'ERROR: no videoUrl in result (not a video/reel?)'; exit 1 }
$owner   = [string]$item.ownerUsername
$capClean = if ($item.caption) { ($item.caption -replace '\s+',' ') } else { '' }
$dur     = [string]$item.videoDuration
$likes   = [string]$item.likesCount
$comments = [string]$item.commentsCount
$views   = if ($item.videoPlayCount) { [string]$item.videoPlayCount } else { [string]$item.videoViewCount }

# 2) Download the .mp4 (cap size to stay within Gemini inline-data limit).
$tmp = Join-Path $env:TEMP ("ig_" + [System.Guid]::NewGuid().ToString('N') + ".mp4")
try {
  Invoke-WebRequest -Uri $videoUrl -OutFile $tmp -Headers @{ 'User-Agent' = 'Mozilla/5.0' } -UseBasicParsing -TimeoutSec 90
} catch { Write-Output ("ERROR: video download failed: " + $_.Exception.Message); exit 1 }
$sizeMb = (Get-Item $tmp).Length / 1MB
if ($sizeMb -gt $MaxMb) { Remove-Item $tmp -Force; Write-Output ("ERROR: video too large ({0:N1}MB > {1}MB); raise -MaxMb or use a shorter reel" -f $sizeMb, $MaxMb); exit 1 }
$b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($tmp))
Remove-Item $tmp -Force

# 3) Ask Gemini to WATCH the video and return the structured guion (same shape the Scrapbook uses).
$prompt = @'
You are an expert video content analyst and transcriber. You have been given the actual video file of an Instagram Reel. WATCH IT CAREFULLY and transcribe EVERY WORD spoken (the audio track). Also read any on-screen text overlays.

Context:
- Creator: @__OWNER__
- Caption: __CAPTION__
- Duration: __DUR__ seconds
- Likes: __LIKES__ | Comments: __COMMENTS__ | Views: __VIEWS__

Return ONLY a JSON object with this EXACT structure:
{
  "full_transcript": "Word-for-word transcript of everything spoken. Put on-screen text overlays in [brackets].",
  "hook": { "text": "Exact opening words (first 3-5 seconds).", "duration_seconds": 3, "type": "Question | Bold Claim | Pattern Interrupt | Shocking Stat | Story Opening | Direct Address | Controversial Take", "strength": 8 },
  "body": { "text": "Everything after the hook and before the CTA.", "key_points": ["point 1", "point 2", "point 3"] },
  "cta": { "text": "The call-to-action, or null if none.", "type": "Follow | Comment | Link | Save | Share | None" },
  "language": "detected language code (e.g. es, en)",
  "confidence": 0.9
}

Rules:
- hook.text MUST be the exact first words the viewer hears.
- full_transcript must include EVERYTHING said, not a summary.
- If no CTA exists, set cta to null.
- Detect the language automatically.
'@
$prompt = $prompt.Replace('__OWNER__',$owner).Replace('__CAPTION__',$capClean).Replace('__DUR__',$dur).Replace('__LIKES__',$likes).Replace('__COMMENTS__',$comments).Replace('__VIEWS__',$views)

# Base64 is [A-Za-z0-9+/=] only, so it needs no JSON escaping and can be inlined
# directly (avoids ConvertTo-Json choking on a multi-MB string). Only the prompt
# text is JSON-encoded (it already includes the surrounding quotes).
$promptJson = ($prompt | ConvertTo-Json)
$reqBody = '{"contents":[{"parts":[{"inline_data":{"mime_type":"video/mp4","data":"' + $b64 + '"}},{"text":' + $promptJson + '}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0.2}}'

$uri = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$gem"
try {
  $resp = Invoke-RestMethod -Method Post -Uri $uri -ContentType 'application/json; charset=utf-8' -Body $reqBody -TimeoutSec 240
} catch { Write-Output ("ERROR: Gemini call failed: " + $_.Exception.Message); exit 1 }

$txt = $null
try { $txt = $resp.candidates[0].content.parts[0].text } catch {}
if (-not $txt) { Write-Output 'ERROR: Gemini returned no text (blocked or empty)'; exit 1 }

Write-Output ("GUION @{0} | ~{1}s | {2} likes / {3} comments / {4} views" -f $owner, $dur, $likes, $comments, $views)
Write-Output '---'
Write-Output $txt
