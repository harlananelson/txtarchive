import os
import requests

def ingest_document(document_path):
    """
    Ingest a document into Ask Sage using the /train endpoint.

    Parameters:
        document_path (str): The path to the document to be ingested.

    Returns:
        dict: The API response as a dictionary.
    """
    # Retrieve the access token from the environment variable
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise EnvironmentError("ACCESS_TOKEN environment variable is not set.")

    # Ensure the document exists
    if not os.path.exists(document_path):
        raise FileNotFoundError(f"Document not found: {document_path}")

    # Read the content of the document
    with open(document_path, "r") as file:
        document_content = file.read()

    # Define the API endpoint
    api_url = "https://api.asksage.ai/server/train"

    # Make the API request
    headers = {
        "Content-Type": "application/json",
        "x-access-tokens": access_token,
    }
    payload = {
        "content": document_content,
    }

    response = requests.post(api_url, headers=headers, json=payload)

    # Debugging: Print the response details
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    # Raise an error if the request failed
    if response.status_code != 200:
        raise Exception(f"Failed to ingest document: {response.text}")

    return response.json()