# Build hotel-manager Docker image

param(
    [string]$Version = "latest"
)

$ImageName = "dkitdevops/hotel-manager"
$FullImage = "${ImageName}:${Version}"

Write-Host "Building hotel manager image: $FullImage" -ForegroundColor Green

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
    Write-Host "  docker run -p 5000:5000 $FullImage"
    Write-Host ""
    Write-Host "To access locally:" -ForegroundColor Yellow
    Write-Host "  http://localhost:5000"
} else {
    Write-Host "`nBuild failed!" -ForegroundColor Red
    exit 1
}
