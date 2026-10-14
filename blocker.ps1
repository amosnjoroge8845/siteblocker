$hostsFile = "$env:SystemRoot\System32\drivers\etc\hosts"

$markerStart = "# SITEBLOCKER START"
$markerEnd = "# SITEBLOCKER END"

$blockedSites = @(
    "example.com",
    "www.example.com"
)

$hosts = Get-Content $hostsFile

$newHosts = New-Object System.Collections.Generic.List[string]

$insideBlock = $false

foreach ($line in $hosts) {

    if ($line -eq $markerStart) {
        $insideBlock = $true
        continue
    }

    if ($line -eq $markerEnd) {
        $insideBlock = $false
        continue
    }

    if (-not $insideBlock) {
        $newHosts.Add($line)
    }
}

$newHosts.Add("")
$newHosts.Add($markerStart)

foreach ($site in $blockedSites) {
    $newHosts.Add("0.0.0.0 $site")
}

$newHosts.Add($markerEnd)

Set-Content `
    -Path $hostsFile `
    -Value $newHosts `
    -Encoding ASCII

ipconfig /flushdns

Write-Host ""
Write-Host "SiteBlocker updated successfully!"
Write-Host "Blocked: example.com"