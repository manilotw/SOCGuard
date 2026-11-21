from parser import parse_log
from detector import detect_brute_force
from database import init_db, save_events, save_alerts


def main():
    print("SOCGuard Authentication Monitoring System")
    print("-" * 45)

    init_db()

    events = parse_log()
    print(f"Authentication events found: {len(events)}")

    saved_events = save_events(events)
    print(f"New events saved: {saved_events}")

    alerts = detect_brute_force(events)
    print(f"Brute-force alerts detected: {len(alerts)}")

    saved_alerts = save_alerts(alerts)
    print(f"New alerts saved: {saved_alerts}")

    if alerts:
        print("\nSECURITY ALERTS:")
        for alert in alerts:
            print(
                f"[{alert.severity}] "
                f"IP: {alert.ip_address} | "
                f"Failed attempts: {alert.attempts} | "
                f"Period: {alert.start_time} - {alert.end_time}"
            )
    else:
        print("\nNo brute-force activity detected.")

    print("\nSOCGuard monitoring completed.")


if __name__ == "__main__":
    main()
