import firebase_admin
import os
from firebase_admin import credentials, firestore, messaging

cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_KEY"))
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