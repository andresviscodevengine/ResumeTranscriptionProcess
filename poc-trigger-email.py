import os
import requests
import google.auth
import google.auth.transport.requests
import functions_framework

# La URL de tu función HTTP principal se pasa como variable de entorno.
HTTP_FUNCTION_URL = os.environ.get('HTTP_FUNCTION_URL')

def get_identity_token(audience_url):
    """
    Obtiene un token de identidad directamente del servidor de metadatos de GCP.
    Este método es el más robusto y no depende de versiones específicas de google-auth.
    """
    # URL especial del servidor de metadatos, siempre disponible en el entorno de GCP.
    metadata_server_url = (
        "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"
    )
    
    # Parámetros para la petición del token.
    params = {'audience': audience_url}
    headers = {'Metadata-Flavor': 'Google'}

    try:
        # Realizar la petición GET al servidor de metadatos.
        response = requests.get(metadata_server_url, params=params, headers=headers)
        
        # Lanza una excepción si la respuesta es un error (ej: 4xx, 5xx).
        response.raise_for_status() 
        
        # El token es el cuerpo de la respuesta en texto plano.
        identity_token = response.text
        return identity_token

    except requests.exceptions.RequestException as e:
        print(f"CRITICAL error obtaining token from metadata server: {e}")
        # It is vital to re-raise the exception so the function execution fails
        # y puedas ver claramente el problema en los logs.
        raise

@functions_framework.cloud_event
def eventarc_adapter_function(cloud_event):
    """
    Se activa con un evento de Cloud Storage y llama a la función HTTP principal.
    """
    if not HTTP_FUNCTION_URL:
        print("Error: The environment variable 'HTTP_FUNCTION_URL' is not set.")
        # It's better to fail with an exception so the error is visible.
        raise ValueError("The HTTP function URL is not configured.")

    # 1. Extraer datos del evento
    data = cloud_event.data
    bucket = data.get("bucket")
    name = data.get("name")

    if not bucket or not name:
        print(f"Could not extract 'bucket' or 'name' from event: {data}")
        return

    print(f"Event received for: {name} in bucket {bucket}.")

    try:
        # 2. Obtener un token de identidad
        identity_token = get_identity_token(HTTP_FUNCTION_URL)

        # 3. Preparar la llamada HTTP
        headers = {
            'Authorization': f'Bearer {identity_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "bucket": bucket,
            "name": name  # O "filename", dependiendo de lo que espere tu función HTTP
        }
        
        # Tu función HTTP no parece necesitar un cuerpo (payload), así que lo dejamos vacío.
        # Si lo necesitaras, lo añadirías aquí con json={'clave': 'valor'}.
        
        # 4. Llamar a la función HTTP principal
        print(f"Making POST call to {HTTP_FUNCTION_URL} with payload: {payload}")
        response = requests.post(HTTP_FUNCTION_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        print(f"Main function call successful. Response: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error during the invocation of the main HTTP function: {e}")
        # Relanzamos la excepción para que el intento se registre como un fallo.
        raise e