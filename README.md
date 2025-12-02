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

kubectl apply -n argocd -f argo-cd/argocd-cm.yaml

### Deploy ArgoCD Apps
First needs to install the CRDs using the declarative approach
`kubectl apply -f argo-cd/crd-app.yaml -n argocd`

Then deploy the root app
`kubectl apply -f argo-cd/root-app.yaml -n argocd`

Then deploy the infra apps like Prometheus, Grafana, etc.
`kubectl apply -f argo-cd/infra-app.yaml -n argocd`

if the root-app set before argocd-cm, you may need restart the argocd-server pod
`kubectl rollout restart -n argocd deployment argocd-repo-server` 

### Namespaces for apps
kubectl create namespace central
kubectl create namespace hotel

## Dev
kubectl apply -k environments/prod

## Monitoring
Add the prometheus endpoint to grafana. 

http://kube-prometheus-stack-prometheus.monitoring.svc:9090

## For kubernetes dashboard
helm upgrade --install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --create-namespace --namespace kubernetes-dashboard

kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-kong-proxy 8443:443

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

## Minikube Ingress
 minikube addons enable ingress
 minikube tunnel

## Kafka
kubectl apply -f https://github.com/strimzi/strimzi-kafka-operator/releases/download/0.44.0/strimzi-crds-0.44.0.yaml

## Starting Frontend

### Dev environment
Uses direct port forwarding.

```bash
kubectl port-forward svc/frontend-svc 81:80 -n central
```

Grafana:

```bash
k port-forward svc/grafana 3001:3000 -n central
```

Access in browser 

Frontend 
```bash
http://localhost:81
```

Grafana
```bash
http://localhost:3001/
```


### Test environment
Uses an ingress with frontend.test.localhost
```bash
kubectl apply -k environments/test/kustomization.yaml
```

Access in broswer: 

```bash
http://frontend.test.localhost
```

### Production environment

Uses ingress with host set to frontend.prod.localhost

```bash
k apply -k environments/prod/kustomization.yaml
```

Access in browser: 
```bash
http://frontend.test.localhost/
```

Grafana:
```bash
https://frontend.prod.localhost/grafana
```

