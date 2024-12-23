import hashlib
import requests

def get_hash(func_name, *args):
    # Use MD5 to generate a unique hash combining function name and inputs
    combined_args = ":".join(map(str, args))
    return hashlib.md5(f"{func_name}:{combined_args}".encode()).hexdigest()

def memoize_to_disk(func, *args):
    """
    Memoize the result of 'func(*args)' using a local Flask caching service.
    """
    base_url="http://127.0.0.1:5000"

    # Step 1: Create the cache key (MD5 hash).
    hash_key = get_hash(func.__name__, *args)
    
    # Step 2: Attempt to retrieve the memoized result from the cache service
    get_endpoint = f"{base_url}/cache/{hash_key}"
    try:
        response = requests.get(get_endpoint)
        if response.status_code == 200:
            data = response.json()
            if data["value"] is not None:
                print(f"Reading from service: {hash_key}")
                return data["value"]
    except requests.RequestException as e:
        # If something goes wrong (e.g. service is down), we simply compute anew
        print(f"Error contacting cache service: {e}")

    # Step 3: Compute the result if not found in cache
    result = func(*args)

    # Step 4: Store in the cache
    post_endpoint = f"{base_url}/cache/{hash_key}"
    try:
        response = requests.post(post_endpoint, json={"value": result})
        if response.status_code != 200:
            print(f"Warning: Could not store value in cache. Status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error storing value in cache: {e}")

    return result
