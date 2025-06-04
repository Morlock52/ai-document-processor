#!/usr/bin/env python3
"""
Cross-platform port availability checker for Document Processor
"""

import argparse
import os
import socket
import sys
from datetime import datetime

# Default ports
DEFAULT_PORTS = {
    "FRONTEND_PORT": 3000,
    "BACKEND_PORT": 8000,
    "POSTGRES_PORT": 5432,
    "REDIS_PORT": 6379,
    "NGINX_PORT": 80,
}

# ANSI color codes
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def check_port(port: int) -> bool:
    """Return True if the given port is free on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            return result != 0
    except Exception:
        return False


def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """Return the next available port starting from ``start_port``."""
    port = start_port
    attempts = 0

    while attempts < max_attempts:
        if check_port(port):
            return port
        port += 1
        attempts += 1

        if port > 65535:
            port = start_port + 1000

    raise RuntimeError(f"No available port found after {max_attempts} attempts")


def main() -> int:
    """Entry point for the port checker script."""

    parser = argparse.ArgumentParser(
        description="Check and assign free ports for the Document Processor"
    )
    for key, default in DEFAULT_PORTS.items():
        parser.add_argument(
            f"--{key.lower()}",
            type=int,
            default=default,
            help=f"Default {key}",
        )

    args = parser.parse_args()
    port_config = {k: getattr(args, k.lower()) for k in DEFAULT_PORTS.keys()}

    print("Checking port availability for Document Processor...")
    print("=" * 50)

    assigned_ports = {}

    for service, default_port in port_config.items():
        if check_port(default_port):
            print(f"{GREEN}✓{NC} {service} port {default_port} is available")
            assigned_ports[service] = default_port
        else:
            print(f"{YELLOW}!{NC} {service} port {default_port} is in use")
            try:
                new_port = find_available_port(default_port)
                print(f"{GREEN}✓{NC} Using alternative {service}: {new_port}")
                assigned_ports[service] = new_port
            except Exception as e:
                print(f"{RED}✗{NC} Failed to find alternative port for {service}: {e}")
                sys.exit(1)

    # Generate .env.ports file
    env_content = f"""# Auto-generated port configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Service ports
FRONTEND_PORT={assigned_ports['FRONTEND_PORT']}
BACKEND_PORT={assigned_ports['BACKEND_PORT']}
POSTGRES_PORT={assigned_ports['POSTGRES_PORT']}
REDIS_PORT={assigned_ports['REDIS_PORT']}
NGINX_PORT={assigned_ports['NGINX_PORT']}

# URLs with dynamic ports
NEXT_PUBLIC_API_URL=http://localhost:{assigned_ports['BACKEND_PORT']}/api/v1
DATABASE_URL=postgresql://docuser:docpass@localhost:{assigned_ports['POSTGRES_PORT']}/docprocessor
REDIS_URL=redis://localhost:{assigned_ports['REDIS_PORT']}
"""

    with open(".env.ports", "w") as f:
        f.write(env_content)

    print("\nPort configuration saved to .env.ports")
    print("=" * 50)
    print(f"Frontend URL: http://localhost:{assigned_ports['FRONTEND_PORT']}")
    print(f"Backend URL: http://localhost:{assigned_ports['BACKEND_PORT']}")
    print(f"API Docs: http://localhost:{assigned_ports['BACKEND_PORT']}/docs")
    print("=" * 50)

    # Set environment variables for current session
    for key, value in assigned_ports.items():
        os.environ[key] = str(value)

    return 0


if __name__ == "__main__":
    sys.exit(main())
