import json
import logging
import os
import threading
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, messaging, firestore

logger = logging.getLogger(__name__)

_watch = None
_start_lock = threading.Lock()
_started = False


def _init_firebase():
    firebase_key = os.getenv("FIREBASE_SERVICE_KEY")
    if not firebase_key:
        raise ValueError("FIREBASE_SERVICE_KEY is not set or loaded.")

    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(firebase_key))
        firebase_admin.initialize_app(cred)

    return firestore.client()


def _build_message(change_type, doc_data):
    brew_name = doc_data.get("name") or "Unknown Brew"

    if change_type == "ADDED":
        return (
            "New Brew Added!",
            f"A new brew has been added: {brew_name}",
            "added",
        )
    if change_type == "MODIFIED":
        return (
            "Brew Updated",
            f"The brew '{brew_name}' has been updated",
            "modified",
        )
    if change_type == "REMOVED":
        return (
            "Brew Removed",
            f"The brew '{brew_name}' has been removed",
            "removed",
        )
    return ("Brew Update", f"Brew '{brew_name}' changed", "unknown")


def _send_fcm_notification(title, body, event_type, doc_data):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data={
            "type": event_type,
            "brewName": doc_data.get("name") or "",
            "modifiedBy": doc_data.get("modifiedBy") or "",
        },
        topic="global",
    )
    response = messaging.send(message)
    logger.info("FCM notification sent: %s", response)


def _watch_firestore():
    client = _init_firebase()
    collection_ref = client.collection("brews")

    has_seen_initial_snapshot = False

    def on_snapshot(col_snapshot, changes, read_time):
        nonlocal has_seen_initial_snapshot
        if not has_seen_initial_snapshot:
            has_seen_initial_snapshot = True
            logger.info(
                "[BACKEND FCM] Initial snapshot received at %s. Skipping initial data (%s docs).",
                read_time,
                len(col_snapshot),
            )
            return

        for change in changes:
            doc_data = change.document.to_dict() or {}
            change_type = change.type.name

            # Firestore watcher debug details
            logger.info(
                "[BACKEND FCM] Change detected: type=%s doc_id=%s update_time=%s",
                change_type,
                change.document.id,
                getattr(change.document, "update_time", None),
            )
            logger.debug(
                "[BACKEND FCM] New data for doc_id=%s: %s",
                change.document.id,
                doc_data,
            )

            title, body, event_type = _build_message(change_type, doc_data)
            try:
                logger.info(
                    "[BACKEND FCM] Sending notification: title=%s body=%s event=%s",
                    title,
                    body,
                    event_type,
                )
                _send_fcm_notification(title, body, event_type, doc_data)
            except Exception as exc:
                logger.exception("Failed to send FCM notification: %s", exc)

    global _watch
    _watch = collection_ref.on_snapshot(on_snapshot)

    # Keep thread alive
    threading.Event().wait()


def start_firestore_watcher():
    global _started

    if os.getenv("FIRESTORE_WATCHER", "0") != "1":
        logger.info("Firestore watcher disabled. Set FIRESTORE_WATCHER=1 to enable.")
        return

    # Avoid running twice in Django autoreload
    run_main = os.getenv("RUN_MAIN")
    if run_main is not None and run_main != "true":
        return

    with _start_lock:
        if _started:
            return
        _started = True

        thread = threading.Thread(target=_watch_firestore, name="firestore-watcher")
        thread.daemon = True
        thread.start()
        logger.info("Firestore watcher started at %s", datetime.utcnow().isoformat())
