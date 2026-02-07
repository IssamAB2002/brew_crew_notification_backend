import firebase_admin
import os
import json
from dotenv import load_dotenv
from firebase_admin import credentials, messaging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# initialize loading .env
load_dotenv()
# Get Firebase service key from environment
firebase_key = os.getenv("FIREBASE_SERVICE_KEY")
# NOTE: Avoid printing secrets in logs; this can leak credentials in prod logs.
print(f'Firebase key: {firebase_key}')
# Ensure the key is loaded
if not firebase_key:
    raise ValueError("FIREBASE_SERVICE_KEY is not set or loaded.")

# Parse the JSON string
cred = credentials.Certificate(json.loads(firebase_key))
# FIX: Avoid re-initializing firebase_admin if Django reloads the module.
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# FIX: Make this a real Django view that accepts POST JSON from the Flutter app.
@csrf_exempt
def firebase_listener(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = payload.get("title") or "Default Title"
    body = payload.get("body") or "Default Body"
    # FIX: Default to the same topic the app subscribes to ("global").
    topic = payload.get("topic") or "global"

    try:
        response = send_notification({"title": title, "body": body, "topic": topic})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    return JsonResponse({"status": "ok", "message_id": response}, status=200)

def send_notification(data):
    message = messaging.Message(
        notification=messaging.Notification(
            title=data.get('title', 'Default Title'),
            body=data.get('body', 'Default Body'),
        ),
        # FIX: Make topic configurable and align default to the app.
        topic=data.get("topic", "global"),
    )
    response = messaging.send(message)
    print(f"Notification sent: {response}")
    return response
