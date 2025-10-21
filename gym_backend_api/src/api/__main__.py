"""
Entrypoint for running the FastAPI app with uvicorn using module execution:
python -m src.api

Resolves to uvicorn import path "src.api.main:app" and binds to 0.0.0.0 on the configured port (API_PORT, default 3001).
"""

import os
import uvicorn


def main() -> None:
    # PUBLIC_INTERFACE
    """Run uvicorn for the Gym Management API.

    Reads:
    - API_PORT: port to bind (default 3001)

    Binds:
    - host: 0.0.0.0 (so container exposes the port)
    """
    port = int(os.getenv("API_PORT", "3001"))
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
