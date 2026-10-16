# Campus Lost & Found: DevOps Final Capstone

**Author:** Divijaa · **GitHub:** [Divii2205](https://github.com/Divii2205) · **Repo:** https://github.com/Divii2205/campus-lost-and-found

## In one minute

Campus Lost & Found is a website for a college campus.

- A student who **loses** something (a calculator, an ID card, keys) writes what it is and where they last had it.
- A student who **finds** something writes that down too.
- Anyone can search the board.
- When an item gets back to its owner, it is marked **returned** (claimed).

This project is not only about the website. It shows every step that takes the code from a laptop to a real, watched server setup:

```text
Code → Git → GitHub Actions (pytest → build → Trivy → GHCR) → Terraform (AWS VPC + EKS)
     → Kubernetes + Helm (Ingress, HPA, probes) → Prometheus + Grafana → Troubleshooting
```

Every screenshot in this README is real output from this project. Each one sits in the section it proves. The [grading checklist](#14-grading-checklist) near the end links every line of `GRADING.md` to a file and a screenshot.

## Table of contents

1. [What the app does](#1-what-the-app-does)
2. [Architecture](#2-architecture)
3. [Tech stack](#3-tech-stack)
4. [Folder structure](#4-folder-structure)
5. [Run it locally (M1)](#5-run-it-locally-m1)
6. [Tests (M2)](#6-tests-m2)
7. [Git and GitHub (M3)](#7-git-and-github-m3)
8. [Docker (M4)](#8-docker-m4)
9. [CI/CD pipeline (M5)](#9-cicd-pipeline-m5)
10. [Security scanning (M6)](#10-security-scanning-m6)
11. [Terraform on AWS (M7)](#11-terraform-on-aws-m7)
12. [Kubernetes + Helm (M8)](#12-kubernetes--helm-m8)
13. [Monitoring (M9)](#13-monitoring-m9)
14. [Grading checklist](#14-grading-checklist)
15. [Troubleshooting](#15-troubleshooting)
16. [Final demo script (M10)](#16-final-demo-script-m10)
17. [Lessons learned](#17-lessons-learned)

---

## 1. What the app does

| Who | What they can do |
|---|---|
| Student who lost something | Search the board. If the item is not there, post a **Lost** report with the place and a way to contact them. |
| Student who found something | Post a **Found** report so the owner knows where the item is. |
| Anyone | Show only Lost, only Found or only Back with owner. Search by words ("library", "keys"). Edit or remove a report. |
| Owner gets the item back | Click **Mark returned**, type the owner's name, and the item gets a **Claimed** stamp. |

Each report looks like a paper lost property tag with an ink stamp: red **Lost**, green **Found**, blue **Claimed**.

![Campus Lost & Found running in the browser](screenshots/01-app-browser-localhost-3000.png)

## 2. Architecture

This picture shows how all the parts connect. Read it from top to bottom.

```text
 Developer (Divijaa)
   │ git commit / git push
   ▼
 GitHub repo: Divii2205/campus-lost-and-found
   │
   ▼
 GitHub Actions  (.github/workflows/ci-cd.yml)
   ├─ test             pytest -v (11 tests) + npm ci && npm run build
   ├─ build-scan-push  docker build (tag = commit SHA) → Trivy gate (HIGH/CRITICAL = fail) → push to GHCR
   └─ deploy           helm upgrade --install (runs when a KUBE_CONFIG secret is set)
                │
                ▼
          GHCR: ghcr.io/divii2205/lostfound-backend:<sha>, lostfound-frontend:<sha>

 Terraform (terraform/) ──► AWS ap-south-1: VPC + 2 public subnets + IGW + EKS + managed node group

 Kubernetes (namespace "lostfound", installed with helm/lostfound)
   Ingress lostfound.local ──┬── "/"    → Service lostfound-frontend → 2× nginx pods (React build)
                             └── "/api" → Service backend           → 2-5× FastAPI pods (HPA)
                                                                        │
                                                       Service lostfound-postgres → PostgreSQL + PVC
   Prometheus ── ServiceMonitor ──► backend /metrics          Grafana ── dashboard "Campus Lost & Found API"
```

In plain words:

1. Divijaa writes code and sends it to GitHub.
2. GitHub Actions tests the code, builds the app boxes, checks them for security problems and stores them.
3. Terraform builds the servers on AWS.
4. Kubernetes runs the app boxes. Helm tells Kubernetes what to run.
5. Prometheus and Grafana watch the app and draw charts.

## 3. Tech stack

Here is every tool, with one plain line about what it does.

| Layer | Tool | What it means in plain words |
|---|---|---|
| Frontend | React 18 + Vite, plain CSS (responsive), served by unprivileged nginx | The page you see in the browser. React builds the page, Vite packs it, CSS makes it look nice on phones and laptops, and nginx is a small web server that hands the page to the browser. |
| Backend | FastAPI, SQLAlchemy 2, Pydantic, Uvicorn | The part that answers requests. FastAPI is the Python web framework, SQLAlchemy talks to the database, Pydantic checks that incoming data is correct, and Uvicorn runs the server. |
| Database | PostgreSQL 16, Alembic migrations | PostgreSQL stores all the reports. Alembic creates and updates the database tables from code. |
| Tests | pytest + FastAPI TestClient, throwaway SQLite database | pytest runs automatic checks on the code. SQLite is a tiny database used only during tests and then thrown away. |
| Containers | Docker (non-root images), Docker Compose | Docker puts the app in a box so it runs the same on every computer. Docker Compose starts several boxes together with one command. |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) | GitHub Actions is a robot that tests and builds the code every time it is pushed. GHCR is a shelf on GitHub where the built boxes are stored. |
| Security | Trivy (image scan gate), gitleaks (secret scan) | Trivy looks inside each box for known security holes. gitleaks looks for passwords or keys saved by mistake. |
| Infrastructure | Terraform + AWS (VPC, subnets, IGW, EKS, node group, IAM) | AWS is Amazon's cloud where you rent computers. Terraform writes down the servers you want in a file and then builds them for you. |
| Kubernetes | kind (local), Helm 3 chart, ingress-nginx, metrics-server, HPA | Kubernetes runs many boxes and restarts them if they break. kind is a small Kubernetes on your own laptop. Helm is like an installer for apps on Kubernetes. ingress-nginx is the front door that sends visitors to the right part. metrics-server measures CPU use. The HPA adds more copies of the app when it gets busy. |
| Monitoring | kube-prometheus-stack (Prometheus Operator, Prometheus, Grafana) | Prometheus collects numbers about the app every few seconds. Grafana turns those numbers into live charts. |

## 4. Folder structure

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
├── helm/lostfound/           Chart.yaml, values.yaml, values-dev.yaml, templates/
├── monitoring/               prometheus-values.yaml, grafana-values.yaml, grafana-dashboard.yaml
├── scripts/                  deploy-local.sh, load-test.sh
└── screenshots/
```

| Folder | What is inside |
|---|---|
| `backend/` | The Python server, the database setup and the tests |
| `frontend/` | The web page code |
| `.github/workflows/` | The robot steps for GitHub Actions |
| `terraform/` | The files that build the AWS servers |
| `k8s/` | Basic Kubernetes files and the broken files used for practice |
| `helm/lostfound/` | The Helm package that installs the whole app on Kubernetes |
| `monitoring/` | Settings for Prometheus and Grafana |
| `scripts/` | Small helper scripts |
| `screenshots/` | Proof pictures used in this README |

## 5. Run it locally (M1)

"Locally" means on your own computer.

### Fastest way: Docker Compose

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

### Backend without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://lostfound:lostfound@localhost:5432/lostfound'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

To run the web page in development mode: `cd frontend && npm ci && npm run dev`. It sends `/api` requests to port 8000.

### REST API

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

That is 7 item endpoints. They use GET (read), POST (create), PUT (replace), PATCH (change one part) and DELETE (remove). The rubric asks for 4.

![Swagger docs](screenshots/01-swagger-docs.png)

Here every endpoint is called with curl (a command line tool that sends web requests): create, read, update, claim, delete, filter and stats.

![API CRUD with curl](screenshots/01-api-crud.png)

### Database and Alembic

The `items` table holds all the reports. It is created by the Alembic migration `backend/alembic/versions/0001_create_items.py`. A migration is a small script that sets up or changes the database tables.

The backend box runs `alembic upgrade head` before it starts Uvicorn. The `alembic_version` table shows which migration was applied:

![PostgreSQL items table and Alembic version](screenshots/01-postgres-alembic.png)

## 6. Tests (M2)

Tests are small programs that check the code works. Run them like this:

```bash
cd backend
pytest -v
```

- There are **11 tests**. They cover `/health`, `/ready`, `/metrics` and every item endpoint: create, input checking (422), list + filter + search, get + 404, update, claim (and the 409 error on a second claim), delete and stats.
- `tests/conftest.py` swaps the real database for a **fresh SQLite file for each test** (using FastAPI `dependency_overrides`). So the tests never touch the real PostgreSQL database.
- `pytest.ini` sets the Python path, the test folder and which warnings to hide.

![pytest -v: 11 passed](screenshots/02-pytest-passing.png)

The tests run before any box is built. If a test fails, the pipeline stops, and no broken box reaches the registry.

## 7. Git and GitHub (M3)

Git saves every version of the code. GitHub keeps a copy of it online.

- Repository: **https://github.com/Divii2205/campus-lost-and-found** (public)
- There are 23 commits. Every commit is by **Divii2205**, and each message says what changed. For example: "Add Alembic migration that creates the items table" and "Remove pip and setuptools from backend runtime image to fix HIGH CVEs found by Trivy".
- `.gitignore` tells Git to skip `.env`, `__pycache__/`, `node_modules/`, `.venv/`, `dist/`, Terraform state and `terraform.tfvars`.
- `.gitattributes` keeps LF line endings, so shell scripts and YAML files work the same on Windows and Linux.

![Commit history](screenshots/03-git-log.png)

## 8. Docker (M4)

Docker puts the app in a box (called an image) so it runs the same on every computer. A Dockerfile is the recipe for that box.

| File | What it does |
|---|---|
| `backend/Dockerfile` | `python:3.12-slim` → OS security updates → install requirements → **remove pip/setuptools** (see Trivy) → copy Alembic + app → runs as **uid 10001 (appuser)** → `alembic upgrade head && uvicorn` |
| `frontend/Dockerfile` | **multi-stage**: stage 1 `node:22-alpine` runs `npm ci && npm run build`; stage 2 `nginxinc/nginx-unprivileged` serves `dist/` as **uid 101** on port 8080. Node and the build tools never reach the final image. |
| `docker-compose.yml` | postgres (with healthcheck and volume) → backend (waits for postgres to be healthy) → frontend on **localhost:3000** |

Some simple words for the table:

- **Non-root** means the app does not run as the all-powerful admin user. This is safer.
- **Multi-stage** means the first stage builds the page, and only the finished result is copied into a small second box.

`docker compose up --build` starts all three services. Running `id` inside the boxes shows both run as non-root:

![docker compose up --build](screenshots/04-docker-compose-up.png)

The browser at http://localhost:3000 is the screenshot in [section 1](#1-what-the-app-does).

## 9. CI/CD pipeline (M5)

CI/CD means a robot tests, builds and ships the code every time you push. Here the robot is GitHub Actions.

File: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). It runs on **every push to `main`** (and on pull requests to `main`).

| Job | Steps | The build fails when |
|---|---|---|
| `test` | checkout → Python 3.12 → `pip install` → **`pytest -v`** → Node 22 → **`npm ci && npm run build`** | any test fails or the frontend does not compile |
| `build-scan-push` (needs `test`) | build **both** images → **Trivy** scan both → log in to GHCR → **push** | Trivy finds a fixable HIGH/CRITICAL CVE |
| `deploy` (needs `build-scan-push`, `main` only) | `helm upgrade --install` with the new SHA → `kubectl rollout status` | the rollout does not become healthy |

**Image tags are the Git commit SHA**, never `latest`. A SHA is the unique id Git gives each commit.

```text
ghcr.io/divii2205/lostfound-backend:<github.sha>
ghcr.io/divii2205/lostfound-frontend:<github.sha>
```

Why this helps:

- Every running box can be traced back to the exact commit it was built from.
- The owner name is made lowercase (`Divii2205` → `divii2205`) because GHCR only accepts lowercase names.
- The Helm chart refuses to work without a tag (`required "backend.tag must be set to a Git commit SHA"`).

The `deploy` job runs only when the repo has a `KUBE_CONFIG` secret. This is a base64 kubeconfig, which is the login file for a cluster (for example the EKS cluster). Without it, the job prints a skip message, and the images still land in GHCR. For the local kind cluster, `scripts/deploy-local.sh` runs the same Helm command.

The workflow passes `actionlint` (a checker for GitHub Actions files). These are its key lines:

![actionlint + key workflow lines](screenshots/05-ci-workflow-lint.png)

### Pipeline run on GitHub

> **To be filled in after the first push.**

- Actions run (green): **`<add link after the first push>`**
- GHCR packages with SHA tags: `screenshots/05-ghcr-packages.png` *(added after the first push)*
- Actions run summary: `screenshots/05-github-actions-green.png` *(added after the first push)*

## 10. Security scanning (M6)

**Trivy in the pipeline.** Trivy looks inside each box for known security holes (called CVEs). Both images are scanned in `build-scan-push` with:

```text
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 <image>
```

`--exit-code 1` makes the step (and the whole pipeline) **fail** when a fixable HIGH or CRITICAL hole is found. So a risky image is never pushed. Trivy runs from the official `aquasec/trivy:0.65.0` container, fixed to one version.

**A real finding and its fix.** The first backend image **failed** the check with 4 HIGH problems:

![Trivy: backend image before the fix](screenshots/06-trivy-backend-before-fix.png)

> **What Trivy scanned and what the result means.**
> Trivy looked at the Debian OS packages and all 37 Python packages inside the backend image. It found 4 HIGH CVEs.
> One example is **CVE-2025-47273**. It is a path traversal bug in **setuptools 70.3.0**. A specially made package address can write files outside the folder it should stay in. It is fixed in 78.1.1.
> The other three were two urllib3 CVEs and one msgpack CVE.
> None of these were the app's own libraries. They came from **pip and setuptools** (and the libraries pip carries with it), which were left in the image after the install step.
> The app never needs them while it runs, so the Dockerfile now removes them after `pip install`.
> The new scan is clean: 0 HIGH/CRITICAL in both images, and the check passes.

![Trivy: both images clean after the fix](screenshots/06-trivy-images-clean.png)

**No secrets in Git.** gitleaks checked the whole history, and no secret files are saved in Git. AWS keys live only in `~/.aws/credentials` (made by `aws configure`). The database password in Kubernetes is a Secret set by Helm.

![gitleaks: no leaks found](screenshots/06-secret-scan-gitleaks.png)

Trivy is one layer of safety. Other layers are:

| Layer | What it does |
|---|---|
| SAST (for example Bandit) | reads the code itself to find unsafe patterns |
| Dependency scanning (`npm audit` and Trivy fs) | checks the libraries the code uses |
| Secret scanning (gitleaks) | finds passwords or keys saved by mistake |
| Runtime security | non-root containers and `allowPrivilegeEscalation: false`, so a box cannot give itself more power |

## 11. Terraform on AWS (M7)

Terraform writes down the servers you want in files, then builds them on AWS for you. AWS is Amazon's cloud where you rent computers.

Folder: [`terraform/`](terraform). Region **ap-south-1 (Mumbai)**.

| File | Creates |
|---|---|
| `main.tf` | VPC `10.30.0.0/16`, internet gateway, **2 public subnets** in 2 availability zones (tagged for EKS load balancers), public route table + associations |
| `eks.tf` | IAM role for the control plane, **EKS cluster `lostfound-eks`** (standard support only, so no extended support charges), IAM role for nodes, **managed node group** (1× t3.small, scales 1 to 2) |
| `variables.tf` / `terraform.tfvars.example` | region, CIDRs, instance type, node count. **No credentials anywhere**: Terraform reads them from `aws configure`. |
| `outputs.tf` | VPC id, subnet ids, cluster endpoint, and the `aws eks update-kubeconfig` command |

Simple words for the table:

- **VPC**: your own private network inside AWS.
- **Subnet**: a smaller part of that network. "Public" means it can reach the internet.
- **Internet gateway (IGW)**: the door between the network and the internet.
- **EKS**: Kubernetes run by AWS.
- **Node group**: the actual computers that run the app boxes.
- **IAM role**: a set of permissions that says what a service is allowed to do.

**Cost choice:** there is no NAT gateway. The worker computer sits in a public subnet. So this demo costs about $0.15 per hour, and it is destroyed right after the screenshots.

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

### It was really built on AWS

`terraform apply` built all 15 things in about 12 minutes:

![terraform apply](screenshots/07-terraform-apply.png)

The AWS command line shows the VPC, the 2 public subnets (in 2 different zones, ap-south-1a and ap-south-1b), the EKS cluster (Active) and the 1 worker computer (Ready):

![AWS CLI: VPC, subnets, EKS, node](screenshots/07-aws-cli-vpc-eks.png)

The AWS Console (the AWS website) in the Mumbai region. The VPC map shows the network, the 2 public subnets, the route table and the internet gateway:

![AWS Console: VPC resource map](screenshots/07-aws-console-vpc.png)

The EKS cluster with its node group `lostfound-eks-nodes`, Active:

![AWS Console: EKS node group](screenshots/07-aws-console-eks.png)

### Then everything was deleted

Right after the screenshots, `terraform destroy` deleted all 15 things. A check of AWS then found 0 clusters, 0 VPCs, 0 computers, 0 disks, 0 NAT gateways and 0 load balancers left. Nothing keeps costing money. The cluster was up for about 30 minutes.

![terraform destroy and AWS check](screenshots/07-terraform-destroy.png)

## 12. Kubernetes + Helm (M8)

Kubernetes runs the app boxes and restarts them if they break. Helm is like an installer: one command sets up every part of the app.

Local cluster: **kind** (`k8s/kind-config.yaml`, cluster `session21`), with **ingress-nginx** (the front door) and **metrics-server** (measures CPU). The same chart also deploys to EKS.

```bash
kubectl apply -f k8s/namespace.yaml                   # namespace "lostfound"
./scripts/deploy-local.sh                             # build SHA-tagged images, kind load, helm upgrade --install
# which runs:
helm upgrade --install lostfound ./helm/lostfound -n lostfound \
  -f helm/lostfound/values-dev.yaml --set backend.tag=<sha> --set frontend.tag=<sha> --wait
```

What the chart (`helm/lostfound/`) creates:

| Template | Resource |
|---|---|
| `backend.yaml` | Deployment `lostfound-backend` (2 replicas, run by the HPA), **wait-for-db initContainer**, startup/readiness/liveness probes, non-root, resource requests; ClusterIP Service `backend:8000` |
| `frontend.yaml` | Deployment `lostfound-frontend` (2 replicas), probes, non-root; ClusterIP Service `lostfound-frontend:80` |
| `postgres.yaml` | PostgreSQL Deployment + **PVC** (1Gi) + ClusterIP Service |
| `config.yaml` | ConfigMap (app name, environment) + **Secret** (DB user, password, `DATABASE_URL`) |
| `ingress.yaml` | Ingress `lostfound.local`: **`/` → frontend, `/api` → backend** |
| `hpa.yaml` | HPA: backend 2 → 5 pods at 60% CPU |
| `servicemonitor.yaml` | tells Prometheus to read `backend /metrics` every 15s |

Simple words for the table:

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

ClusterIP Services and the pods behind them (endpoints):

![kubectl get svc](screenshots/08-kubectl-get-svc.png)

![helm list](screenshots/08-helm-list.png)

Ingress routing (`/api` → backend pods, `/` → frontend pods):

![Ingress routing](screenshots/08-ingress-routing.png)

The app opened through the Ingress address **http://lostfound.local** (add `127.0.0.1 lostfound.local` to your hosts file first):

![App through the Ingress](screenshots/08-app-via-ingress-lostfound-local.png)

ConfigMap, Secret, PVC and the three probes:

![ConfigMap, Secret, PVC, probes](screenshots/08-configmap-secret-pvc-probes.png)

**HPA.** While `scripts/load-test.sh` sent lots of traffic, the backend CPU went above 60% of its request. The HPA then grew it from 2 to 3 pods ("New size: 3; reason: cpu resource utilization above target"):

![HPA scaling](screenshots/08-hpa-scaling.png)

## 13. Monitoring (M9)

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
| `prometheus-values.yaml` | lets Prometheus find ServiceMonitors in every namespace, and turns off parts a small cluster does not need |
| `grafana-values.yaml` | turns on the dashboard helper (sidecar). No admin password is saved in Git: the chart makes one and keeps it in a Secret. |
| `grafana-dashboard.yaml` | a ConfigMap that holds the dashboard. Grafana loads it by itself. |

`/metrics` gives numbers in the Prometheus text format: how many requests came in for each route, method and status, plus how long they took (latency histograms):

![curl /metrics](screenshots/09-metrics-endpoint.png)

Prometheus **Targets**: every backend pod found by the ServiceMonitor is **UP** (3/3 while the HPA had grown the backend):

![Prometheus targets UP](screenshots/09-prometheus-targets-up.png)

The Grafana dashboard **Campus Lost & Found API** with live data during the load test. It shows requests per second for each route, p95 latency (95 out of 100 requests were faster than this), error rate (the load test asks for a missing item on purpose, which gives 404s), backend pods up, and CPU for each pod:

![Grafana dashboard](screenshots/09-grafana-dashboard.png)

## 14. Grading checklist

This table links each rubric line in `GRADING.md` to the file or screenshot that proves it.

| Module | Rubric line | Where |
|---|---|---|
| **M1** | FastAPI starts, `/health` responds | `backend/app/main.py`, [API screenshot](screenshots/01-api-crud.png) |
| | ≥ 4 REST endpoints (GET, POST, PUT, DELETE) | 7 item endpoints, `backend/app/routes.py`, [Swagger](screenshots/01-swagger-docs.png) |
| | PostgreSQL table via Alembic | `backend/alembic/versions/0001_create_items.py`, [DB screenshot](screenshots/01-postgres-alembic.png) |
| | Frontend renders and calls the API | `frontend/src/`, [browser](screenshots/01-app-browser-localhost-3000.png) |
| | Responsive, usable UI | `frontend/src/styles.css` (mobile breakpoint at 640px) |
| **M2** | pytest runs without errors | [pytest -v](screenshots/02-pytest-passing.png) |
| | ≥ 5 tests on ≥ 3 endpoints | 11 tests, every endpoint, `backend/tests/test_items.py` |
| | Test DB, not production | `backend/tests/conftest.py` (SQLite per test) |
| | pytest.ini / conftest.py | both present |
| **M3** | Public GitHub repo | https://github.com/Divii2205/campus-lost-and-found |
| | Meaningful commits (≥ 10) | 23 commits, [git log](screenshots/03-git-log.png) |
| | .gitignore: .env, \_\_pycache\_\_, node_modules, .venv | `.gitignore` |
| **M4** | backend/Dockerfile builds | [compose](screenshots/04-docker-compose-up.png) |
| | frontend multi-stage (Node → nginx) | `frontend/Dockerfile` |
| | Non-root images | uid 10001 / uid 101 in the [compose screenshot](screenshots/04-docker-compose-up.png) |
| | `docker compose up --build` starts 3 services | [compose](screenshots/04-docker-compose-up.png) |
| **M5** | Workflow file, push to `main`, pytest gate, frontend build, both images, GHCR push, SHA tags | `.github/workflows/ci-cd.yml`, [lint + key lines](screenshots/05-ci-workflow-lint.png), Actions run link in [section 9](#pipeline-run-on-github) |
| **M6** | Trivy on both images in CI, fails on HIGH/CRITICAL, CVE explained | [section 10](#10-security-scanning-m6), [before](screenshots/06-trivy-backend-before-fix.png) / [after](screenshots/06-trivy-images-clean.png) |
| **M7** | Valid HCL, init, plan, VPC + 2 public subnets, EKS + node group, destroy, tfvars.example | `terraform/`, [init](screenshots/07-terraform-init-validate.png), [plan](screenshots/07-terraform-plan.png), [apply](screenshots/07-terraform-apply.png), [AWS Console VPC](screenshots/07-aws-console-vpc.png), [AWS Console EKS](screenshots/07-aws-console-eks.png), [destroy](screenshots/07-terraform-destroy.png) |
| **M8** | namespace.yaml, Helm chart, helm install, 2 replicas, ClusterIP, Ingress `/` + `/api`, pods Running | `k8s/`, `helm/lostfound/`, [section 12](#12-kubernetes--helm-m8) |
| **M9** | `/metrics`, Prometheus scraping (UP), Grafana, live panel | `monitoring/`, [section 13](#13-monitoring-m9) |
| **M10** | README, live demo | this file, [demo script](#16-final-demo-script-m10) |

## 15. Troubleshooting

These are real problems found while building this project. Each one lists what went wrong, why, the fix and the proof.

### 15.1 Backend kept crashing on the first Helm install

- **What we saw:** backend pods were `Running` but had **4 restarts** right after `helm install`.
- **Logs:** `psycopg.OperationalError: connection failed ... port 5432 failed: Connection refused`
- **Why:** both pods start at the same time. The backend runs `alembic upgrade head` before PostgreSQL is ready to accept connections. The migration fails, the box stops, and Kubernetes restarts it again and again until the database is up.

![Backend restarts before the fix](screenshots/11-troubleshoot-backend-restarts-before.png)

- **Fix:** a `wait-for-db` **initContainer** in `templates/backend.yaml`. It runs `pg_isready` over and over until the database answers. (The first try printed `no attempt`. This was because uid 10001 has no user entry in the postgres image, so `pg_isready` needs `-U lostfound`.)
- **Proof:** a clean reinstall plus a planned database restart. The init log shows "waiting for db … accepting connections", and every pod has 0 restarts.

![Backend after the fix](screenshots/11-troubleshoot-backend-restarts-after.png)

### 15.2 Trivy check failed on the backend image

See [section 10](#10-security-scanning-m6). pip and setuptools were left in the image and carried 4 HIGH CVEs. The fix was to remove them after the install step.

### 15.3 Practice: ImagePullBackOff (`k8s/troubleshooting/broken-image.yaml`)

ImagePullBackOff means Kubernetes cannot download the image. `kubectl describe pod` shows the tag `does-not-exist` cannot be pulled. The fix is `kubectl set image` with a real commit SHA tag.

![ImagePullBackOff and fix](screenshots/11-troubleshoot-imagepullbackoff.png)

### 15.4 Practice: Service with no endpoints (`k8s/troubleshooting/broken-service.yaml`)

The Service looks for pods with `app=lostfound-api`, but the pods are labelled `app=lostfound-backend`. So the Service finds no pods (no endpoints) and no traffic gets through. Fixing the selector fills in the endpoints.

![Service no endpoints and fix](screenshots/11-troubleshoot-service-no-endpoints.png)

### 15.5 Smaller problems

| Problem | Why | Fix |
|---|---|---|
| `vite build` failed on the Windows laptop: `@rollup/rollup-win32-x64-msvc ... blocked by Application Control policy` | Windows blocks the native Rollup program | build inside `node:22-alpine` (same as the Dockerfile and CI) |
| Grafana panels were empty on first load | panels relied on the "default" data source | each panel now names the data source `uid: prometheus` |
| GHCR rejects `ghcr.io/Divii2205/...` | GHCR needs lowercase names | workflow uses `${GITHUB_REPOSITORY_OWNER,,}` |

## 16. Final demo script (M10)

Live (or recorded if remote). About 10 minutes.

1. **App:** open http://lostfound.local, report a found item, search for it, then mark it returned.
2. **API:** open `/docs` and run `GET /api/items/stats`.
3. **Database:** `kubectl exec -n lostfound deploy/lostfound-postgres -- psql -U lostfound -d lostfound -c 'select id,status,title from items;'`
4. **Change + commit:** edit a line in `frontend/src/App.jsx`, `git commit -am "..."`, `git push`.
5. **CI:** open the Actions tab and watch `test` → `build-scan-push` (Trivy) → `deploy`.
6. **Registry:** the GHCR packages page, where the new tag is the same as the commit SHA.
7. **Terraform:** walk through `terraform/main.tf` and `eks.tf`, then the plan screenshot.
8. **Kubernetes + Helm:** `kubectl get pods,svc,ingress,hpa -n lostfound`, `helm history lostfound -n lostfound` (a new revision for each deploy).
9. **Updated page:** refresh http://lostfound.local and the change is live.
10. **HPA:** `./scripts/load-test.sh 4000 40` and `kubectl get hpa -n lostfound -w`.
11. **Monitoring:** Prometheus targets UP, Grafana panels moving.
12. **Failure:** `kubectl apply -f k8s/troubleshooting/broken-service.yaml`, find the empty endpoints, fix the selector.

This flow was practiced on the laptop. The commit "Reword the hero line…" went through pytest, the frontend build, both image builds with its SHA, both Trivy checks and `helm upgrade` (revision 2):

![Demo: commit to deploy](screenshots/10-demo-commit-to-deploy.png)

The page after the upgrade shows the new line ("Search the board before you report…"):

![Updated page after deploy](screenshots/10-demo-updated-page.png)

## 17. Lessons learned

- **Ready is not the same as alive.** `/health` only says the program is running. `/ready` also checks the database, so Kubernetes sends visitors only to pods that can really help them.
- **Start order matters.** In Compose, `depends_on: service_healthy` handles it. Kubernetes has no start order, so an initContainer does the waiting.
- **Most security holes come from things you did not mean to ship.** The app's own libraries were clean. The HIGH CVEs came from build tools left in the image.
- **SHA tags make deploys easy to trace.** `kubectl get deploy -o wide` shows the exact commit that is running, and `helm rollback` goes back to a known good one.
- **Cloud servers cost money while they exist.** No NAT gateway, one small computer and deleting everything right after the demo keep the AWS bill under a dollar.
