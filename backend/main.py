import os
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import storage, firestore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Allow all origins for development. For production, you'd want to restrict this.
CORS(app)

# Initialize Google Cloud clients
try:
    storage_client = storage.Client()
    db = firestore.Client()
except Exception as e:
    print(f"Error initializing Google Cloud clients: {e}")
    # Handle the error appropriately in a real application
    storage_client = None
    db = None

# Get the GCS bucket name from environment variables
BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")

@app.route("/files", methods=["GET"])
def list_files():
    """Lists all files in the configured GCS bucket."""
    if not BUCKET_NAME or not storage_client:
        return jsonify({"error": "GCS_BUCKET_NAME not configured or storage client not initialized"}), 500

    try:
        blobs = storage_client.list_blobs(BUCKET_NAME)
        file_list = [
            {"name": blob.name, "updated": blob.updated.isoformat()} for blob in blobs
        ]
        return jsonify(file_list)
    except Exception as e:
        return jsonify({"error": f"Could not list files: {e}"}), 500

@app.route("/generate-signed-url", methods=["POST"])
def generate_signed_url():
    """Generates a time-limited signed URL for a specific file."""
    if not BUCKET_NAME or not storage_client or not db:
        return jsonify({"error": "Application not configured correctly"}), 500

    data = request.get_json()
    if not data or "fileName" not in data:
        return jsonify({"error": "fileName is required"}), 400

    file_name = data["fileName"]
    # Default expiration to 15 minutes, but allow it to be overridden
    expiration_minutes = int(data.get("expiration", 15))
    expiration_delta = datetime.timedelta(minutes=expiration_minutes)

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)

        if not blob.exists():
            return jsonify({"error": "File not found"}), 404

        # Generate the signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_delta,
            method="GET",
        )

        # Store metadata about the generated URL in Firestore for tracking
        doc_ref = db.collection("signed_urls").document()
        doc_ref.set({
            "file_name": file_name,
            "signed_url_hash": hash(signed_url), # Don't store the full URL
            "created_at": firestore.SERVER_TIMESTAMP,
            "expires_at": datetime.datetime.utcnow() + expiration_delta,
            "is_active": True,
            "accessed_at": None,
        })

        # Return the actual URL to the client, and the ID for our reference
        return jsonify({"signed_url": signed_url, "id": doc_ref.id})

    except Exception as e:
        return jsonify({"error": f"Could not generate signed URL: {e}"}), 500

@app.route("/active-links", methods=["GET"])
def get_active_links():
    """Retrieves a list of all active, non-expired links from Firestore."""
    if not db:
        return jsonify({"error": "Firestore client not initialized"}), 500

    try:
        now = datetime.datetime.utcnow()
        # Query for links that are active and haven't expired yet
        links_ref = db.collection("signed_urls").where("expires_at", ">", now).where("is_active", "==", True).order_by("expires_at", direction=firestore.Query.DESCENDING)
        
        links = []
        for doc in links_ref.stream():
            link_data = doc.to_dict()
            link_data["id"] = doc.id
            # Convert datetime objects to ISO 8601 strings for JSON compatibility
            for key, value in link_data.items():
                if isinstance(value, datetime.datetime):
                    link_data[key] = value.isoformat() + "Z"
            links.append(link_data)
            
        return jsonify(links)
    except Exception as e:
        return jsonify({"error": f"Could not retrieve active links: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))