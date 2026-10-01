import re
from dataclasses import dataclass
from pathlib import Path


LOG_FILE = Path("/var/log/auth.log")


@dataclass
class AuthEvent:
    timestamp: str
    ip_address: str | None
    username: str | None
    status: str


FAILED_PASSWORD_PATTERN = re.compile(
    r"Failed password for (?:invalid user )?(\S+) from (\S+)"
)

ACCEPTED_PASSWORD_PATTERN = re.compile(
    r"Accepted password for (\S+) from (\S+)"
)


def parse_line(line: str) -> AuthEvent | None:
    timestamp_match = re.match(
        r"^(\S+)\s+\S+\s+\S+\[\d+\]:",
        line,
    )

    if not timestamp_match:
        return None

    timestamp = timestamp_match.group(1)

    failed_match = FAILED_PASSWORD_PATTERN.search(line)

    if failed_match:
        return AuthEvent(
            timestamp=timestamp,
            username=failed_match.group(1),
            ip_address=failed_match.group(2),
            status="failed",
        )

    accepted_match = ACCEPTED_PASSWORD_PATTERN.search(line)

    if accepted_match:
        return AuthEvent(
            timestamp=timestamp,
            username=accepted_match.group(1),
            ip_address=accepted_match.group(2),
            status="success",
        )

    return None


def parse_log(log_file: Path = LOG_FILE) -> list[AuthEvent]:
    events = []

    with log_file.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            event = parse_line(line)

            if event:
                events.append(event)

    return events


if __name__ == "__main__":
    events = parse_log()

    print(f"Parsed events: {len(events)}")

    for event in events:
        print(event)
