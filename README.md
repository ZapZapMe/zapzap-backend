```bash
gcloud projects create tips-backend
gcloud config set project tips-backend
gcloud services enable compute.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud projects add-iam-policy-binding tips-backend --member="user:simon@imaginator.com" --role="roles/owner"
gcloud beta billing projects link tips-backend --billing-account 01FC12-3BC201-063FED
gcloud secrets create db-password --replication-policy="automatic"
echo -n "my-secret-password" | gcloud secrets versions add db-password --data-file=-
gcloud secrets versions access latest --secret="db-password"

gcloud artifacts repositories create docker-repo --repository-format=docker --location=europe-west1 --description="Docker repository"

#listing AR
gcloud artifacts repositories list
```

