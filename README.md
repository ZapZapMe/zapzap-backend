## Running Locally (Python)

```bash
python3 -m venv ~/zapzap-env
source ~/zapzap-env/bin/activate
pip install --no-cache-dir -r requirements.txt
source .env
uvicorn main:app --reload --host 0.0.0.0 --port 2121
```

# Running Locally (Docker)

```bash
docker build -t zapzap-backend -f Dockerfile
docer run zapzap-backend
```

## Pushing Builds

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker build -t zapzap-backend -f Dockerfile --platform linux/x86_64 .
docker push     zapzap-backend europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend
gcloud run deploy cloudrun-service  --image europe-west1-docker.pkg.dev/zapzap-me/zapzap-repo/zapzap-backend
```
