# Build and push hotel operator image

param(
    [string]$Version = "latest"
)

$ImageName = "dkitdevops/hotel-operator"
$FullImage = "${ImageName}:${Version}"

Write-Host "Building hotel operator image: $FullImage" -ForegroundColor Green

# Build the image
docker build -t $FullImage .

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nImage built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To push to registry:" -ForegroundColor Yellow
    Write-Host "  docker push $FullImage"
    Write-Host ""
    Write-Host "To deploy to Kubernetes:" -ForegroundColor Yellow
    Write-Host "  kubectl apply -f deployment.yaml"
    Write-Host ""
    Write-Host "To test locally:" -ForegroundColor Yellow
    Write-Host "  docker run --rm $FullImage"
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
    exit 1
}
