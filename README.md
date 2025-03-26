## Running Locally (Python)

```bash
cd <repo root>
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
source .env
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## VSCode Setup

VSCode 
- Linting: [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
- Fomatting: [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

Install dependencies:

```bash
pip install ruff pre-commit
```


## Authenticate and setup environment

```bash
gcloud auth login
gcloud config set project zapzap-me
gcloud config set run/region europe-west1

# Authenticate docker
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

## Running via Docker Compose (recommended)

export GCLOUD_CREDENTIALS_PATH=/path/to/your/application_default_credentials.json # windows: $env:GCLOUD_CREDENTIALS_PATH = "C:\path\to\your\application_default_credentials.json"
docker-compose up
```

Then browse to:
- http://127.0.0.1:3000
- http://127.0.0.1:8080
```
## Deploying

### beta

shows up at https://api-beta.zap-zap.me

```bash
docker build --tag zapzap-backend:beta  -f Dockerfile --platform linux/x86_64 .
docker push zapzap-backend:beta europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:beta
gcloud run deploy beta --image europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:beta
```

Additionally any commits to the `beta` branch:
- trigger [cloud build for `beta`](https://console.cloud.google.com/cloud-build/builds;region=europe-west1) 
- deploy to [the cloud run instance for `beta`](https://console.cloud.google.com/run/detail/europe-west1/beta) 
- and are avaliable on https://api-beta.zap-zap.me

### production

visible at https://api.zap-zap.me

```bash
docker build -t zapzap-backend:production -f Dockerfile --platform linux/x86_64 .
docker push zapzap-backend:production europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:production
gcloud run deploy production --image europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:production
```

### For Windows
```bash
docker build -t zapzap-backend:production -f Dockerfile --platform linux/x86_64 .
docker tag zapzap-backend:production europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:production
docker push europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:production
gcloud run deploy production --image europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend:production
```

## Database Schema Changes

```bash
# ensure we're at head
cd backend/app
alembic upgrade head

# create a new revision
alembic revision --autogenerate -m "add tweet.user_id with not null"

# make change
alembic upgrade head
```