Param(
  [string]$Namespace = "ghost-lab",
  [string]$Selector = "app=app-service",
  [string]$RunId = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RunId)) {
  $RunId = Get-Date -Format "yyyyMMdd-HHmmss"
}

$runDir = "data/external/runs/$RunId"

python tools/collect_k8s_lab_data.py --namespace $Namespace --selector $Selector --run-id $RunId
python tools/normalize_external_capture.py `
  --events "$runDir/events.json" `
  --logs "$runDir/logs.txt" `
  --out-records "$runDir/normalized.json" `
  --out-gt "$runDir/ground_truth.json"

python tools/run_external_replay.py `
  --data "$runDir/normalized.json" `
  --ground-truth "$runDir/ground_truth.json" `
  --record

Write-Host "Pipeline complete: $runDir"
