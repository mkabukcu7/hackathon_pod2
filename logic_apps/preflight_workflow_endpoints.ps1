param(
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$WorkflowSharedKey,
    [string]$CustomerId = "C0000481",
    [int]$TimeoutSec = 25
)

$ErrorActionPreference = "Stop"

$baseUrl = $ApiBaseUrl.TrimEnd('/')
$headers = @{ "x-workflow-key" = $WorkflowSharedKey }

function Invoke-Step {
    param(
        [string]$Name,
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -Headers $headers -UseBasicParsing -TimeoutSec $TimeoutSec
        $statusCode = [int]$response.StatusCode
        $body = $null
        try { $body = $response.Content | ConvertFrom-Json } catch {}

        Write-Host ("PASS  {0,-22} {1}" -f $Name, $statusCode)
        return [PSCustomObject]@{ Name = $Name; Passed = $true; StatusCode = $statusCode; Body = $body; Raw = $response.Content }
    }
    catch {
        $statusCode = "ERR"
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        Write-Host ("FAIL  {0,-22} {1}" -f $Name, $statusCode)
        return [PSCustomObject]@{ Name = $Name; Passed = $false; StatusCode = $statusCode; Body = $null; Raw = $null }
    }
}

Write-Host ("[preflight] Base URL: " + $baseUrl)

$health = Invoke-Step -Name "platform-health" -Url ("$baseUrl/api/workflows/platform-health")
$packet = Invoke-Step -Name "customer-packet" -Url ("$baseUrl/api/workflows/customer-packet/$CustomerId")

if ($health.Passed -and $health.Body -and $health.Body.status) {
    Write-Host ("INFO  platform status       " + $health.Body.status)
}
if ($packet.Passed -and $packet.Body -and $packet.Body.status) {
    Write-Host ("INFO  packet status         " + $packet.Body.status)
}
if ($packet.Passed -and $packet.Body -and $packet.Body.request_id) {
    Write-Host ("INFO  packet request_id     " + $packet.Body.request_id)
}
if ($packet.Passed -and $packet.Body -and $packet.Body.meta -and $packet.Body.meta.components_returned) {
    $components = ($packet.Body.meta.components_returned -join ', ')
    Write-Host ("INFO  packet components     " + $components)
}

if ($health.Passed -and $packet.Passed) {
    Write-Host "[preflight] Completed: PASS"
    exit 0
}

Write-Host "[preflight] Completed: FAIL"
exit 1
