import firebase_admin
import os
import json
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, messaging
# initialize loading .env
load_dotenv()
# Get Firebase service key from environment
firebase_key = os.getenv("FIREBASE_SERVICE_KEY")
print(f'Firebase key: {firebase_key}')
# Ensure the key is loaded
if not firebase_key:
    raise ValueError("FIREBASE_SERVICE_KEY is not set or loaded.")

# Parse the JSON string
cred = credentials.Certificate(json.loads(firebase_key))
firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore Listener
def firestore_listener():
    collection_ref = db.collection('brews')
    docs = collection_ref.stream()

    for doc in docs:
        # Check for condition to send a notification
        data = doc.to_dict()
        if 'notify' in data and data['notify']:
            send_notification(data)

def send_notification(data):
    message = messaging.Message(
        notification=messaging.Notification(
            title=data.get('title', 'Default Title'),
            body=data.get('body', 'Default Body'),
        ),
        topic="your-topic",
    )
    response = messaging.send(message)
    print(f"Notification sent: {response}")
