# GCS Signed URL Manager - Deployment Guide

This guide provides step-by-step instructions to deploy the full-stack GCS Signed URL Manager application to Google Cloud Run.

The application consists of two services:
- **Backend**: A Python (Flask) API that interacts with Google Cloud Storage and Firestore.
- **Frontend**: A React application that provides the user interface.

## 1. Prerequisites

Before you begin, ensure you have the following installed and configured:

- **Google Cloud SDK (gcloud)**: [Installation Guide](https://cloud.google.com/sdk/docs/install)
- **Docker**: [Installation Guide](https://docs.docker.com/engine/install/)
- **Node.js and npm**: [Installation Guide](https://nodejs.org/)
- **Python**: [Installation Guide](https://www.python.org/downloads/)

## 2. Google Cloud Project Setup

1.  **Create or Select a Project**:
    ```bash
    gcloud projects create YOUR_PROJECT_ID --name="GCS Signed URL App"
    gcloud config set project YOUR_PROJECT_ID
    ```
    Replace `YOUR_PROJECT_ID` with a unique ID for your project.

2.  **Link Billing Account**:
    Ensure your project is linked to a billing account.
    ```bash
    gcloud beta billing projects link YOUR_PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT_ID
    ```

3.  **Enable Required APIs**:
    This command enables all the necessary services for the application.
    ```bash
    gcloud services enable \
      run.googleapis.com \
      storage.googleapis.com \
      firestore.googleapis.com \
      artifactregistry.googleapis.com \
      cloudbuild.googleapis.com
    ```

4.  **Authenticate Docker**:
    Configure Docker to use your Google Cloud credentials to push images to Artifact Registry.
    ```bash
    gcloud auth configure-docker us-central1-docker.pkg.dev
    ```
    (Replace `us-central1` with your preferred region if different).

## 3. Create Cloud Resources

1.  **Create a GCS Bucket**:
    Choose a globally unique name for your bucket.
    ```bash
    gsutil mb -p YOUR_PROJECT_ID -l US-CENTRAL1 gs://YOUR_UNIQUE_BUCKET_NAME
    ```
    *Action*: Upload a few sample files to this bucket via the Cloud Console so you can see them in the app.

2.  **Create a Firestore Database**:
    Go to the Firestore section in the Google Cloud Console and create a database in **Native Mode**. Choose a region (e.g., `us-central`).

3.  **Create an Artifact Registry Repository**:
    This is where your Docker images will be stored.
    ```bash
    gcloud artifacts repositories create gcs-signed-url-repo \
      --repository-format=docker \
      --location=us-central1 \
      --description="Docker repository for GCS Signed URL app"
    ```

## 4. Backend Deployment

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Build the Docker Image**:
    Replace `YOUR_PROJECT_ID` and `us-central1` where necessary.
    ```bash
    docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gcs-signed-url-repo/backend:latest .
    ```

3.  **Push the Image to Artifact Registry**:
    ```bash
    docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gcs-signed-url-repo/backend:latest
    ```

4.  **Deploy to Cloud Run**:
    This command deploys the backend service.
    ```bash
    gcloud run deploy backend-service \
      --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gcs-signed-url-repo/backend:latest \
      --platform=managed \
      --region=us-central1 \
      --allow-unauthenticated \
      --set-env-vars="GCS_BUCKET_NAME=YOUR_UNIQUE_BUCKET_NAME"
    ```
    - `--allow-unauthenticated` makes the API publicly accessible. For a production app, you would secure this.
    - Note the **Service URL** in the output. This is your backend API endpoint.

## 5. Frontend Deployment

1.  **Navigate to the frontend directory**:
    ```bash
    cd ../frontend
    ```

2.  **Build the Docker Image**:
    ```bash
    docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gcs-signed-url-repo/frontend:latest .
    ```

3.  **Push the Image to Artifact Registry**:
    ```bash
    docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gcs-signed-url-repo/frontend:latest
    ```

4.  **Deploy to Cloud Run**:
    At this step, we deploy the frontend without knowledge of the backend URL. We'll fix this in the next step.
    ```bash
    gcloud run deploy frontend-service \
      --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/gcs-signed-url-repo/frontend:latest \
      --platform=managed \
      --region=us-central1 \
      --allow-unauthenticated
    ```
    Note the **Service URL** for the frontend. This is where you will access the web interface.

## 6. Final Configuration

The frontend needs to know the URL of the backend.

1.  **Update the Frontend Service with the Backend URL**:
    Take the backend service URL from step 4 and use it here.
    ```bash
    gcloud run services update frontend-service \
      --region=us-central1 \
      --set-env-vars="REACT_APP_API_URL=YOUR_BACKEND_SERVICE_URL"
    ```
    This will trigger a new revision of the frontend service with the correct environment variable.

2.  **Access Your Application**:
    Open the frontend service URL in your browser. You should now see the dashboard, which successfully calls the backend to list files from your GCS bucket.

## 7. Local Development (Optional)

1.  **Run the Backend**:
    - Navigate to the `backend` directory.
    - Create a `.env` file from `.env.example` and fill in your bucket name.
    - Authenticate for local development: `gcloud auth application-default login`
    - Install dependencies: `pip install -r requirements.txt`
    - Run the server: `python main.py`

2.  **Run the Frontend**:
    - Navigate to the `frontend` directory.
    - Install dependencies: `npm install`
    - Run the server: `npm start`
    - The app will open at `http://localhost:3000`. It will connect to the backend running on `http://localhost:8080` by default.
