# Hotel Manager - Testing Overlay

This overlay configures the Hotel Manager for the testing environment.

## Changes from Base

### Configuration
- **Secret Key**: Uses testing-specific secret key (not for production!)
- **Image Pull Policy**: Always pull latest image for testing
- **Ingress Host**: `hotel-manager.testing.local`

### Labels & Annotations
- **Environment**: `testing`
- **Part Of**: `hotel-platform`
- **Deployed By**: `argocd`

## Deployment

### Using ArgoCD

```bash
# Deploy the ArgoCD application
kubectl apply -f ../../argo-cd/hotel-manager-testing-app.yaml

# Check status
kubectl get app hotel-manager-testing -n argocd

# View in ArgoCD UI
# The app will auto-sync when changes are pushed to Git
```

### Using kubectl + kustomize

```bash
# Apply directly
kubectl apply -k .

# Preview changes
kubectl kustomize . | less

# Delete
kubectl delete -k .
```

## Accessing the Application

### Port Forward
```bash
kubectl port-forward svc/hotel-manager 8080:80
```
Visit: http://localhost:8080

### Ingress
Add to `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts`):
```
127.0.0.1 hotel-manager.testing.local
```

Visit: http://hotel-manager.testing.local

## Testing Checklist

- [ ] Deployment creates successfully
- [ ] Pods are running and healthy
- [ ] Service is accessible
- [ ] Ingress routing works
- [ ] Can list hotels via UI
- [ ] Can create new hotel
- [ ] Can add rooms to hotel
- [ ] Can delete rooms
- [ ] Can delete hotels
- [ ] RBAC permissions work correctly
- [ ] Health endpoint responds: `/health`
- [ ] API endpoint works: `/api/hotels`

## Customization

To customize for your testing environment, edit `kustomization.yaml`:

```yaml
# Example: Change replica count
patches:
  - target:
      kind: Deployment
      name: hotel-manager
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 2
```

## Environment Variables

Testing overlay sets:
- `SECRET_KEY`: Testing secret (change for production!)
- `PORT`: 5000 (inherited from base)

To add more:
```yaml
patches:
  - target:
      kind: Deployment
      name: hotel-manager
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: DEBUG
          value: "true"
```

## Troubleshooting

### Application not syncing
```bash
# Check ArgoCD app status
kubectl describe app hotel-manager-testing -n argocd

# Manual sync
argocd app sync hotel-manager-testing
```

### Pods not starting
```bash
# Check pod status
kubectl get pods -l app=hotel-manager

# View logs
kubectl logs -l app=hotel-manager -f

# Describe pod
kubectl describe pod -l app=hotel-manager
```

### Ingress not working
```bash
# Check ingress
kubectl get ingress hotel-manager

# Verify ingress controller
kubectl get pods -n ingress-nginx

# Check service
kubectl get svc hotel-manager
```

## Notes

⚠️ **Security**: This overlay uses a testing secret key. Do not use in production!

⚠️ **Image**: Always pulls latest image. Ensure your image is pushed before deploying.

⚠️ **Namespace**: Deploys to `default` namespace. Adjust if needed.
