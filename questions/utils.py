import hmac
import hashlib
import base64
import json
import time

def generate_centrifugo_token(user_id, secret):
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    payload = {
        "sub": str(user_id),         
        "exp": int(time.time()) + 3600 
    }
    
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    message = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"