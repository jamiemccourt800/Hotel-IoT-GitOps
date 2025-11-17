# Storage Overlays

This directory contains Kustomize overlays for managing Persistent Volume Claims (PVCs) across different environments.

## Structure

```
storage/
├── base/                          # Base PVC definitions (no storage class)
│   ├── pvc-grafana.yaml
│   ├── pvc-mongodb.yaml
│   ├── pvc-victoria-metrics.yaml
│   ├── pvc-mosquitto.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/                       # Development overlay
│   │   └── kustomization.yaml     # Uses 'standard' storage class
│   └── prod/                      # Production overlay
│       └── kustomization.yaml     # Uses 'azure-disk-premium-ssd-retain'
```

## Usage

### Development Environment (dev)
Uses the `standard` storage class for local Kubernetes clusters:
```bash
kubectl apply -k storage/overlays/dev
```

### Production Environment (prod)
Uses Azure-specific storage class `azure-disk-premium-ssd-retain`:
```bash
kubectl apply -k storage/overlays/prod
```

## Environment Integration

The storage overlays are automatically included in environment-specific deployments:

- **Dev**: `environments/dev/kustomization.yaml` → includes `storage/overlays/dev`
- **Prod**: `environments/prod/kustomization.yaml` → includes `storage/overlays/prod`

## PVCs Managed

1. **grafana-data** (128Mi) - Grafana dashboard data
2. **mongodb-data** (1Gi) - MongoDB database storage
3. **victoria-metrics-data** (512Mi) - VictoriaMetrics time-series data
4. **mosquitto-data** (120Mi) - Mosquitto MQTT broker data

## Storage Classes

### dev (Local Development)
- **Storage Class**: `standard`
- **Use Case**: Local development, testing, Minikube, Kind, etc.

### prod (Production)
- **Storage Class**: `azure-disk-premium-ssd-retain`
- **Use Case**: AKS (Azure Kubernetes Service) production deployments
- **Features**: Premium SSD with retain reclaim policy for data persistence

## Customization

To add a new PVC:
1. Create the base PVC in `storage/base/`
2. Add it to `storage/base/kustomization.yaml`
3. The overlays will automatically apply the appropriate storage class

To change storage classes:
- Edit the patch in the respective overlay's `kustomization.yaml`
