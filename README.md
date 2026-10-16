# Campus Lost & Found — DevOps Final Capstone

**Author:** Divijaa · **GitHub:** [Divii2205](https://github.com/Divii2205) · **Repo:** https://github.com/Divii2205/campus-lost-and-found

Campus Lost & Found is a web app for a college campus. A student who **loses** something (a calculator, an ID card, keys) posts what it is and where they last had it. A student who **finds** something posts it too. Anyone can search the board, and when an item gets back to its owner it is marked **returned** (claimed).

This project takes that app all the way from code on a laptop to a monitored Kubernetes cluster:

```text
Code → Git → GitHub Actions (pytest → build → Trivy → GHCR) → Terraform (AWS VPC + EKS)
     → Kubernetes + Helm (Ingress, HPA, probes) → Prometheus + Grafana → Troubleshooting
```

Every screenshot in this README is real output from this project, placed in the section it proves. The [grading checklist](#14-grading-checklist) at the end maps every line of `GRADING.md` to a file and a screenshot.

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
| Student who lost something | Search the board. If it isn't there, post a **Lost** report with the place and a contact. |
| Student who found something | Post a **Found** report so the owner knows where it is. |
| Anyone | Filter by Lost / Found / Back with owner, search by text ("library", "keys"), edit or remove a report. |
| Owner gets the item back | Click **Mark returned**, type the owner's name, and the item is stamped **Claimed**. |

Each report is shown as a manila lost-property tag with an ink stamp: red **Lost**, green **Found**, blue **Claimed**.

![Campus Lost & Found running in the browser](screenshots/01-app-browser-localhost-3000.png)

## 2. Architecture

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

## 3. Tech stack

| Layer | Tool |
|---|---|
| Frontend | React 18 + Vite, plain CSS (responsive), served by unprivileged nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic, Uvicorn |
| Database | PostgreSQL 16, Alembic migrations |
| Tests | pytest + FastAPI TestClient, throwaway SQLite database |
| Containers | Docker (non-root images), Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) |
| Security | Trivy (image scan gate), gitleaks (secret scan) |
| Infrastructure | Terraform + AWS (VPC, subnets, IGW, EKS, node group, IAM) |
| Kubernetes | kind (local), Helm 3 chart, ingress-nginx, metrics-server, HPA |
| Monitoring | kube-prometheus-stack (Prometheus Operator, Prometheus, Grafana) |

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

## 5. Run it locally (M1)

### Fastest: Docker Compose

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | the app |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/health | liveness (`{"status":"UP"}`) |
| http://localhost:8000/ready | readiness (checks the database) |
| http://localhost:8000/metrics | Prometheus metrics |

Stop with `docker compose down` (add `-v` to delete the database too).

### Backend without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://lostfound:lostfound@localhost:5432/lostfound'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend dev server: `cd frontend && npm ci && npm run dev` (proxies `/api` to port 8000).

### REST API

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

That is 7 item endpoints using GET, POST, PUT, PATCH and DELETE (the rubric asks for 4).

![Swagger docs](screenshots/01-swagger-docs.png)

Every endpoint called with curl (create, read, update, claim, delete, filter, stats):

![API CRUD with curl](screenshots/01-api-crud.png)

### Database and Alembic

The `items` table is created by the Alembic migration `backend/alembic/versions/0001_create_items.py`. The backend container runs `alembic upgrade head` before it starts Uvicorn, and `alembic_version` shows the migration that was applied:

![PostgreSQL items table and Alembic version](screenshots/01-postgres-alembic.png)

## 6. Tests (M2)

```bash
cd backend
pytest -v
```

- **11 tests** covering `/health`, `/ready`, `/metrics` and every item endpoint: create, input validation (422), list + filter + search, get + 404, update, claim (and the 409 on a second claim), delete, stats.
- `tests/conftest.py` swaps the database for a **fresh SQLite file per test** (FastAPI `dependency_overrides`), so tests never touch the real PostgreSQL database.
- `pytest.ini` sets the Python path, the test folder and warning filters.

![pytest -v: 11 passed](screenshots/02-pytest-passing.png)

Tests run before any image is built. If a test fails, the pipeline stops and no broken image reaches the registry.

## 7. Git and GitHub (M3)

- Repository: **https://github.com/Divii2205/campus-lost-and-found** (public)
- Every commit is by **Divii2205**, and each message says what changed (for example "Add Alembic migration that creates the items table", "Remove pip and setuptools from backend runtime image to fix HIGH CVEs found by Trivy").
- `.gitignore` excludes `.env`, `__pycache__/`, `node_modules/`, `.venv/`, `dist/`, Terraform state and `terraform.tfvars`.
- `.gitattributes` keeps LF line endings, so shell scripts and YAML work the same on Windows and Linux.

![Commit history](screenshots/03-git-log.png)

## 8. Docker (M4)

| File | What it does |
|---|---|
| `backend/Dockerfile` | `python:3.12-slim` → OS security updates → install requirements → **remove pip/setuptools** (see Trivy) → copy Alembic + app → runs as **uid 10001 (appuser)** → `alembic upgrade head && uvicorn` |
| `frontend/Dockerfile` | **multi-stage**: stage 1 `node:22-alpine` runs `npm ci && npm run build`; stage 2 `nginxinc/nginx-unprivileged` serves `dist/` as **uid 101** on port 8080. Node and the build tools never reach the final image. |
| `docker-compose.yml` | postgres (with healthcheck and volume) → backend (waits for postgres to be healthy) → frontend on **localhost:3000** |

`docker compose up --build` starts all three services. `id` inside the containers shows both run as non-root:

![docker compose up --build](screenshots/04-docker-compose-up.png)

The browser at http://localhost:3000 is the screenshot in [section 1](#1-what-the-app-does).

## 9. CI/CD pipeline (M5)

File: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). It runs on **every push to `main`** (and on pull requests to `main`).

| Job | Steps | Fails the build when |
|---|---|---|
| `test` | checkout → Python 3.12 → `pip install` → **`pytest -v`** → Node 22 → **`npm ci && npm run build`** | any test fails or the frontend doesn't compile |
| `build-scan-push` (needs `test`) | build **both** images → **Trivy** scan both → log in to GHCR → **push** | Trivy finds a fixable HIGH/CRITICAL CVE |
| `deploy` (needs `build-scan-push`, `main` only) | `helm upgrade --install` with the new SHA → `kubectl rollout status` | the rollout doesn't become healthy |

**Image tags are the Git commit SHA**, never `latest`:

```text
ghcr.io/divii2205/lostfound-backend:<github.sha>
ghcr.io/divii2205/lostfound-frontend:<github.sha>
```

So every running container can be traced back to the exact commit it was built from. The owner is lowercased (`Divii2205` → `divii2205`) because GHCR only accepts lowercase names. The Helm chart refuses to render without a tag (`required "backend.tag must be set to a Git commit SHA"`).

The `deploy` job runs when the repo has a `KUBE_CONFIG` secret (a base64 kubeconfig, for example for the EKS cluster). Without it the job prints a skip message, and the images still land in GHCR. For the local kind cluster, `scripts/deploy-local.sh` runs the same Helm command.

The workflow passes `actionlint` (the GitHub Actions linter), and these are its key lines:

![actionlint + key workflow lines](screenshots/05-ci-workflow-lint.png)

### Pipeline run on GitHub

- Actions run (green): **`<add link after the first push>`**
- GHCR packages with SHA tags: `screenshots/05-ghcr-packages.png` *(added after the first push)*
- Actions run summary: `screenshots/05-github-actions-green.png` *(added after the first push)*

## 10. Security scanning (M6)

**Trivy in the pipeline.** Both images are scanned in `build-scan-push` with

```text
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 <image>
```

`--exit-code 1` makes the step (and the pipeline) **fail** when a fixable HIGH or CRITICAL vulnerability is found, so the image is never pushed. Trivy runs from the official `aquasec/trivy:0.65.0` container, pinned to a version.

**A real finding and its fix.** The first backend image **failed** the gate with 4 HIGH vulnerabilities:

![Trivy: backend image before the fix](screenshots/06-trivy-backend-before-fix.png)

> **What Trivy scanned and what the result means.** Trivy looked at the Debian OS packages and all 37 Python packages inside the backend image. It found 4 HIGH CVEs, for example **CVE-2025-47273**, a path-traversal bug in **setuptools 70.3.0** where a crafted package URL can write files outside the target folder (fixed in 78.1.1), plus two urllib3 CVEs and one msgpack CVE. None of these were app dependencies: they were **pip and setuptools** (and the libraries pip bundles) left in the image from the install step. The app never needs them at runtime, so the Dockerfile now uninstalls them after `pip install`. The rescan is clean: 0 HIGH/CRITICAL in both images, and the gate passes.

![Trivy: both images clean after the fix](screenshots/06-trivy-images-clean.png)

**No secrets in Git.** gitleaks scanned the whole history, and no secret files are tracked. AWS keys live only in `~/.aws/credentials` (from `aws configure`), and the database password in Kubernetes is a Secret set by Helm.

![gitleaks: no leaks found](screenshots/06-secret-scan-gitleaks.png)

Trivy is one security layer. Others: SAST (code scanning such as Bandit), dependency scanning (`npm audit` and Trivy fs), secret scanning (gitleaks), and runtime security (non-root containers, `allowPrivilegeEscalation: false`).

## 11. Terraform on AWS (M7)

Folder: [`terraform/`](terraform). Region **ap-south-1 (Mumbai)**.

| File | Creates |
|---|---|
| `main.tf` | VPC `10.30.0.0/16`, internet gateway, **2 public subnets** in 2 availability zones (tagged for EKS load balancers), public route table + associations |
| `eks.tf` | IAM role for the control plane, **EKS cluster `lostfound-eks`** (standard support only, so no extended-support charges), IAM role for nodes, **managed node group** (1× t3.small, scales 1-2) |
| `variables.tf` / `terraform.tfvars.example` | region, CIDRs, instance type, node count. **No credentials anywhere**: Terraform reads them from `aws configure`. |
| `outputs.tf` | VPC id, subnet ids, cluster endpoint, and the `aws eks update-kubeconfig` command |

Cost choice: no NAT gateway. The worker node sits in a public subnet, so this demo costs roughly $0.15 per hour and is destroyed right after the screenshots.

```bash
cd terraform
terraform init
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name lostfound-eks
terraform destroy
```

![terraform init + validate](screenshots/07-terraform-init-validate.png)

`terraform plan`: 15 resources to add, 0 errors:

![terraform plan](screenshots/07-terraform-plan.png)

*Apply, AWS Console and destroy screenshots are added in the next step (`07-terraform-apply.png`, `07-aws-console-vpc.png`, `07-aws-console-eks.png`, `07-terraform-destroy.png`).*

## 12. Kubernetes + Helm (M8)

Local cluster: **kind** (`k8s/kind-config.yaml`, cluster `session21`) with **ingress-nginx** and **metrics-server**. The same chart deploys to EKS.

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
| `servicemonitor.yaml` | tells Prometheus to scrape `backend /metrics` every 15s |

All pods **Running**, 2 replicas each for backend and frontend, 0 restarts:

![kubectl get pods](screenshots/08-kubectl-get-pods.png)

ClusterIP Services and their endpoints:

![kubectl get svc](screenshots/08-kubectl-get-svc.png)

![helm list](screenshots/08-helm-list.png)

Ingress routing (`/api` → backend pods, `/` → frontend pods):

![Ingress routing](screenshots/08-ingress-routing.png)

The app opened through the Ingress host **http://lostfound.local** (add `127.0.0.1 lostfound.local` to your hosts file):

![App through the Ingress](screenshots/08-app-via-ingress-lostfound-local.png)

ConfigMap, Secret, PVC and the three probes:

![ConfigMap, Secret, PVC, probes](screenshots/08-configmap-secret-pvc-probes.png)

**HPA.** Under `scripts/load-test.sh` the backend CPU went above 60% of its request, and the HPA scaled it from 2 to 3 pods ("New size: 3; reason: cpu resource utilization above target"):

![HPA scaling](screenshots/08-hpa-scaling.png)

## 13. Monitoring (M9)

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

- `prometheus-values.yaml` lets Prometheus pick up ServiceMonitors from every namespace, and turns off parts a small cluster doesn't need.
- `grafana-values.yaml` turns on the dashboard sidecar. No admin password is committed: the chart generates one into a Secret.
- `grafana-dashboard.yaml` is a ConfigMap with the dashboard. Grafana loads it automatically.

`/metrics` returns Prometheus text format: request counts per route, method and status, plus latency histograms:

![curl /metrics](screenshots/09-metrics-endpoint.png)

Prometheus **Targets**: every backend pod found by the ServiceMonitor is **UP** (3/3 while the HPA had scaled up):

![Prometheus targets UP](screenshots/09-prometheus-targets-up.png)

Grafana dashboard **Campus Lost & Found API** with live data during the load test: requests per second by route, p95 latency, error rate (the load test asks for a missing item on purpose, giving 404s), backend pods up, and CPU per pod:

![Grafana dashboard](screenshots/09-grafana-dashboard.png)

## 14. Grading checklist

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
| | Meaningful commits (≥ 10) | [git log](screenshots/03-git-log.png) |
| | .gitignore: .env, \_\_pycache\_\_, node_modules, .venv | `.gitignore` |
| **M4** | backend/Dockerfile builds | [compose](screenshots/04-docker-compose-up.png) |
| | frontend multi-stage (Node → nginx) | `frontend/Dockerfile` |
| | Non-root images | uid 10001 / uid 101 in the [compose screenshot](screenshots/04-docker-compose-up.png) |
| | `docker compose up --build` starts 3 services | [compose](screenshots/04-docker-compose-up.png) |
| **M5** | Workflow file, push to `main`, pytest gate, frontend build, both images, GHCR push, SHA tags | `.github/workflows/ci-cd.yml`, [lint + key lines](screenshots/05-ci-workflow-lint.png), Actions run link in [section 9](#pipeline-run-on-github) |
| **M6** | Trivy on both images in CI, fails on HIGH/CRITICAL, CVE explained | [section 10](#10-security-scanning-m6), [before](screenshots/06-trivy-backend-before-fix.png) / [after](screenshots/06-trivy-images-clean.png) |
| **M7** | Valid HCL, init, plan, VPC + 2 public subnets, EKS + node group, destroy, tfvars.example | `terraform/`, [section 11](#11-terraform-on-aws-m7) |
| **M8** | namespace.yaml, Helm chart, helm install, 2 replicas, ClusterIP, Ingress `/` + `/api`, pods Running | `k8s/`, `helm/lostfound/`, [section 12](#12-kubernetes--helm-m8) |
| **M9** | `/metrics`, Prometheus scraping (UP), Grafana, live panel | `monitoring/`, [section 13](#13-monitoring-m9) |
| **M10** | README, live demo | this file, [demo script](#16-final-demo-script-m10) |

## 15. Troubleshooting

Real problems found while building this project, with the cause, fix and proof.

### 15.1 Backend crash-looped on the first Helm install

- **Symptom:** backend pods `Running` but with **4 restarts** right after `helm install`.
- **Logs:** `psycopg.OperationalError: connection failed ... port 5432 failed: Connection refused`
- **Cause:** both pods start at the same time. The backend runs `alembic upgrade head` before PostgreSQL accepts connections, the migration fails, the container exits, and Kubernetes restarts it until the database is up.

![Backend restarts before the fix](screenshots/11-troubleshoot-backend-restarts-before.png)

- **Fix:** a `wait-for-db` **initContainer** in `templates/backend.yaml` loops on `pg_isready` until the database answers. (A first try printed `no attempt`, because uid 10001 has no user entry in the postgres image, so `pg_isready` needs `-U lostfound`.)
- **Proof:** a clean reinstall plus a deliberate database restart. The init log shows "waiting for db … accepting connections", and every pod has 0 restarts.

![Backend after the fix](screenshots/11-troubleshoot-backend-restarts-after.png)

### 15.2 Trivy gate failed on the backend image

See [section 10](#10-security-scanning-m6): pip and setuptools left in the image carried 4 HIGH CVEs. Fixed by uninstalling them after the install step.

### 15.3 Lab: ImagePullBackOff (`k8s/troubleshooting/broken-image.yaml`)

`kubectl describe pod` shows the tag `does-not-exist` can't be pulled. The fix is `kubectl set image` to a real commit-SHA tag.

![ImagePullBackOff and fix](screenshots/11-troubleshoot-imagepullbackoff.png)

### 15.4 Lab: Service with no endpoints (`k8s/troubleshooting/broken-service.yaml`)

The Service selects `app=lostfound-api`, but the pods are labelled `app=lostfound-backend`, so there are no endpoints and no traffic. Fixing the selector fills in the endpoints.

![Service no endpoints and fix](screenshots/11-troubleshoot-service-no-endpoints.png)

### 15.5 Smaller ones

| Problem | Cause | Fix |
|---|---|---|
| `vite build` failed on the Windows laptop: `@rollup/rollup-win32-x64-msvc ... blocked by Application Control policy` | Windows blocks the native Rollup binary | build inside `node:22-alpine` (same as the Dockerfile and CI) |
| Grafana panels empty on first load | panels relied on the "default" datasource | each panel now names the datasource `uid: prometheus` |
| GHCR rejects `ghcr.io/Divii2205/...` | GHCR needs lowercase names | workflow uses `${GITHUB_REPOSITORY_OWNER,,}` |

## 16. Final demo script (M10)

Live (or recorded if remote). About 10 minutes.

1. **App:** open http://lostfound.local, report a found item, search for it, then mark it returned.
2. **API:** open `/docs` and run `GET /api/items/stats`.
3. **Database:** `kubectl exec -n lostfound deploy/lostfound-postgres -- psql -U lostfound -d lostfound -c 'select id,status,title from items;'`
4. **Change + commit:** edit a line in `frontend/src/App.jsx`, `git commit -am "..."`, `git push`.
5. **CI:** open the Actions tab and watch `test` → `build-scan-push` (Trivy) → `deploy`.
6. **Registry:** GHCR packages page, where the new tag equals the commit SHA.
7. **Terraform:** walk through `terraform/main.tf` and `eks.tf`, then the plan screenshot.
8. **Kubernetes + Helm:** `kubectl get pods,svc,ingress,hpa -n lostfound`, `helm history lostfound -n lostfound` (a new revision per deploy).
9. **Updated page:** refresh http://lostfound.local and the change is live.
10. **HPA:** `./scripts/load-test.sh 4000 40` and `kubectl get hpa -n lostfound -w`.
11. **Monitoring:** Prometheus targets UP, Grafana panels moving.
12. **Failure:** `kubectl apply -f k8s/troubleshooting/broken-service.yaml`, find the empty endpoints, fix the selector.

This flow was rehearsed locally. The commit "Reword the hero line…" went through pytest, the frontend build, both image builds with its SHA, both Trivy gates and `helm upgrade` (revision 2):

![Demo: commit to deploy](screenshots/10-demo-commit-to-deploy.png)

The page after the upgrade shows the new line ("Search the board before you report…"):

![Updated page after deploy](screenshots/10-demo-updated-page.png)

## 17. Lessons learned

- **Readiness is not liveness.** `/health` only says the process is up. `/ready` checks the database, so Kubernetes sends traffic only to pods that can serve it.
- **Start order matters.** `depends_on: service_healthy` handles it in Compose. Kubernetes has no start order, so an initContainer does the waiting.
- **Most CVEs come from what you didn't mean to ship.** The app's own dependencies were clean; the HIGH CVEs came from build tools left in the image.
- **SHA tags make deploys traceable.** `kubectl get deploy -o wide` shows the exact commit that is running, and `helm rollback` returns to a known one.
- **Infrastructure costs money while it exists.** Choosing no NAT gateway, one small node and destroying right after the demo keeps the AWS bill under a dollar.
