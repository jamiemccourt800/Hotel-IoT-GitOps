# Storage Overlay Migration Guide

## What Changed

The PVC (Persistent Volume Claim) definitions have been reorganized to use Kustomize overlays, allowing for environment-specific storage configurations.

### Old Structure
```
applications/
  central/
    pvc-grafana.yaml          # Hard-coded storageClassName
    pvc-mongodb.yaml
    pvc-victoria-metrics.yaml
  hotel/
    pvc-mosquitto.yaml
```

### New Structure
```
storage/
  base/                        # Base PVC definitions (no storageClassName)
    pvc-grafana.yaml
    pvc-mongodb.yaml
    pvc-victoria-metrics.yaml
    pvc-mosquitto.yaml
  overlays/
    dev/                       # Development
      kustomization.yaml       # Adds storageClassName: standard
    prod/                      # Production
      kustomization.yaml       # Adds storageClassName: azure-disk-premium-ssd-retain
```

## Benefits

1. **Environment-Specific Storage**: Different storage classes for dev (azurite/local) and prod (Azure)
2. **DRY Principle**: Single source of truth for PVC definitions in `storage/base/`
3. **Easy Customization**: Change storage class in one place per environment
4. **GitOps Ready**: Clear separation between environments

## Deployment

### Development Environment
```bash
# Deploy to local cluster with standard storage
kubectl kustomize --enable-helm environments/dev | kubectl apply -f -
```

### Production Environment
```bash
# Deploy to AKS with Azure premium SSD
kubectl kustomize --enable-helm environments/prod | kubectl apply -f -
```

## Storage Classes

| Environment | Storage Class | Description |
|------------|---------------|-------------|
| Dev (dev) | `standard` | Local Kubernetes clusters (Minikube, Kind, etc.) |
| Prod (prod) | `azure-disk-premium-ssd-retain` | Azure Premium SSD with retain policy |

## Verification

To verify the overlays work correctly:

```bash

# Test dev overlay
kubectl kustomize storage/overlays/dev

# Test prod overlay
kubectl kustomize storage/overlays/prod

# Test dev environment
kubectl kustomize --enable-helm environments/dev | grep storageClassName

# Test prod environment
kubectl kustomize --enable-helm environments/prod | grep storageClassName
```

## Next Steps

1. **Delete old PVC files** (optional, if no longer needed):
   ```bash
   rm applications/central/pvc-*.yaml
   rm applications/hotel/pvc-*.yaml
   ```

2. **Update ArgoCD applications** to use environment-specific paths:
   - Dev: `environments/dev`
   - Prod: `environments/prod`

3. **Customize Azure storage class** if needed in `storage/overlays/azure/kustomization.yaml`

## Rollback

If you need to rollback, the old PVC files are still in:
- `applications/central/pvc-*.yaml`
- `applications/hotel/pvc-mosquitto.yaml`

Simply remove the storage resources from environment kustomizations to use the old files.
