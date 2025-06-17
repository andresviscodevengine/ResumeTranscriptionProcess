import functions_framework
import base64
import json
from google.cloud import storage
from flask import jsonify, Request

BUCKET_NAME = "transcription_poc_uploads_raw" 
@functions_framework.http
def upload_to_bucket(request):
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return jsonify({"error": "No JSON body provided"}), 400

        filename = request_json.get("filename")
        base64_data = request_json.get("base64")
        mime_type = request_json.get("mimeType", "application/octet-stream")

        if not all([filename, base64_data]):
            return jsonify({"error": "Need required fields"}), 400

        # Decodificar el base64
        file_bytes = base64.b64decode(base64_data)

        # Subir al bucket
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(file_bytes, content_type=mime_type)

        return jsonify({
            "message": f"File '{filename}' was correctly uploaded togs://{BUCKET_NAME}/{filename}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500