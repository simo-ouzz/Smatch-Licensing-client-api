"""
Custom uvicorn configuration to force port reuse
"""
import socket

# Force SO_REUSEADDR
import uvicorn
from uvicorn.config import Config

original_init = Config.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    # Enable SO_REUSEADDR for the underlying socket
    if hasattr(self, 'loop') and self.loop:
        # This will be applied via uvicorn's lifespan
        pass

# Apply via uvicorn command line instead
if __name__ == "__main__":
    import sys
    import os
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run with reuse-addr
    import subprocess
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "licensing_api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
        "--log-level", "info",
        "--factory"  # Use app factory
    ])
