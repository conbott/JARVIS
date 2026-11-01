import platform
import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_system_hardware() -> Dict[str, Any]:
    """
    Dynamically detects the host hardware (NVIDIA GPU, Apple Silicon, or CPU)
    so the application works seamlessly on any user machine.
    """
    # 1. Check for NVIDIA GPU via nvidia-smi
    try:
        res = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            encoding="utf-8",
            timeout=2.0
        )
        lines = res.strip().split("\n")
        if lines and lines[0]:
            parts = [p.strip() for p in lines[0].split(",")]
            gpu_name = parts[0]
            vram_mb = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            vram_gb = round(vram_mb / 1024, 1)
            display = f"{gpu_name} ({vram_gb}GB)" if vram_gb else gpu_name
            return {
                "device_name": display,
                "device_type": "NVIDIA GPU",
                "is_gpu": True,
                "vram_gb": vram_gb
            }
    except Exception:
        pass

    # 2. Check for Apple Silicon (macOS)
    if platform.system() == "Darwin":
        try:
            brand = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], encoding="utf-8").strip()
            if "Apple" in brand:
                return {
                    "device_name": f"{brand} (Metal/MPS)",
                    "device_type": "Apple Silicon",
                    "is_gpu": True,
                    "vram_gb": None
                }
        except Exception:
            pass

    # 3. Fallback to CPU architecture
    cpu_model = platform.processor() or platform.machine()
    return {
        "device_name": f"CPU ({cpu_model})",
        "device_type": "CPU",
        "is_gpu": False,
        "vram_gb": None
    }

system_hardware = get_system_hardware()
