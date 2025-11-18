# GitOps with Argo CD
This repository defines the **GitOps structure** for deploying all services using **Argo CD**.
- `argo-cd/` → contains the Argo CD root application manifest. 
- `apps/` → stores Kubernetes manifests for each microservice (central, hotel, etc.).  
- `environments/` → groups applications per environment (dev, prod).

## Install ArgoCD
### Install ArgoCD
``` bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```
### Make a port forward
`kubectl port-forward svc/argocd-server -n argocd 8080:443`

### Create a password
``` bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```
``` powershell
(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}') |
  ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

### Deploy Root App
`kubectl apply -f argo-cd/root-app.yaml -n argocd`

if the root-app set before argocd-cm, you may need restart the argocd-server pod
`kubectl rollout restart -n argocd deployment argocd-repo-server` 

### Namespaces for apps
kubectl create namespace central
kubectl create namespace hotel

## Dev
kubectl apply -k environments/prod

## For kubernetes dashboard
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

## Kafka
helm repo add confluentinc https://packages.confluent.io/helm
helm repo update
helm upgrade --install confluent-operator confluentinc/confluent-for-kubernetes --namespace central
kubectl apply -f .\applications\central\kafka\ -n central

kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.46.0/strimzi-crds-0.46.0.yaml 

## Starting Frontend

### Dev environment
Uses direct port forwarding.

```bash
kubectl port-forward svc/frontend-service 8081:80 -n central
```

Grafana:

```bash
k port-forward svc/grafana 3001:3000 -n central
```

Access in browser 

Frontend 
```bash
http://localhost:8081
```

Grafana
```bash
http://localhost:3001/
```


### Test environment
Uses an ingress with frontend.test.localhost. \
```bash
kubectl apply -k environments/test/kustomization.yaml
```

Access in broswer: 

```bash
http://localhost
```

### Production environment

Uses ingress with host set to prod.127.0.0.1.nip.io

```bash
k apply -k environments/prod/kustomization.yaml
```

Access in browser: 
```bash
https://frontend.prod.127.0.0.1.nip.io/
```

Grafana:
```bash
https://frontend.prod.127.0.0.1.nip.io/grafana

```

