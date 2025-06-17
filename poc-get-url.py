import functions_framework
from google.cloud import storage
from google.auth import impersonated_credentials
from datetime import timedelta
import json
import os

# Parámetros globales
BUCKET_NAME = "transcription_poc_processed"
SIGNER_SERVICE_ACCOUNT = "poc-service-account@celtic-tendril-455220-v1.iam.gserviceaccount.com"  # reemplaza por tu service account

@functions_framework.http
def signed_urls(request):
    try:
        # Inicializar cliente de Storage
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)

        # Impersonar a la service account que sí puede firmar
        target_scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
        credentials = impersonated_credentials.Credentials(
            source_credentials=client._credentials,
            target_principal=SIGNER_SERVICE_ACCOUNT,
            target_scopes=target_scopes,
            lifetime=300
        )

        # Listar archivos .docx y generar signed URLs
        urls = []
        for blob in bucket.list_blobs():
            if blob.name.endswith(".docx"):
                signed_url = blob.generate_signed_url(
                    expiration=timedelta(minutes=15),
                    method="GET",
                    version="v4",
                    credentials=credentials,
                    service_account_email=SIGNER_SERVICE_ACCOUNT
                )
                urls.append({
                    "filename": blob.name,
                    "url": signed_url
                })
        print(str(urls))
        return (json.dumps(urls), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        return (json.dumps({"error": str(e)}), 500, {'Content-Type': 'application/json'})
