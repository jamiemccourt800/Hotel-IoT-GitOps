# Hotel Manager - ArgoCD Testing Deployment

## Overview

The Hotel Manager application is now configured for deployment to the testing environment via ArgoCD.

## Files Created

### Testing Overlay
- **`overlays/testing/kustomization.yaml`** - Kustomize overlay for testing environment
- **`overlays/testing/README.md`** - Testing overlay documentation

### ArgoCD Application
- **`argo-cd/hotel-manager-testing-app.yaml`** - ArgoCD Application manifest

## What's Configured

### Testing Overlay Patches
1. **Secret Key**: Testing-specific secret (not for production)
2. **Image Pull Policy**: Always (pulls latest image)
3. **Ingress Host**: `hotel-manager.testing.local`
4. **Labels**: `environment: testing`, `app.kubernetes.io/part-of: hotel-platform`
5. **Annotations**: `deployed-by: argocd`, `environment: testing`

### ArgoCD Application Settings
- **Sync Wave**: 15 (deploys after infrastructure)
- **Auto-Sync**: Enabled with prune and self-heal
- **Namespace**: default
- **Retry**: Configured with exponential backoff

## Deployment Steps

### 1. Ensure Prerequisites

```bash
# Verify ArgoCD is installed
kubectl get pods -n argocd

# Verify Hotel CRDs are installed
kubectl get crd hotels.platform.devops.io
kubectl get crd rooms.platform.devops.io

# Verify hotel-operator is running
kubectl get deployment hotel-operator
```

### 2. Build and Push Image

```bash
cd applications/hotel-manager

# Build image
docker build -t dkitdevops/hotel-manager:latest .

# Push to registry
docker push dkitdevops/hotel-manager:latest
```

### 3. Update Repository URL

Edit `argo-cd/hotel-manager-testing-app.yaml`:
```yaml
spec:
  source:
    repoURL: https://github.com/YOUR-USERNAME/devops-project-gitops.git
```

### 4. Deploy ArgoCD Application

```bash
# Apply the ArgoCD application
kubectl apply -f argo-cd/hotel-manager-testing-app.yaml

# Check application status
kubectl get app hotel-manager-testing -n argocd

# Watch the sync
kubectl get app hotel-manager-testing -n argocd -w
```

### 5. Verify Deployment

```bash
# Check deployment
kubectl get deployment hotel-manager

# Check pods
kubectl get pods -l app=hotel-manager

# Check service
kubectl get svc hotel-manager

# Check ingress
kubectl get ingress hotel-manager

# View logs
kubectl logs -l app=hotel-manager -f
```

### 6. Access the Application

#### Option A: Port Forward
```bash
kubectl port-forward svc/hotel-manager 8080:80
```
Visit: http://localhost:8080

#### Option B: Ingress
Add to your hosts file:
```
# Windows: C:\Windows\System32\drivers\etc\hosts
# Linux/Mac: /etc/hosts
127.0.0.1 hotel-manager.testing.local
```

Visit: http://hotel-manager.testing.local

## ArgoCD UI

### View in ArgoCD Dashboard

1. Port forward to ArgoCD:
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```

2. Login:
   ```bash
   # Get password
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

3. Visit: https://localhost:8080

4. Find the `hotel-manager-testing` application

### Expected Status
- **Sync Status**: Synced
- **Health Status**: Healthy
- **Resources**: Deployment, Service, Ingress, ServiceAccount, ClusterRole, ClusterRoleBinding

## Testing the Application

### 1. Access Dashboard
Navigate to the home page to see the dashboard.

### 2. Create a Test Hotel
1. Click "Create Hotel"
2. Fill in:
   - Hotel ID: `hotel-test1`
   - Location: `Testing Lab`
   - Replicas: `1`
3. Submit

### 3. Verify Hotel Creation
```bash
# Check Hotel CRD
kubectl get hotel hotel-test1-instance

# Check namespace was created
kubectl get ns hotel-test1

# Check ConfigMap in argocd namespace
kubectl get cm -n argocd -l platform.devops.io/hotel-id=hotel-test1
```

### 4. Add a Room
1. Click on the hotel
2. Click "Add Room"
3. Configure:
   - Room ID: `room001`
   - Enable all sensors
4. Submit

### 5. Verify Room Creation
```bash
# Check Room CRD
kubectl get room -n hotel-test1

# Check room simulators (once deployed)
kubectl get pods -n hotel-test1
```

## Updating the Application

### Method 1: GitOps (Recommended)
1. Make changes to code or manifests
2. Commit and push to Git
3. ArgoCD will auto-sync within ~3 minutes
4. Or manually sync in ArgoCD UI

### Method 2: Manual Rebuild
```bash
# Rebuild image
docker build -t dkitdevops/hotel-manager:latest .
docker push dkitdevops/hotel-manager:latest

# Restart deployment (triggers pull)
kubectl rollout restart deployment/hotel-manager

# Watch rollout
kubectl rollout status deployment/hotel-manager
```

## Troubleshooting

### Application Not Syncing

```bash
# Check application status
kubectl describe app hotel-manager-testing -n argocd

# View sync status
argocd app get hotel-manager-testing

# Manual sync
argocd app sync hotel-manager-testing

# Or via kubectl
kubectl patch app hotel-manager-testing -n argocd \
  --type merge -p '{"operation":{"sync":{}}}'
```

### Deployment Issues

```bash
# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check pod status
kubectl describe pod -l app=hotel-manager

# Check logs
kubectl logs -l app=hotel-manager --tail=100

# Check RBAC
kubectl auth can-i list hotels --as=system:serviceaccount:default:hotel-manager
```

### Ingress Not Working

```bash
# Check ingress
kubectl describe ingress hotel-manager

# Check ingress controller
kubectl get pods -n ingress-nginx

# Check service endpoints
kubectl get endpoints hotel-manager
```

## Clean Up

### Remove Hotel Manager

```bash
# Delete ArgoCD application (will prune all resources)
kubectl delete app hotel-manager-testing -n argocd

# Or delete directly
kubectl delete -k overlays/testing/
```

### Remove Test Hotels

```bash
# Delete all test hotels
kubectl delete hotels --all -A

# Operator will clean up resources
```

## Configuration Reference

### Environment Variables (Testing)
| Variable | Value | Source |
|----------|-------|--------|
| `SECRET_KEY` | `testing-secret-key-do-not-use-in-prod` | Overlay patch |
| `PORT` | `5000` | Base deployment |

### Labels (Testing)
| Label | Value |
|-------|-------|
| `app` | `hotel-manager` |
| `environment` | `testing` |
| `app.kubernetes.io/name` | `hotel-manager` |
| `app.kubernetes.io/component` | `web-ui` |
| `app.kubernetes.io/part-of` | `hotel-platform` |

### Resource Limits
| Resource | Request | Limit |
|----------|---------|-------|
| Memory | 128Mi | 256Mi |
| CPU | 100m | 500m |

## Next Steps

1. **Add Production Overlay**: Create `overlays/production/` with production settings
2. **Add Staging Overlay**: Create `overlays/staging/` for staging environment
3. **Add Monitoring**: Integrate with Prometheus/Grafana
4. **Add Alerts**: Configure alerting rules
5. **Add Authentication**: Implement OAuth/OIDC

## Documentation

- **Testing Overlay**: [overlays/testing/README.md](../applications/hotel-manager/overlays/testing/README.md)
- **Hotel Manager Features**: [applications/hotel-manager/FEATURES.md](../applications/hotel-manager/FEATURES.md)
- **Quick Start**: [applications/hotel-manager/QUICKSTART.md](../applications/hotel-manager/QUICKSTART.md)
- **Platform Docs**: [applications/hotel/README.md](../applications/hotel/README.md)
