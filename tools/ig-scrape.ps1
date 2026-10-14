param(
  [Parameter(Mandatory=$true)][string]$User,
  [int]$Limit = 8
)
# Reads APIFY_API_TOKEN from the profile .env (robust: no shell/env dependency).
$envFile = Join-Path $PSScriptRoot '..\.env'
function GetEnv($n){
  $line = (Get-Content $envFile -ErrorAction SilentlyContinue | Where-Object { $_ -match "^\s*$n\s*=" } | Select-Object -First 1)
  if ($line) { return (($line -split '=',2)[1]).Trim().Trim('"').Trim("'") }
  return $null
}
$tok = GetEnv 'APIFY_API_TOKEN'
if (-not $tok) { Write-Output 'ERROR: APIFY_API_TOKEN missing in profile .env'; exit 1 }
# Accept @handle, bare handle, or a pasted reel/post URL. Strip any ?igsh=... tracking
# query so the reel scraper (which accepts usernames OR direct reel URLs) doesn't choke.
$handle = (($User -split '\?')[0]).Trim().TrimStart('@')
# Use the SAME dedicated Actor the IREAL Scrapbook uses (instagram-reel-scraper),
# which the app confirms works on the FREE plan. Input field is `username` (array),
# NOT `directUrls` on the generic instagram-scraper (that path returns empty on FREE).
$body = @{ username = @($handle); resultsLimit = $Limit } | ConvertTo-Json
try {
  $r = Invoke-RestMethod -Method Post -Uri "https://api.apify.com/v2/acts/apify~instagram-reel-scraper/run-sync-get-dataset-items?token=$tok" -ContentType 'application/json' -Body $body -TimeoutSec 180
  $items = @($r)
  # Filter out Apify error items (restricted/unavailable pages), same as the Scrapbook.
  $valid = @($items | Where-Object { -not $_.error -and $_.shortCode })
  $errs  = @($items | Where-Object { $_.error })
  Write-Output ("POSTS: {0}" -f $valid.Count)
  foreach($p in $valid){
    $cap = if ($p.caption) { ($p.caption -replace '\s+',' ') } else { '' }
    $type = if ($p.type) { $p.type } else { 'reel' }
    $views = if ($p.videoPlayCount) { $p.videoPlayCount } else { $p.videoViewCount }
    $obj = [ordered]@{ type=$type; likes=$p.likesCount; comments=$p.commentsCount; views=$views; date=$p.timestamp; url=$p.url; caption=$cap }
    Write-Output (($obj | ConvertTo-Json -Compress))
  }
  if ($errs.Count -gt 0) { Write-Output ("NOTE: {0} item(s) returned an Apify error (restricted/unavailable)." -f $errs.Count) }
} catch {
  Write-Output ("ERROR: " + $_.Exception.Message)
  exit 1
}
