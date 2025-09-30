param(
    [string]$HostName = "localhost"
)

Write-Host "Scanning ports 3000-3005 on $HostName..."
$ports = 3000..3005
$reachable = @()
foreach ($port in $ports) {
    $result = Test-NetConnection -ComputerName $HostName -Port $port -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        $reachable += $port
    }
}

if (-not $reachable) {
    Write-Warning "No active ports discovered in range."
    exit 1
}

foreach ($port in $reachable) {
    $uri = "http://$HostName:$port/api/health/connectors"
    Write-Host "Testing $uri"
    try {
        $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
            Write-Host "Port $port health check passed" -ForegroundColor Green
        } else {
            Write-Error "Health check failed on port $port with status $($response.StatusCode)"
            exit 1
        }
    }
    catch {
        Write-Error "Failed to contact $uri. $_"
        exit 1
    }
}

Write-Host "Connector smoke tests completed successfully."
