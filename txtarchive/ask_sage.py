import os
import requests

def ingest_document(document_path, endpoint="train"):
    """
    Ingest a document into Ask Sage using the specified endpoint.

    Parameters:
        document_path (str): The path to the document to be ingested.
        endpoint (str): The Ask Sage endpoint to use ('train', 'chat', 'embed', 'upload')

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
    with open(document_path, "r", encoding="utf-8") as file:
        document_content = file.read()

    # Define the API endpoint URL
    endpoint_urls = {
        'train': 'https://api.asksage.ai/server/train',
        'upload': 'https://api.asksage.ai/server/upload', 
        'embed': 'https://api.asksage.ai/server/embed',
        'chat': 'https://api.asksage.ai/server/chat'
    }
    
    if endpoint not in endpoint_urls:
        raise ValueError(f"Unknown endpoint: {endpoint}. Valid options: {list(endpoint_urls.keys())}")
    
    api_url = endpoint_urls[endpoint]

    # Make the API request
    headers = {
        "Content-Type": "application/json",
        "x-access-tokens": access_token,
    }
    
    # Different payload structures for different endpoints
    if endpoint == 'chat':
        payload = {
            "message": f"Please analyze this content: {document_content}"
        }
    else:
        payload = {
            "content": document_content,
        }

    response = requests.post(api_url, headers=headers, json=payload)

    # Debugging: Print the response details
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    # Raise an error if the request failed
    if response.status_code != 200:
        raise Exception(f"Failed to ingest document via {endpoint} endpoint: {response.text}")

    return response.json()

def test_endpoints(document_path):
    """
    Test different Ask Sage endpoints to find the best one for ingestion.
    
    Args:
        document_path (str): Path to a test document
        
    Returns:
        dict: Results from testing different endpoints
    """
    import os
    
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise EnvironmentError("ACCESS_TOKEN environment variable is not set.")
    
    endpoints = {
        'train': 'https://api.asksage.ai/server/train',
        'upload': 'https://api.asksage.ai/server/upload', 
        'embed': 'https://api.asksage.ai/server/embed',
        'chat': 'https://api.asksage.ai/server/chat'
    }
    
    # Read document content
    with open(document_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    results = {}
    
    for endpoint_name, endpoint_url in endpoints.items():
        try:
            print(f"Testing {endpoint_name} endpoint...")
            
            headers = {
                "Content-Type": "application/json",
                "x-access-tokens": access_token,
            }
            
            # Different payload structures for different endpoints
            if endpoint_name == 'chat':
                payload = {
                    "message": f"Please analyze this content: {content[:1000]}..."  # Truncate for chat
                }
            else:
                payload = {
                    "content": content,
                }
            
            response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
            
            results[endpoint_name] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_size': len(response.text),
                'content_length': len(content),
                'error': None if response.status_code == 200 else response.text
            }
            
            print(f"  {endpoint_name}: Status {response.status_code}")
            
        except Exception as e:
            results[endpoint_name] = {
                'status_code': None,
                'success': False,
                'response_size': 0,
                'content_length': len(content),
                'error': str(e)
            }
            print(f"  {endpoint_name}: Error - {e}")
    
    return results