## Running Locally (Python)

```bash
python3 -m venv ~/zapzap-env
source ~/zapzap-env/bin/activate
pip install --no-cache-dir -r requirements.txt
source .env
uvicorn main:app --reload --host 0.0.0.0 --port 2121
```
You will need to setup a local proxy to the production database. Install https://github.com/GoogleCloudPlatform/cloud-sql-proxy and run: 

```bash
# command line
./cloud_sql_proxy -instances=zapzap-me:europe-west1:postgres-instance=tcp:127.0.0.1:5432

# via Docker
docker run -d \
  -v ~/.config/gcloud/application_default_credentials.json:/path/to/service-account-key.json \
  -p 127.0.0.1:5432:5432 \
  gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.14.2 \
  --address 0.0.0.0 --port 5432 \
  --credentials-file /path/to/service-account-key.json instances=zapzap-me:europe-west1
```

## Running Locally (Docker)

```bash
source .env
docker build -t zapzap-backend -f Dockerfile
docker run -p 8080:8080 --env ENVIRONMENT=development --env BREEZ_API_KEY=$BREEZ_API_KEY --env BREEZ_MNEMONIC=$BREEZ_MNEMONIC  --env BREEZ_DATA_PATH=./  zapzap-backend
```

## Pushing Builds

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker build -t zapzap-backend -f Dockerfile --platform linux/x86_64 .
docker push zapzap-backend europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend
gcloud run deploy cloudrun-service  --image europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend
```

## Development Setup

- Linting: Ruff
- Fomatting: Black

1. Install dependencies:

   ```bash
   pip install black ruff pre-commit
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