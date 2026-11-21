import os
import hashlib
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()


def get_es_client():
    return Elasticsearch(
        os.getenv("ELASTICSEARCH_URL"),
        basic_auth=(
            os.getenv("ELASTICSEARCH_USERNAME"),
            os.getenv("ELASTICSEARCH_PASSWORD"),
        ),
        ca_certs=os.getenv("ELASTICSEARCH_CA_CERT"),
        request_timeout=10,
    )


def check_connection():
    client = get_es_client()
    return client.ping()


def index_alert(alert):
    client = get_es_client()

    alert_id = hashlib.sha256(
        f"{alert.ip_address}|{alert.start_time}|{alert.end_time}|{alert.severity}".encode()
    ).hexdigest()

    document = {
        "@timestamp": alert.end_time,
        "event": {
            "kind": "alert",
            "category": ["intrusion_detection"],
            "type": ["indicator"],
            "action": "brute_force_detected",
            "severity": 3 if alert.severity == "HIGH" else 2,
            "outcome": "success",
        },
        "source": {
            "ip": alert.ip_address,
        },
        "socguard": {
            "attempts": alert.attempts,
            "severity": alert.severity,
            "start_time": alert.start_time,
            "end_time": alert.end_time,
        },
        "message": (
            f"Brute-force detected from {alert.ip_address}: "
            f"{alert.attempts} failed login attempts"
        ),
    }

    return client.index(
        index="socguard-alerts",
        id=alert_id,
        document=document,
    )


if __name__ == "__main__":
    try:
        if check_connection():
            print("Connected to Elasticsearch successfully!")
        else:
            print("Could not connect to Elasticsearch.")
    except Exception as error:
        print(f"Elasticsearch connection error: {error}")
