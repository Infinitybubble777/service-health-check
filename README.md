# Service Health Check

A Python command-line tool for checking a small set of HTTP endpoints. It reports response codes, elapsed time and connection errors, and returns an exit code a scheduled check can use to detect failures.

## Run the local demo

Use Python 3.10 or newer. The tool uses the standard library.

From the repository directory, start a local demo service in one terminal.

```sh
python -m http.server 8000 --bind 127.0.0.1 --directory demo
```

In a second terminal, run the check.

```sh
python healthcheck.py checks.example.json
```

Expect a line like `UP   Local demo health endpoint: HTTP 200 (12 ms)`. Stop the demo server and rerun the command to see a connection failure. Add `--json` for machine-readable output or `--timeout 1` to adjust the socket timeout.

To monitor your own services, create a JSON list with a `name`, an HTTP(S) `url` and an optional `expected_status` for each check. The default status is 200. Standard HTTP redirects are followed. The elapsed time measures the request through receipt of response headers. This check does not read the response body.

| Exit code | Meaning |
| --- | --- |
| 0 | All checks returned the expected HTTP status |
| 1 | At least one service returned an unexpected status or could not be reached |
| 2 | Invalid command options or configuration |

AI-assisted portfolio demo with a synthetic local endpoint.
