Param(
  [string]$Namespace = "ghost-lab"
)

$ErrorActionPreference = "Stop"

# Failure 1: ImagePullBackOff
kubectl -n $Namespace set image deploy/app-service app=ghcr.io/ghost/does-not-exist:badtag
Start-Sleep -Seconds 15

# Recovery for next failures
kubectl -n $Namespace set image deploy/app-service app=nginx:1.27-alpine
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s

# Failure 2: CrashLoopBackOff (exit immediately)
kubectl -n $Namespace patch deploy app-service --type='json' `
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/command","value":["/bin/sh","-c","exit 1"]}]'
Start-Sleep -Seconds 20

# Recover command
kubectl -n $Namespace patch deploy app-service --type='json' `
  -p='[{"op":"remove","path":"/spec/template/spec/containers/0/command"}]'
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s

# Failure 3: Startup/readiness unhealthy
kubectl -n $Namespace patch deploy app-service --type='json' `
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/does-not-exist"}]'
Start-Sleep -Seconds 20

# Recover readiness
kubectl -n $Namespace patch deploy app-service --type='json' `
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/"}]'
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s

Write-Host "Failure injection sequence complete"
