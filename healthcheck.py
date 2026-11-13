"""Check the HTTP status of services listed in a JSON file."""

import argparse
import json
import math
from pathlib import Path
import sys
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def read_checks(path):
    checks = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(checks, list) or not checks:
        raise ValueError("Configuration must be a nonempty list of checks.")

    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            raise ValueError(f"Check {index} must be an object.")
        name = check.get("name")
        url = check.get("url")
        expected_status = check.get("expected_status", 200)
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Check {index} needs a nonempty name.")
        if not isinstance(url, str):
            raise ValueError(f"{name}: url must be a string.")
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError(f"{name}: url must be an HTTP or HTTPS address.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError(f"{name}: credentials in URLs are unsupported.")
        if parsed.port == 0:
            raise ValueError(f"{name}: port must be greater than zero.")
        if type(expected_status) is not int or not 200 <= expected_status <= 599:
            raise ValueError(f"{name}: expected_status must be an integer from 200 to 599.")
    return checks


def check_service(check, timeout):
    expected_status = check.get("expected_status", 200)
    status = None
    detail = None
    started_at = perf_counter()
    try:
        with urlopen(check["url"], timeout=timeout) as response:
            status = response.status
    except HTTPError as error:
        with error:
            status = error.code
    except (URLError, OSError, ValueError) as error:
        detail = str(error)

    healthy = status == expected_status
    if detail is None and not healthy:
        detail = f"Expected HTTP {expected_status}, got {status}"

    return {
        "name": check["name"],
        "healthy": healthy,
        "status": status,
        "expected_status": expected_status,
        "elapsed_ms": round((perf_counter() - started_at) * 1000),
        "detail": detail,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON file containing checks")
    parser.add_argument("--timeout", type=float, default=3, help="socket timeout in seconds (default: 3)")
    parser.add_argument("--json", action="store_true", help="output a JSON report")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    try:
        checks = read_checks(args.config)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    results = [check_service(check, args.timeout) for check in checks]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            label = "UP" if result["healthy"] else "FAIL"
            response = f'HTTP {result["status"]}' if result["healthy"] else result["detail"]
            print(f'{label:<4} {result["name"]}: {response} ({result["elapsed_ms"]} ms)')
    return 0 if all(result["healthy"] for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
