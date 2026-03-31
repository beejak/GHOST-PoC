Param(
  [string]$Namespace = "ghost-lab",
  [string]$Selector = "app=app-service",
  [string]$RunId = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param([string]$Name)
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed (exit code $LASTEXITCODE)"
  }
}

if ([string]::IsNullOrWhiteSpace($RunId)) {
  $RunId = Get-Date -Format "yyyyMMdd-HHmmss"
}

$runDir = "data/external/runs/$RunId"

python tools/collect_k8s_lab_data.py --namespace $Namespace --selector $Selector --run-id $RunId
Invoke-Checked "collect_k8s_lab_data.py"
python tools/normalize_external_capture.py `
  --events "$runDir/events.json" `
  --logs "$runDir/logs.txt" `
  --out-records "$runDir/normalized.json" `
  --out-gt "$runDir/ground_truth.json"
Invoke-Checked "normalize_external_capture.py"

python tools/run_external_replay.py `
  --data "$runDir/normalized.json" `
  --ground-truth "$runDir/ground_truth.json" `
  --record
Invoke-Checked "run_external_replay.py"

Write-Host "Pipeline complete: $runDir"
