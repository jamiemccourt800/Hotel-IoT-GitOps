# GitOps with Argo CD
This repository defines the **GitOps structure** for deploying all services using **Argo CD**.
- `argo-cd/` → contains the Argo CD root application manifest. 
- `apps/` → stores Kubernetes manifests for each microservice (central, hotel, etc.).  
- `environments/` → groups applications per environment (dev, prod) managed via App-of-Apps.

## Install ArgoCD
### Install ArgoCD
``` bash
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```
### Make a port forward
`kubectl port-forward svc/argocd-server -n argocd 8080:443`

### Create a password
`kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

### Deploy Root App
`kubectl apply -f argo-cd/root-app.yaml -n argocd`
