import os
import sys


def _exec_python(script_path: str) -> None:
    os.execvp(sys.executable, [sys.executable, script_path, *sys.argv[1:]])


def main() -> None:
    # Zeabur currently launches this service with `python /app/main.py`.
    # APP_MODE lets us route that single entrypoint to the desired workload.
    mode = os.getenv("APP_MODE", "api").strip().lower()

    if mode in {"api", "http", "server"}:
        _exec_python("scripts/market_api_server.py")
    if mode in {"monitor", "market-monitor"}:
        _exec_python("scripts/market_monitor.py")
    if mode in {"twitter", "twitter-monitor"}:
        _exec_python("scripts/twitter_monitor.py")

    raise SystemExit(
        f"Unsupported APP_MODE='{mode}'. "
        "Use one of: api, monitor, twitter."
    )


if __name__ == "__main__":
    main()
