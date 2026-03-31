Param(
  [string]$ClusterName = "ghost-lab",
  [string]$Namespace = "ghost-lab"
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param([string]$Name)
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed (exit code $LASTEXITCODE)"
  }
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "docker not found"
}
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
  throw "kubectl not found"
}
$kindCmd = Get-Command kind -ErrorAction SilentlyContinue
if (-not $kindCmd) {
  $localKind = Join-Path (Resolve-Path ".").Path ".tools\kind.exe"
  if (Test-Path $localKind) {
    $kindCmd = $localKind
  } else {
    throw "kind not found. Install kind first: https://kind.sigs.k8s.io/ (or place .tools\\kind.exe)"
  }
} else {
  $kindCmd = "kind"
}

$existing = (& $kindCmd get clusters) -contains $ClusterName
Invoke-Checked "kind get clusters"
if (-not $existing) {
  & $kindCmd create cluster --name $ClusterName
  Invoke-Checked "kind create cluster"
}

kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -
Invoke-Checked "kubectl create/apply namespace"
kubectl apply -f "lab/manifests/namespace.yaml"
Invoke-Checked "kubectl apply namespace manifest"
kubectl apply -f "lab/manifests/app-service.yaml"
Invoke-Checked "kubectl apply app-service manifest"
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s
Invoke-Checked "kubectl rollout status app-service"
Write-Host "Lab bootstrap complete"
