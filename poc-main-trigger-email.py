import functions_framework
import requests
from datetime import timedelta
import google.auth
from google.cloud import storage
from flask import Flask, request
from google.auth.transport.requests import Request


WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzgGsoyPh90b_mWFXd2W3YRnQRMDYCes4oXaKQnbkfK70lplaANsE9OebAh0nZM1gr7/exec"
SIGNED_URL_SERVICE = "https://poc-get-url-88050344039.us-east1.run.app"
def transformar_cadena(cadena):
    """
    Extrae una porción de una cadena, reemplaza guiones bajos con puntos y agrega un sufijo.

    Args:
        cadena (str): La cadena de entrada.

    Returns:
        str: La cadena transformada, o un mensaje de error si no se puede procesar.
    """
    try:
        # Encontrar el índice del primer guion "-"
        inicio = cadena.find('-')
        if inicio == -1:
            return "Error: Not found '-' in the string"

        # Encontrar el índice de ".docx"
        fin = cadena.find('.docx')
        if fin == -1:
            return "Error: Not found '.docx' in the string"

        # Extraer la subcadena entre el primer guion y ".docx"
        subcadena = cadena[inicio + 1:fin]

        # Reemplazar guiones bajos "_" con puntos "."
        subcadena_transformada = subcadena.replace('_', '.')

        # Agregar el sufijo "@devengine.ca"
        resultado = subcadena_transformada + "@devengine.ca"
        return resultado

    except Exception as e:
        return f"Error: An error occurred during processing: {e}"


@functions_framework.http
def hello_http(request):
    try:
        request_json = request.get_json(silent=True)
    except Exception as e:
        print(f"Error processing the event: {e}")
    # finally:
        # data = cloud_event["data"]
    try:
        # Llamada a la Cloud Run que devuelve todas las URLs firmadas
        response = requests.get(SIGNED_URL_SERVICE)
        response.raise_for_status()

        # Parsear respuesta JSON
        file_list = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting signed URL: {e}")
        return {"Error": str(e)}, 400

    bucket = request_json["bucket"]
    name = request_json["name"]
    email = transformar_cadena(name)
    print(email)
    # Generate the public URL for the file
    match = next((file for file in file_list if file["filename"] == name), None)


    if not match:
        print(f"Signed URL not found for file: {name}")
        return {"Error": "File not found"}, 404

        # Return only the matching file
    signed_url = match["url"]
    print(f"Signed URL found: {signed_url}")

    params = {
        "name": name,
        "bucket": bucket,
        "url": signed_url,
        "email": email
        }

    try:
        # Make an HTTP GET request to the web app
        response = requests.get(WEB_APP_URL, params=params)
        response.raise_for_status()  # Raise exception for HTTP error codes
        print(f"Apps Script triggered successfully. Response: {response.text}")
        return {"signed_url": signed_url}, 200 
    except requests.exceptions.RequestException as e:
        print(f"Error triggering Apps Script: {e}")
        return {"Error": str(e)}, 400

    