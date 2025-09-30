param(
    [string]$Path = "http://localhost:3000/api/health",
    [string]$HostName = "localhost"
)

Write-Host "Weather Vessel Health Check"
Write-Host "=========================="
Write-Host "Target: $Path"
Write-Host "Host: $HostName"
Write-Host ""

# Function to test a specific endpoint
function Test-Endpoint {
    param([string]$Url)
    
    try {
        Write-Host "Testing $Url..."
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
            Write-Host "✅ $Url - Status: $($response.StatusCode)" -ForegroundColor Green
            
            # Try to parse JSON response
            try {
                $json = $response.Content | ConvertFrom-Json
                Write-Host "   Response: $($json | ConvertTo-Json -Compress)" -ForegroundColor Gray
            } catch {
                Write-Host "   Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "❌ $Url - Status: $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $Url - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test the specified endpoint
$success = Test-Endpoint -Url $Path

if ($success) {
    Write-Host ""
    Write-Host "🎉 Health check passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "💥 Health check failed!" -ForegroundColor Red
    exit 1
}
