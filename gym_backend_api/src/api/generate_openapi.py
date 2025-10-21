import json
import os

from src.api.main import app

"""
Generates a fresh OpenAPI schema JSON after all routers are registered.
"""

def generate():
    schema = app.openapi()
    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    return output_path


if __name__ == "__main__":
    path = generate()
    print(f"OpenAPI schema written to {path}")
