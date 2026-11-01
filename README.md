<div align="center">

# Campus Lost & Found

**A simple board where students report lost and found items, and get them back to their owners.**

[![CI/CD](https://github.com/Divii2205/campus-lost-and-found/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Divii2205/campus-lost-and-found/actions/workflows/ci-cd.yml)
![Tests](https://img.shields.io/badge/tests-11%20passing-brightgreen)
![Trivy](https://img.shields.io/badge/Trivy-0%20HIGH%2FCRITICAL-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-18-blue)
![Kubernetes](https://img.shields.io/badge/deploy-Kubernetes%20%2B%20Helm-326ce5)
![Terraform](https://img.shields.io/badge/infra-Terraform%20on%20AWS-7b42bc)

[Quick start](#quick-start) · [How it works](#how-it-works) · [API](#api-reference) · [CI/CD](#cicd-pipeline) · [Kubernetes](#deploying-to-kubernetes-with-helm) · [ArgoCD](#gitops-with-argocd) · [Monitoring](#monitoring) · [Runbook](#troubleshooting-runbook)

</div>

![Campus Lost & Found running in the browser](screenshots/01-app-browser-localhost-3000.png)

---

## What it does

Campus Lost & Found is a website for a college campus.

- A student who **loses** something (a calculator, an ID card, keys) writes what it is and where they last had it.
- A student who **finds** something writes that down too.
- Anyone can search the board.
- When an item gets back to its owner, it is marked **returned** (claimed).

The project also shows the full path that takes code from a laptop to a real, watched server setup:

```text
Code -> Git -> GitHub Actions (pytest -> build -> Trivy -> GHCR) -> Terraform (AWS VPC + EKS)
     -> Kubernetes + Helm (Ingress, HPA, probes) -> ArgoCD (GitOps) -> Prometheus + Grafana -> Troubleshooting
```

Every screenshot on this page is real output from this project.

## Features

| Who | What they can do |
|---|---|
| Student who lost something | Search the board. If the item is not there, post a **Lost** report with the place and a way to contact them. |
| Student who found something | Post a **Found** report so the owner knows where the item is. |
| Anyone | Show only Lost, only Found or only Back with owner. Search by words ("library", "keys"). Edit or remove a report. |
| Owner gets the item back | Click **Mark returned**, type the owner's name, and the item gets a **Claimed** stamp. |

Each report looks like a paper lost property tag with an ink stamp: red **Lost**, green **Found**, blue **Claimed**. The page works on phones and laptops.

Behind the page:

- A clean REST API with 7 item endpoints and live API docs.
- Health and readiness checks, so Kubernetes knows when the app is alive and when it can serve visitors.
- 11 automatic tests that run before anything is shipped.
- Small, non-root container images with zero HIGH or CRITICAL security holes.
- One pipeline that tests, builds, scans and publishes every change.
- Cloud servers written as code, built and torn down with one command.
- Auto scaling and live charts.

## How it works

Read this picture from top to bottom.

```text
 Developer (Divijaa)
   │ git commit / git push
   ▼
 GitHub repo: Divii2205/campus-lost-and-found
   │
   ▼
 GitHub Actions  (.github/workflows/ci-cd.yml)
   ├─ test             pytest -v (11 tests) + npm ci && npm run build
   ├─ build-scan-push  docker build (tag = commit SHA) -> Trivy gate (HIGH/CRITICAL = fail) -> push to GHCR
   └─ deploy           helm upgrade --install (runs when a KUBE_CONFIG secret is set)
                │
                ▼
          GHCR: ghcr.io/divii2205/lostfound-backend:<sha>, lostfound-frontend:<sha>

 Terraform (terraform/) ──► AWS ap-south-1: VPC + 2 public subnets + IGW + EKS + managed node group

 Kubernetes (namespace "lostfound", installed with helm/lostfound)
   Ingress lostfound.local ──┬── "/"    -> Service lostfound-frontend -> 2x nginx pods (React build)
                             └── "/api" -> Service backend            -> 2 to 5 FastAPI pods (HPA)
                                                                        │
                                                       Service lostfound-postgres -> PostgreSQL + PVC
   Prometheus ── ServiceMonitor ──► backend /metrics          Grafana ── dashboard "Campus Lost & Found API"
```

In plain words:

1. Divijaa writes code and sends it to GitHub.
2. GitHub Actions tests the code, builds the app boxes, checks them for security problems and stores them.
3. Terraform builds the servers on AWS.
4. Kubernetes runs the app boxes. Helm tells Kubernetes what to run.
5. Prometheus and Grafana watch the app and draw charts.

## Tech stack

Every tool, with one plain line about what it does.

| Layer | Tool | What it means in plain words |
|---|---|---|
| Frontend | React 18 + Vite, plain CSS (responsive), served by unprivileged nginx | The page you see in the browser. React builds the page, Vite packs it, CSS makes it look nice on phones and laptops, and nginx is a small web server that hands the page to the browser. |
| Backend | FastAPI, SQLAlchemy 2, Pydantic, Uvicorn | The part that answers requests. FastAPI is the Python web framework, SQLAlchemy talks to the database, Pydantic checks that incoming data is correct, and Uvicorn runs the server. |
| Database | PostgreSQL 16, Alembic migrations | PostgreSQL stores all the reports. Alembic creates and updates the database tables from code. |
| Tests | pytest + FastAPI TestClient, throwaway SQLite database | pytest runs automatic checks on the code. SQLite is a tiny database used only during tests and then thrown away. |
| Containers | Docker (non-root images), Docker Compose | Docker packs the app into a box so it runs the same on every computer. Docker Compose starts several boxes together with one command. |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) | GitHub Actions is a robot that tests and builds the code every time it is pushed. GHCR is a shelf on GitHub where the built boxes are stored. |
| Security | Trivy (image scan gate), gitleaks (secret scan) | Trivy looks inside each box for known security holes. gitleaks looks for passwords or keys saved by mistake. |
| Infrastructure | Terraform + AWS (VPC, subnets, IGW, EKS, node group, IAM) | AWS is Amazon's cloud where you rent computers. Terraform writes down the servers you want in a file and then builds them for you. |
| Kubernetes | kind (local), Helm 3 chart, ingress-nginx, metrics-server, HPA | Kubernetes runs many boxes and restarts them if they break. kind is a small Kubernetes on your own laptop. Helm is like an installer for apps on Kubernetes. ingress-nginx is the front door that sends visitors to the right part. metrics-server measures CPU use. The HPA adds more copies of the app when it gets busy. |
| GitOps | Argo CD | Argo CD watches this Git repo and makes the cluster match it. A new release is just a change to a file in Git. |
| Monitoring | kube-prometheus-stack (Prometheus Operator, Prometheus, Grafana) | Prometheus collects numbers about the app every few seconds. Grafana turns those numbers into live charts. |

## Quick start

"Locally" means on your own computer.

### Option 1: Docker Compose (fastest)

One command starts the web page, the server and the database:

```bash
docker compose up --build
```

Then open these addresses in your browser:

| URL | What you see |
|---|---|
| http://localhost:3000 | the app |
| http://localhost:8000/docs | Swagger API docs (a page that lists every API call and lets you try it) |
| http://localhost:8000/health | liveness (`{"status":"UP"}`), which means "the server is alive" |
| http://localhost:8000/ready | readiness, which means "the server can reach the database" |
| http://localhost:8000/metrics | Prometheus metrics (numbers about the app) |

To stop everything, run `docker compose down`. Add `-v` to delete the saved database too.

### Option 2: Backend without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://lostfound:lostfound@localhost:5432/lostfound'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

To run the web page in development mode: `cd frontend && npm ci && npm run dev`. It sends `/api` requests to port 8000.

### Database and migrations

The `items` table holds all the reports. It is created by the Alembic migration [`backend/alembic/versions/0001_create_items.py`](backend/alembic/versions/0001_create_items.py). A migration is a small script that sets up or changes the database tables.

The backend box runs `alembic upgrade head` before it starts Uvicorn. The `alembic_version` table shows which migration was applied:

![PostgreSQL items table and Alembic version](screenshots/01-postgres-alembic.png)

## Project structure

```text
campus-lost-and-found/
├── backend/
│   ├── app/                  main.py, routes.py, models.py, schemas.py, db.py, config.py
│   ├── alembic/versions/     0001_create_items.py
│   ├── tests/                conftest.py (test DB), test_items.py (11 tests)
│   ├── pytest.ini  requirements.txt  Dockerfile  .env.example
├── frontend/
│   ├── src/                  App.jsx, api.js, main.jsx, styles.css
│   ├── index.html  nginx.conf  package.json  package-lock.json  Dockerfile (multi-stage)
├── docker-compose.yml        frontend + backend + postgres
├── .github/workflows/ci-cd.yml
├── terraform/                versions.tf, variables.tf, main.tf (VPC), eks.tf, outputs.tf, terraform.tfvars.example
├── k8s/                      namespace.yaml, kind-config.yaml, troubleshooting/
├── helm/lostfound/           Chart.yaml, values.yaml, values-dev.yaml, values-gitops.yaml, templates/
├── argocd/                   application.yaml (the Argo CD app)
├── monitoring/               prometheus-values.yaml, grafana-values.yaml, grafana-dashboard.yaml
├── scripts/                  deploy-local.sh, gitops-release.sh, load-test.sh
├── demo/                     presentation.pptx, slides.pdf, demo-video.mp4
└── screenshots/
```

| Folder | What is inside |
|---|---|
| [`backend/`](backend) | The Python server, the database setup and the tests |
| [`frontend/`](frontend) | The web page code |
| [`.github/workflows/`](.github/workflows) | The robot steps for GitHub Actions |
| [`terraform/`](terraform) | The files that build the AWS servers |
| [`k8s/`](k8s) | Basic Kubernetes files and the broken files used for practice |
| [`helm/lostfound/`](helm/lostfound) | The Helm package that installs the whole app on Kubernetes |
| [`argocd/`](argocd) | The Argo CD app that deploys the Helm package from Git |
| [`monitoring/`](monitoring) | Settings for Prometheus and Grafana |
| [`scripts/`](scripts) | Small helper scripts |
| [`demo/`](demo) | The slides and the demo video |
| [`screenshots/`](screenshots) | The pictures used on this page |

### Version control

Git saves every version of the code. GitHub keeps a copy of it online.

- Repository: **https://github.com/Divii2205/campus-lost-and-found** (public).
- More than 25 commits, all by **Divii2205**. Each message says what changed. For example: "Add Alembic migration that creates the items table" and "Remove pip and setuptools from backend runtime image to fix HIGH CVEs found by Trivy".
- `.gitignore` tells Git to skip `.env`, `__pycache__/`, `node_modules/`, `.venv/`, `dist/`, Terraform state and `terraform.tfvars`.
- `.gitattributes` keeps LF line endings, so shell scripts and YAML files work the same on Windows and Linux.

![Commit history](screenshots/03-git-log.png)

## API reference

An API is a list of addresses that the web page calls to read or change data. Each row below is one of them.

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | the process is alive |
| GET | `/ready` | the database answers |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/items` | list items; filters `?status=LOST`, `?category=KEYS`, `?q=library` |
| GET | `/api/items/{id}` | one item |
| POST | `/api/items` | report a lost or found item |
| PUT | `/api/items/{id}` | edit a report |
| PATCH | `/api/items/{id}/claim` | mark it returned to its owner (only once, else 409) |
| DELETE | `/api/items/{id}` | remove a report |
| GET | `/api/items/stats` | totals: lost, found, claimed |

That is 7 item endpoints. They use GET (read), POST (create), PUT (replace), PATCH (change one part) and DELETE (remove).

![Swagger docs](screenshots/01-swagger-docs.png)

Here every endpoint is called with curl (a command line tool that sends web requests): create, read, update, claim, delete, filter and stats.

![API CRUD with curl](screenshots/01-api-crud.png)

## Testing

Tests are small programs that check the code works. Run them like this:

```bash
cd backend
pytest -v
```

- There are **11 tests**. They cover `/health`, `/ready`, `/metrics` and every item endpoint: create, input checking (422), list + filter + search, get + 404, update, claim (and the 409 error on a second claim), delete and stats.
- [`tests/conftest.py`](backend/tests/conftest.py) swaps the real database for a **fresh SQLite file for each test** (using FastAPI `dependency_overrides`). So the tests never touch the real PostgreSQL database.
- [`pytest.ini`](backend/pytest.ini) sets the Python path, the test folder and which warnings to hide.

![pytest -v: 11 passed](screenshots/02-pytest-passing.png)

The tests run before any box is built. If a test fails, the pipeline stops, and no broken box reaches the registry.

## Containers

Docker packs the app into a box (called an image) so it runs the same on every computer. A Dockerfile is the recipe for that box.

| File | What it does |
|---|---|
| [`backend/Dockerfile`](backend/Dockerfile) | `python:3.12-slim` -> OS security updates -> install requirements -> **remove pip/setuptools** (see [Security](#security)) -> copy Alembic + app -> runs as **uid 10001 (appuser)** -> `alembic upgrade head && uvicorn` |
| [`frontend/Dockerfile`](frontend/Dockerfile) | **multi-stage**: stage 1 `node:22-alpine` runs `npm ci && npm run build`; stage 2 `nginxinc/nginx-unprivileged` serves `dist/` as **uid 101** on port 8080. Node and the build tools never reach the final image. |
| [`docker-compose.yml`](docker-compose.yml) | postgres (with healthcheck and volume) -> backend (waits for postgres to be healthy) -> frontend on **localhost:3000** |

Two simple words:

- **Non-root** means the app does not run as the all-powerful admin user. This is safer.
- **Multi-stage** means the first stage builds the page, and only the finished result is copied into a small second box.

`docker compose up --build` starts all three services. Running `id` inside the boxes shows both run as non-root:

![docker compose up --build](screenshots/04-docker-compose-up.png)

The browser at http://localhost:3000 is the screenshot at the [top of this page](#campus-lost--found).

## CI/CD pipeline

CI/CD means a robot tests, builds and ships the code every time you push. Here the robot is GitHub Actions.

File: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). It runs on **every push to `main`** (and on pull requests to `main`).

| Job | Steps | The build fails when |
|---|---|---|
| `test` | checkout -> Python 3.12 -> `pip install` -> **`pytest -v`** -> Node 22 -> **`npm ci && npm run build`** | any test fails or the frontend does not compile |
| `build-scan-push` (needs `test`) | build **both** images -> **Trivy** scan both -> log in to GHCR -> **push** | Trivy finds a fixable HIGH/CRITICAL CVE |
| `deploy` (needs `build-scan-push`, `main` only) | `helm upgrade --install` with the new SHA -> `kubectl rollout status` | the rollout does not become healthy |

**Image tags are the Git commit SHA**, never `latest`. A SHA is the unique id Git gives each commit.

```text
ghcr.io/divii2205/lostfound-backend:<github.sha>
ghcr.io/divii2205/lostfound-frontend:<github.sha>
```

Why this helps:

- Every running box can be traced back to the exact commit it was built from.
- The owner name is made lowercase (`Divii2205` -> `divii2205`) because GHCR only accepts lowercase names.
- The Helm chart refuses to work without a tag (`required "backend.tag must be set to a Git commit SHA"`).

The `deploy` job runs only when the repo has a `KUBE_CONFIG` secret. This is a base64 kubeconfig, which is the login file for a cluster (for example the EKS cluster). Without it, the job prints a skip message, and the images still land in GHCR. For the local kind cluster, `scripts/deploy-local.sh` runs the same Helm command.

**Why the GitHub deploy step skips today:** GitHub runs the pipeline on its own computers on the internet. They cannot reach a kind cluster on a laptop, and the EKS cluster is deleted after use to save money. So the pipeline stops after publishing the images. To deploy a commit, run `./scripts/deploy-local.sh` on the laptop. It rolls out the same commit SHA with the same `helm upgrade --install` command. To let GitHub deploy by itself, keep a cluster running and save its kubeconfig as the `KUBE_CONFIG` repository secret.

The workflow passes `actionlint` (a checker for GitHub Actions files). These are its key lines:

![actionlint + key workflow lines](screenshots/05-ci-workflow-lint.png)

### A real run

The first push to `main` started the pipeline by itself, and every job passed.

**Actions run (green):** https://github.com/Divii2205/campus-lost-and-found/actions/runs/38920194477

All 3 jobs passed: `test`, then `build-scan-push`, then `deploy` (deploy skipped the cluster step because no cluster secret is set):

![GitHub Actions run, all green](screenshots/05-github-actions-green.png)

The images are in GHCR. The tag is the commit SHA `29b1201ad5f4f1ab1c03823bd2f5071f05adf74b`, not `latest`:

![GHCR backend package with the commit SHA tag](screenshots/05-ghcr-packages.png)

![GHCR frontend package with the same commit SHA tag](screenshots/05-ghcr-packages-frontend.png)

## Security

### Image scanning with Trivy

Trivy looks inside each box for known security holes (called CVEs). Both images are scanned in `build-scan-push` with:

```text
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 <image>
```

`--exit-code 1` makes the step (and the whole pipeline) **fail** when a fixable HIGH or CRITICAL hole is found. So a risky image is never pushed. Trivy runs from the official `aquasec/trivy:0.65.0` container, fixed to one version.

### A real finding and its fix

The first backend image **failed** the check with 4 HIGH problems:

![Trivy: backend image before the fix](screenshots/06-trivy-backend-before-fix.png)

> **What Trivy scanned and what the result means.**
> Trivy looked at the Debian OS packages and all 37 Python packages inside the backend image. It found 4 HIGH CVEs.
> One example is **CVE-2025-47273**. It is a path traversal bug in **setuptools 70.3.0**. A specially made package address can write files outside the folder it should stay in. It is fixed in 78.1.1.
> The other three were two urllib3 CVEs and one msgpack CVE.
> None of these were the app's own libraries. They came from **pip and setuptools** (and the libraries pip carries with it), which were left in the image after the install step.
> The app never needs them while it runs, so the Dockerfile now removes them after `pip install`.
> The new scan is clean: 0 HIGH/CRITICAL in both images, and the check passes.

![Trivy: both images clean after the fix](screenshots/06-trivy-images-clean.png)

The same Trivy check inside the real GitHub Actions run. The backend image `29b1201...` has 0 HIGH or CRITICAL problems, so the step passed and the images were pushed:

![Trivy scan inside the GitHub Actions pipeline](screenshots/05-trivy-in-pipeline.png)

### No secrets in Git

gitleaks checked the whole history, and no secret files are saved in Git. AWS keys live only in `~/.aws/credentials` (made by `aws configure`). The database password in Kubernetes is a Secret set by Helm.

![gitleaks: no leaks found](screenshots/06-secret-scan-gitleaks.png)

### Layers of safety

Trivy is one layer. The others are:

| Layer | What it does |
|---|---|
| SAST (for example Bandit) | reads the code itself to find unsafe patterns |
| Dependency scanning (`npm audit` and Trivy fs) | checks the libraries the code uses |
| Secret scanning (gitleaks) | finds passwords or keys saved by mistake |
| Runtime security | non-root containers and `allowPrivilegeEscalation: false`, so a box cannot give itself more power |

## Infrastructure (AWS with Terraform)

Terraform writes down the servers you want in files, then builds them on AWS for you. AWS is Amazon's cloud where you rent computers.

Folder: [`terraform/`](terraform). Region **ap-south-1 (Mumbai)**. Kubernetes version **1.36** on EKS (the AWS default, so there are no extended support charges).

| File | Creates |
|---|---|
| `main.tf` | VPC `10.30.0.0/16`, internet gateway, **2 public subnets** in 2 availability zones (tagged for EKS load balancers), public route table + associations |
| `eks.tf` | IAM role for the control plane, **EKS cluster `lostfound-eks`** (standard support only, so no extended support charges), IAM role for nodes, **managed node group** (1x t3.small, scales 1 to 2) |
| `variables.tf` / [`terraform.tfvars.example`](terraform/terraform.tfvars.example) | region, CIDRs, instance type, node count. **No credentials anywhere**: Terraform reads them from `aws configure`. |
| `outputs.tf` | VPC id, subnet ids, cluster endpoint, and the `aws eks update-kubeconfig` command |

Simple words for the table:

- **VPC**: your own private network inside AWS.
- **Subnet**: a smaller part of that network. "Public" means it can reach the internet.
- **Internet gateway (IGW)**: the door between the network and the internet.
- **EKS**: Kubernetes run by AWS.
- **Node group**: the actual computers that run the app boxes.
- **IAM role**: a set of permissions that says what a service is allowed to do.

**Cost choice:** there is no NAT gateway, because a NAT gateway costs money every hour. Instead, the worker computer sits in a public subnet. So the cluster costs about $0.15 per hour, and it is destroyed right after use.

```bash
cd terraform
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name lostfound-eks
terraform destroy
```

| Command | What it does |
|---|---|
| `terraform init` | downloads what Terraform needs |
| `terraform validate` | checks the files are written correctly |
| `terraform plan` | shows what will be built, without building it |
| `terraform apply` | builds it |
| `terraform destroy` | deletes everything so it stops costing money |

![terraform init + validate](screenshots/07-terraform-init-validate.png)

`terraform plan`: 15 resources to add, 0 errors:

![terraform plan](screenshots/07-terraform-plan.png)

### Built for real on AWS

`terraform apply` built all 15 resources in about 12 minutes:

![terraform apply](screenshots/07-terraform-apply.png)

<details>
<summary><b>More proof: AWS CLI and AWS Console views</b></summary>

<br>

The AWS command line shows the VPC, the 2 public subnets (in 2 different zones, ap-south-1a and ap-south-1b), the EKS cluster (Active) and the 1 worker computer (Ready):

![AWS CLI: VPC, subnets, EKS, node](screenshots/07-aws-cli-vpc-eks.png)

The AWS Console (the AWS website) in the Mumbai region. The VPC map shows the network, the 2 public subnets, the route table and the internet gateway:

![AWS Console: VPC resource map](screenshots/07-aws-console-vpc.png)

The EKS cluster with its node group `lostfound-eks-nodes`, Active:

![AWS Console: EKS node group](screenshots/07-aws-console-eks.png)

</details>

### Torn down, nothing left

The cluster was up for about 30 minutes. Then `terraform destroy` deleted all 15 resources. A check of AWS found 0 clusters, 0 VPCs, 0 computers, 0 disks, 0 NAT gateways and 0 load balancers left. Nothing keeps costing money.

![terraform destroy and AWS check](screenshots/07-terraform-destroy.png)

## Deploying to Kubernetes with Helm

Kubernetes runs the app boxes and restarts them if they break. Helm is like an installer: one command sets up every part of the app.

Local cluster: **kind** ([`k8s/kind-config.yaml`](k8s/kind-config.yaml), cluster `session21`), with **ingress-nginx** (the front door) and **metrics-server** (measures CPU). The same chart also deploys to EKS.

One time setup of the local cluster and its two helpers:

```bash
kind create cluster --config k8s/kind-config.yaml
# front door (ingress-nginx made for kind)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
# CPU meter for the HPA (kind needs the insecure TLS flag)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

Deploy the app:

```bash
kubectl apply -f k8s/namespace.yaml                   # namespace "lostfound"
./scripts/deploy-local.sh                             # build SHA-tagged images, kind load, helm upgrade --install
# which runs:
helm upgrade --install lostfound ./helm/lostfound -n lostfound \
  -f helm/lostfound/values-dev.yaml --set backend.tag=<sha> --set frontend.tag=<sha> --wait
```

What the chart ([`helm/lostfound/`](helm/lostfound)) creates:

| Template | Resource |
|---|---|
| `backend.yaml` | Deployment `lostfound-backend` (2 replicas, run by the HPA), **wait-for-db initContainer**, startup/readiness/liveness probes, non-root, resource requests; ClusterIP Service `backend:8000` |
| `frontend.yaml` | Deployment `lostfound-frontend` (2 replicas), probes, non-root; ClusterIP Service `lostfound-frontend:80` |
| `postgres.yaml` | PostgreSQL Deployment + **PVC** (1Gi) + ClusterIP Service |
| `config.yaml` | ConfigMap (app name, environment) + **Secret** (DB user, password, `DATABASE_URL`) |
| `ingress.yaml` | Ingress `lostfound.local`: **`/` -> frontend, `/api` -> backend** |
| `hpa.yaml` | HPA: backend 2 to 5 pods at 60% CPU |
| `servicemonitor.yaml` | tells Prometheus to read `backend /metrics` every 15s |

Kubernetes words in plain language:

| Word | Meaning |
|---|---|
| Pod | one running copy of an app box |
| Deployment | keeps the right number of pods running |
| Replica | one copy; 2 replicas means 2 copies |
| Service (ClusterIP) | a fixed inside address that reaches the pods |
| Ingress | the front door that sends `/` and `/api` to the right place |
| initContainer | a small helper that runs first, before the main app starts |
| Probe | a regular health check Kubernetes does on a pod |
| ConfigMap | normal settings |
| Secret | private settings, like passwords |
| PVC | saved disk space, so the database keeps its data after a restart |
| HPA | adds more pods when CPU gets busy, and removes them later |

All pods are **Running**, with 2 copies each for backend and frontend, and 0 restarts:

![kubectl get pods](screenshots/08-kubectl-get-pods.png)

The app opened through the Ingress address **http://lostfound.local** (add `127.0.0.1 lostfound.local` to your hosts file first):

![App through the Ingress](screenshots/08-app-via-ingress-lostfound-local.png)

<details>
<summary><b>More proof: Services, Helm release, Ingress, config and probes</b></summary>

<br>

ClusterIP Services and the pods behind them (endpoints):

![kubectl get svc](screenshots/08-kubectl-get-svc.png)

The Helm release:

![helm list](screenshots/08-helm-list.png)

Ingress routing (`/api` -> backend pods, `/` -> frontend pods):

![Ingress routing](screenshots/08-ingress-routing.png)

ConfigMap, Secret, PVC and the three probes:

![ConfigMap, Secret, PVC, probes](screenshots/08-configmap-secret-pvc-probes.png)

</details>

### Auto scaling

While `scripts/load-test.sh` sent lots of traffic, the backend CPU went above 60% of its request. The HPA then grew it from 2 to 3 pods ("New size: 3; reason: cpu resource utilization above target"):

```bash
./scripts/load-test.sh 4000 40
kubectl get hpa -n lostfound -w
```

![HPA scaling](screenshots/08-hpa-scaling.png)

## GitOps with ArgoCD

GitOps means Git holds the wanted state of the cluster. Argo CD is a tool inside the cluster that reads Git and makes the cluster match it. Nobody runs `helm upgrade` by hand. A release is just a commit.

| File | What it does |
|---|---|
| [`argocd/application.yaml`](argocd/application.yaml) | The Argo CD app `lostfound`. It reads `helm/lostfound` from the `main` branch of this repo and installs it in the `lostfound` namespace. Auto sync, prune and self heal are on. |
| [`helm/lostfound/values-gitops.yaml`](helm/lostfound/values-gitops.yaml) | Only the two image tags. Changing them in Git is how a new version goes out. |
| [`scripts/gitops-release.sh`](scripts/gitops-release.sh) | Builds both images with the current commit SHA, loads them into kind and writes the SHA into `values-gitops.yaml`. |

Install Argo CD and add the app (once):

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait -n argocd --for=condition=Available deployment --all --timeout=300s
kubectl apply -f argocd/application.yaml
# the Argo CD page at https://localhost:8080, user admin, password from
kubectl port-forward -n argocd svc/argocd-server 8080:443
kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

Install the monitoring stack first. The chart has a ServiceMonitor, and Argo CD can only create it after Prometheus Operator is installed.

The release flow:

```text
edit code -> git push -> GitHub Actions green (tests, Trivy, GHCR)
          -> ./scripts/gitops-release.sh -> git commit + push values-gitops.yaml
          -> Argo CD sees the new SHA -> Synced + Healthy -> new pods running
```

Argo CD after a release: the app `lostfound` is Synced to the new commit and Healthy, with every resource in the tree:

![Argo CD app synced and healthy](screenshots/12-argocd-synced.png)

The history shows each deploy as a Git revision, started by the automated sync policy:

![Argo CD sync history](screenshots/12-argocd-history.png)

**Why the images are built on the laptop:** GitHub Actions builds images for amd64 computers. The laptop is an Apple Silicon Mac, so kind runs arm64 and cannot run those images. `gitops-release.sh` builds the same commit for arm64 and loads it into kind, the same way `deploy-local.sh` does. On EKS (amd64) Argo CD would pull the GHCR images directly.

## Monitoring

Monitoring means watching the app while it runs. Prometheus collects numbers about the app every few seconds. Grafana turns those numbers into live charts.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml -f monitoring/grafana-values.yaml
kubectl apply -f monitoring/grafana-dashboard.yaml
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
# Grafana login: admin / password from
kubectl get secret -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.data.admin-password}' | base64 -d
```

| File | What it does |
|---|---|
| [`prometheus-values.yaml`](monitoring/prometheus-values.yaml) | lets Prometheus find ServiceMonitors in every namespace, and turns off parts a small cluster does not need |
| [`grafana-values.yaml`](monitoring/grafana-values.yaml) | turns on the dashboard helper (sidecar). No admin password is saved in Git: the chart makes one and keeps it in a Secret. |
| [`grafana-dashboard.yaml`](monitoring/grafana-dashboard.yaml) | a ConfigMap that holds the dashboard. Grafana loads it by itself. |

`/metrics` gives numbers in the Prometheus text format: how many requests came in for each route, method and status, plus how long they took (latency histograms):

![curl /metrics](screenshots/09-metrics-endpoint.png)

Prometheus **Targets**: every backend pod found by the ServiceMonitor is **UP** (3/3 while the HPA had grown the backend):

![Prometheus targets UP](screenshots/09-prometheus-targets-up.png)

The Grafana dashboard **Campus Lost & Found API** with live data during the load test. It shows requests per second for each route, p95 latency (95 out of 100 requests were faster than this), error rate (the load test asks for a missing item on purpose, which gives 404s), backend pods up, and CPU for each pod:

![Grafana dashboard](screenshots/09-grafana-dashboard.png)

## Troubleshooting runbook

These are real problems found while building the project. Each one lists what went wrong, why, the fix and the proof.

### 1. Backend kept crashing on the first Helm install

- **What we saw:** backend pods were `Running` but had **4 restarts** right after `helm install`.
- **Logs:** `psycopg.OperationalError: connection failed ... port 5432 failed: Connection refused`
- **Why:** both pods start at the same time. The backend runs `alembic upgrade head` before PostgreSQL is ready to accept connections. The migration fails, the box stops, and Kubernetes restarts it again and again until the database is up.

![Backend restarts before the fix](screenshots/11-troubleshoot-backend-restarts-before.png)

- **Fix:** a `wait-for-db` **initContainer** in `templates/backend.yaml`. It runs `pg_isready` over and over until the database answers. (The first try printed `no attempt`. This was because uid 10001 has no user entry in the postgres image, so `pg_isready` needs `-U lostfound`.)
- **Proof:** a clean reinstall plus a planned database restart. The init log shows "waiting for db ... accepting connections", and every pod has 0 restarts.

![Backend after the fix](screenshots/11-troubleshoot-backend-restarts-after.png)

### 2. Trivy check failed on the backend image

See [Security](#a-real-finding-and-its-fix). pip and setuptools were left in the image and carried 4 HIGH CVEs. The fix was to remove them after the install step.

### 3. Practice lab: ImagePullBackOff

File: [`k8s/troubleshooting/broken-image.yaml`](k8s/troubleshooting/broken-image.yaml)

ImagePullBackOff means Kubernetes cannot download the image.

```bash
kubectl apply -f k8s/troubleshooting/broken-image.yaml
kubectl get pods -n lostfound
kubectl describe pod <pod-name> -n lostfound
kubectl get events -n lostfound --sort-by=.lastTimestamp
```

`kubectl describe pod` shows the tag `does-not-exist` cannot be pulled. The fix is `kubectl set image` with a real commit SHA tag.

![ImagePullBackOff and fix](screenshots/11-troubleshoot-imagepullbackoff.png)

### 4. Practice lab: Service with no endpoints

File: [`k8s/troubleshooting/broken-service.yaml`](k8s/troubleshooting/broken-service.yaml)

```bash
kubectl apply -f k8s/troubleshooting/broken-service.yaml
kubectl get svc -n lostfound
kubectl get endpoints -n lostfound
kubectl get pods -n lostfound --show-labels
```

The Service looks for pods with `app=lostfound-api`, but the pods are labelled `app=lostfound-backend`. So the Service finds no pods (no endpoints) and no traffic gets through. Fixing the selector fills in the endpoints.

![Service no endpoints and fix](screenshots/11-troubleshoot-service-no-endpoints.png)

### 5. Smaller problems

| Problem | Why | Fix |
|---|---|---|
| `vite build` failed on the Windows laptop: `@rollup/rollup-win32-x64-msvc ... blocked by Application Control policy` | Windows blocks the native Rollup program | build inside `node:22-alpine` (same as the Dockerfile and CI) |
| Grafana panels were empty on first load | panels relied on the "default" data source | each panel now names the data source `uid: prometheus` |
| GHCR rejects `ghcr.io/Divii2205/...` | GHCR needs lowercase names | workflow uses `${GITHUB_REPOSITORY_OWNER,,}` |

### What we learned

- **Ready is not the same as alive.** `/health` only says the program is running. `/ready` also checks the database, so Kubernetes sends visitors only to pods that can really help them.
- **Start order matters.** In Compose, `depends_on: service_healthy` handles it. Kubernetes has no start order, so an initContainer does the waiting.
- **Most security holes come from things you did not mean to ship.** The app's own libraries were clean. The HIGH CVEs came from build tools left in the image.
- **SHA tags make deploys easy to trace.** `kubectl get deploy -o wide` shows the exact commit that is running, and `helm rollback` goes back to a known good one.
- **Cloud servers cost money while they exist.** No NAT gateway, one small computer and deleting everything right after use keep the AWS bill under a dollar.

## Demo walkthrough

| File | What it is |
|---|---|
| [`demo/demo-video.mp4`](demo/demo-video.mp4) | The demo video: the slides first, then a live walkthrough of CI/CD, the code, Terraform, Argo CD, Kubernetes, Prometheus and Grafana |
| [`demo/presentation.pptx`](demo/presentation.pptx) | The slides (14 slides) |
| [`demo/slides.pdf`](demo/slides.pdf) | The same slides as a PDF |

A 10 minute tour, from code change to live update. Run it live, or record it.

1. **App:** open http://lostfound.local, report a found item, search for it, then mark it returned.
2. **API:** open `/docs` and run `GET /api/items/stats`.
3. **Database:** `kubectl exec -n lostfound deploy/lostfound-postgres -- psql -U lostfound -d lostfound -c 'select id,status,title from items;'`
4. **Change + commit:** edit a line in `frontend/src/App.jsx`, `git commit -am "..."`, `git push`.
5. **CI:** open the Actions tab and watch `test` -> `build-scan-push` (Trivy) -> `deploy`.
6. **Registry:** the GHCR packages page, where the new tag is the same as the commit SHA.
7. **Deploy:** run `./scripts/deploy-local.sh`. It rolls the same commit SHA out to the cluster with `helm upgrade --install`.
8. **Terraform:** walk through `terraform/main.tf` and `eks.tf`, then the plan screenshot.
9. **Kubernetes + Helm:** `kubectl get pods,svc,ingress,hpa -n lostfound`, `helm history lostfound -n lostfound` (a new revision for each deploy).
10. **Updated page:** refresh http://lostfound.local and the change is live.
11. **HPA:** `./scripts/load-test.sh 4000 40` and `kubectl get hpa -n lostfound -w`.
12. **Monitoring:** Prometheus targets UP, Grafana panels moving.
13. **Failure:** `kubectl apply -f k8s/troubleshooting/broken-service.yaml`, find the empty endpoints, fix the selector.

This flow was rehearsed on the laptop. The commit "Reword the hero line..." went through pytest, the frontend build, both image builds with its SHA, both Trivy checks and `helm upgrade` (revision 2):

![Demo: commit to deploy](screenshots/10-demo-commit-to-deploy.png)

The page after the upgrade shows the new line ("Search the board before you report..."):

![Updated page after deploy](screenshots/10-demo-updated-page.png)

## Design choices

A few things are done on purpose in a different way from a standard template:

| Choice | Why |
|---|---|
| The API uses `/api/items` | The app is about lost and found items, so the names match the real things in it. |
| The Helm chart lives in `helm/lostfound/` and the practice labs live in `k8s/troubleshooting/` | One chart folder per app, and all Kubernetes files sit together. |
| AWS uses only public subnets and no NAT gateway | A NAT gateway costs money every hour. Two public subnets are enough for EKS and keep the demo under a dollar. |
| Trivy uses `--ignore-unfixed` | The pipeline stops only for problems that already have a fix. A problem with no fix yet cannot be solved by updating, so it is watched instead of blocking every release. |
| The Service for the backend is named `backend` | nginx in the frontend sends `/api` to `http://backend:8000`, and the same name works in Docker Compose and in Kubernetes. |

## Requirements coverage

This project was built as the final DevOps capstone. The table maps each course module to where it lives in the repo and the screenshot that proves it.

| Module | Requirement | Where in the repo | Proof |
|---|---|---|---|
| **M1** Application | FastAPI with `/health`, at least 4 REST endpoints (7 here), PostgreSQL table by Alembic, frontend calls the API, responsive UI (breakpoint at 640px) | `backend/app/`, `backend/app/routes.py`, `backend/alembic/versions/0001_create_items.py`, `frontend/src/`, `frontend/src/styles.css` | [browser](screenshots/01-app-browser-localhost-3000.png), [Swagger](screenshots/01-swagger-docs.png), [curl CRUD](screenshots/01-api-crud.png), [DB + Alembic](screenshots/01-postgres-alembic.png) |
| **M2** Testing | pytest passes, at least 5 tests on 3 endpoints (11 tests, every endpoint), test DB not production, pytest.ini + conftest.py | `backend/tests/test_items.py`, `backend/tests/conftest.py`, `backend/pytest.ini` | [pytest -v](screenshots/02-pytest-passing.png) |
| **M3** Git and GitHub | Public repo, meaningful commits (25+), `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | https://github.com/Divii2205/campus-lost-and-found, `.gitignore` | [git log](screenshots/03-git-log.png) |
| **M4** Docker | Backend Dockerfile builds, frontend multi-stage (Node to nginx), non-root (uid 10001 / uid 101), `docker compose up --build` starts 3 services | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | [compose up](screenshots/04-docker-compose-up.png), [browser](screenshots/01-app-browser-localhost-3000.png) |
| **M5** CI/CD | Workflow on push to `main`, pytest gate, frontend build, both images, push to GHCR, SHA tags | `.github/workflows/ci-cd.yml` | [green run](https://github.com/Divii2205/campus-lost-and-found/actions/runs/38920194477), [run screenshot](screenshots/05-github-actions-green.png), [lint + key lines](screenshots/05-ci-workflow-lint.png), [GHCR backend](screenshots/05-ghcr-packages.png), [GHCR frontend](screenshots/05-ghcr-packages-frontend.png) |
| **M6** DevSecOps | Trivy on both images in CI, fails on HIGH/CRITICAL, one CVE explained (CVE-2025-47273), no secrets in Git | `.github/workflows/ci-cd.yml`, [Security](#security) | [before](screenshots/06-trivy-backend-before-fix.png), [after](screenshots/06-trivy-images-clean.png), [in pipeline](screenshots/05-trivy-in-pipeline.png), [gitleaks](screenshots/06-secret-scan-gitleaks.png) |
| **M7** Terraform | Valid HCL, init, plan (15 resources), VPC + 2 public subnets, EKS + node group, destroy, tfvars.example | `terraform/` | [init](screenshots/07-terraform-init-validate.png), [plan](screenshots/07-terraform-plan.png), [apply](screenshots/07-terraform-apply.png), [CLI](screenshots/07-aws-cli-vpc-eks.png), [Console VPC](screenshots/07-aws-console-vpc.png), [Console EKS](screenshots/07-aws-console-eks.png), [destroy](screenshots/07-terraform-destroy.png) |
| **M8** Kubernetes + Helm | namespace.yaml, Helm chart, `helm upgrade --install`, 2 replicas each, ClusterIP, Ingress `/` + `/api`, pods Running, HPA | `k8s/`, `helm/lostfound/` | [pods](screenshots/08-kubectl-get-pods.png), [svc](screenshots/08-kubectl-get-svc.png), [helm list](screenshots/08-helm-list.png), [Ingress](screenshots/08-ingress-routing.png), [app via Ingress](screenshots/08-app-via-ingress-lostfound-local.png), [config + probes](screenshots/08-configmap-secret-pvc-probes.png), [HPA](screenshots/08-hpa-scaling.png) |
| **M9** Observability | `/metrics`, Prometheus scraping (UP), Grafana installed, live panel | `monitoring/` | [/metrics](screenshots/09-metrics-endpoint.png), [targets UP](screenshots/09-prometheus-targets-up.png), [Grafana](screenshots/09-grafana-dashboard.png) |
| **M10** Presentation | README explains the app, slides and demo video: commit, pipeline, deploy update | `README.md`, `demo/`, [Demo walkthrough](#demo-walkthrough) | [commit to deploy](screenshots/10-demo-commit-to-deploy.png), [updated page](screenshots/10-demo-updated-page.png) |

## Author

**Divijaa** · GitHub [@Divii2205](https://github.com/Divii2205) · Repository [Divii2205/campus-lost-and-found](https://github.com/Divii2205/campus-lost-and-found)
