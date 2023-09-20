from google.oauth2 import id_token
from google.auth.transport import requests
from config.appconfig import gcpParams

def verifyGoogleIdToken(idToken):
    try:
        idinfo = id_token.verify_oauth2_token(idToken, requests.Request(), gcpParams["oauth-client-id"])
        return idinfo
        
    except  ValueError as e:
        print(f"Error: {e}")
        return None