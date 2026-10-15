
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class BruteForceAlert:
    ip_address: str
    attempts: int
    start_time: str
    end_time: str
    severity: str


def detect_brute_force(
    events,
    threshold: int = 5,
    window_minutes: int = 5,
) -> list[BruteForceAlert]:
    failed_by_ip = defaultdict(list)

    for event in events:
        if event.status != "failed" or not event.ip_address:
            continue

        try:
            timestamp = datetime.fromisoformat(event.timestamp)
        except ValueError:
            continue

        failed_by_ip[event.ip_address].append(timestamp)

    alerts = []
    window = timedelta(minutes=window_minutes)

    for ip_address, timestamps in failed_by_ip.items():
        timestamps.sort()
        left = 0
        max_attempts = 0
        best_start = None
        best_end = None

        for right, current_time in enumerate(timestamps):
            while current_time - timestamps[left] > window:
                left += 1

            attempts = right - left + 1

            if attempts > max_attempts:
                max_attempts = attempts
                best_start = timestamps[left]
                best_end = current_time

        if max_attempts < threshold:
            continue

        if max_attempts >= 10:
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        alerts.append(
            BruteForceAlert(
                ip_address=ip_address,
                attempts=max_attempts,
                start_time=best_start.isoformat(),
                end_time=best_end.isoformat(),
                severity=severity,
            )
        )

    return alerts


if __name__ == "__main__":
    from parser import parse_log

    events = parse_log()
    alerts = detect_brute_force(events)

    print(f"Authentication events: {len(events)}")
    print(f"Brute-force alerts: {len(alerts)}")

    if not alerts:
        print("No brute-force activity detected.")

    for alert in alerts:
        print(
            f"[{alert.severity}] "
            f"IP: {alert.ip_address} | "
            f"Failed attempts: {alert.attempts} | "
            f"Period: {alert.start_time} - {alert.end_time}"
        )
