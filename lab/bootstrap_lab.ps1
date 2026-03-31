Param(
  [string]$ClusterName = "ghost-lab",
  [string]$Namespace = "ghost-lab"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "docker not found"
}
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
  throw "kubectl not found"
}
if (-not (Get-Command kind -ErrorAction SilentlyContinue)) {
  throw "kind not found. Install kind first: https://kind.sigs.k8s.io/"
}

$existing = (kind get clusters) -contains $ClusterName
if (-not $existing) {
  kind create cluster --name $ClusterName
}

kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f "lab/manifests/namespace.yaml"
kubectl apply -f "lab/manifests/app-service.yaml"
kubectl -n $Namespace rollout status deploy/app-service --timeout=120s
Write-Host "Lab bootstrap complete"
