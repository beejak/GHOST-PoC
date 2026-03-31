Param(
  [string]$Namespace = "ghost-lab"
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param([string]$Name)
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed (exit code $LASTEXITCODE)"
  }
}

# Failure 1: ImagePullBackOff
kubectl -n $Namespace set image deploy/app-service app=ghcr.io/ghost/does-not-exist:badtag
Invoke-Checked "inject ImagePullBackOff image"
Start-Sleep -Seconds 15

# Recovery for next failures
kubectl -n $Namespace set image deploy/app-service app=nginx:1.27-alpine
Invoke-Checked "recover image"
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s
Invoke-Checked "rollout after image recovery"

# Failure 2: CrashLoopBackOff (exit immediately)
$crashPatchPath = Join-Path $env:TEMP "ghost-crash-patch.json"
Set-Content -Path $crashPatchPath -Encoding utf8 -Value @'
[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["/bin/sh","-c","exit 1"]}]
'@
kubectl -n $Namespace patch deploy app-service --type='json' --patch-file $crashPatchPath
Invoke-Checked "inject crash loop command"
Start-Sleep -Seconds 20

# Recover command
$recoverPatchPath = Join-Path $env:TEMP "ghost-recover-patch.json"
Set-Content -Path $recoverPatchPath -Encoding utf8 -Value @'
[{"op":"remove","path":"/spec/template/spec/containers/0/command"}]
'@
kubectl -n $Namespace patch deploy app-service --type='json' --patch-file $recoverPatchPath
Invoke-Checked "recover crash loop command"
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s
Invoke-Checked "rollout after crash recovery"

# Failure 3: Startup/readiness unhealthy
kubectl -n $Namespace patch deploy app-service --type='json' `
  -p='[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/readinessProbe/httpGet/path\",\"value\":\"/does-not-exist\"}]'
Invoke-Checked "inject readiness failure"
Start-Sleep -Seconds 20

# Recover readiness
kubectl -n $Namespace patch deploy app-service --type='json' `
  -p='[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/readinessProbe/httpGet/path\",\"value\":\"/\"}]'
Invoke-Checked "recover readiness path"
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s
Invoke-Checked "rollout after readiness recovery"

Write-Host "Failure injection sequence complete"
