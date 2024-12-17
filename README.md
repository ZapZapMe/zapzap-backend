## Python Local

```bash
python3 -m venv ~/zapzap-env
source ~/zapzap-env/bin/activate
pip install --no-cache-dir -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 2121
```

# via Docker Local
```bash
docker build -t zapzap-backend -f Dockerfile
docer run zapzap-backend:latest
```


## Pushing builds

```bash
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker build -t zapzap-backend -f Dockerfile --platform linux/x86_64 .
docker push     zapzap-backend europe-west1-docker.pkg.dev/zapzap01/zapzap-repo/zapzap-backend:latest
gcloud run deploy zapzap-backend --image europe-west1-docker.pkg.dev/zapzap01/zapzap-repo/zapzap-backend:latest
```


## infrastrcture

```bash
# project setup
gcloud config set run/region europe-west1
gcloud projects create zapzap01 --name="zapzap"
gcloud config set project zapzap01
# setup billing account at https://console.cloud.google.com/billing/projects

# database password
gcloud services enable secretmanager.googleapis.com
gcloud secrets create db_password --replication-policy="automatic"
echo -n "CSW is not Satoshi" | gcloud secrets versions add db_password --data-file=-
gcloud secrets versions access latest --secret="db_password"

# permissions
gcloud projects add-iam-policy-binding zapzap01 --member="user:simon@imaginator.com" --role="roles/owner"  # admin role
gcloud projects add-iam-policy-binding zapzap01 --member="user:user@gmail.com"       --role="roles/editor" # developer role

# Domain verification
gcloud domains verify zap-zap.me
```