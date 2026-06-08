# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0
# By. soe1hom-arch / Wandi
# ============================================================
# Tool ini dilindungi hak cipta. Dilarang menghapus atau
# mengubah kredit penulis tanpa izin.
# ============================================================

import os
import shutil
import subprocess
import stat
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = BASE_DIR / "bin"
INPUT_DIR = BASE_DIR / "input"
# OUTPUT_DIR = BASE_DIR / "output"  # (deprecated - all output now in TEMP_DIR)
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"
RUNTIME_BIN_DIR = Path.home()


def ensure_workspace():
    for path in (BIN_DIR, INPUT_DIR, TEMP_DIR, LOGS_DIR, RUNTIME_BIN_DIR):
        path.mkdir(parents=True, exist_ok=True)


def safe_mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def binary_path(name: str) -> Path:
    return BIN_DIR / name


def binary_exists(name: str) -> bool:
    return resolve_binary(name) is not None


def _copy_binary_safe(src: Path, dst: Path) -> bool:
    """Copy binary dari src ke dst dengan fallback method.
    Returns True jika sukses, False jika gagal.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    # Method 1: shutil.copy2
    try:
        shutil.copy2(src, dst)
        dst.chmod(0o755)
        return True
    except OSError:
        pass
    
    # Method 2: shutil.copy (tanpa metadata)
    try:
        shutil.copy(src, dst)
        dst.chmod(0o755)
        return True
    except OSError:
        pass
    
    # Method 3: subprocess cp
    try:
        subprocess.run(
            ["cp", str(src), str(dst)],
            check=True, capture_output=True, timeout=10
        )
        dst.chmod(0o755)
        return True
    except Exception:
        pass
    
    # Method 4: baca & tulis manual
    try:
        with open(src, "rb") as f_src:
            data = f_src.read()
        with open(dst, "wb") as f_dst:
            f_dst.write(data)
        dst.chmod(0o755)
        return True
    except Exception:
        pass
    
    return False


def resolve_binary(name: str):
    """Cari binary — cocok dengan pola main.py asli.
    
    1. Cek PATH ($PREFIX/bin) — binary Termux / system
    2. Cek $HOME/<name> — hasil copy langsung ke home
    3. Cek bin/<name> (lokal) → copy ke $HOME/<name>
    
    NEVER return path di external storage (noexec)!
    """
    # 1. Cek PATH dulu (system binary, pkg install)
    system = shutil.which(name)
    if system:
        return Path(system)

    # 2. Cek $HOME/<name> (hasil copy sebelumnya, sesuai pola asli)
    runtime = RUNTIME_BIN_DIR / name
    if runtime.exists():
        try:
            if os.name != 'nt':
                subprocess.run(["chmod", "+x", str(runtime)],
                             capture_output=True, timeout=5)
        except Exception:
            pass
        return runtime

    # 3. Coba copy dari bin/ lokal ke $HOME/ (sesuai pola main.py asli)
    local = binary_path(name)
    if local.exists():
        try:
            if runtime.exists():
                runtime.unlink()
            shutil.copy2(local, runtime)
            subprocess.run(["chmod", "+x", str(runtime)],
                         capture_output=True, timeout=5)
            return runtime
        except Exception as e:
            print(f"  [WARN] Gagal copy {name}: {e}")
            print(f"         Coba manual: cp {local} {runtime} && chmod +x {runtime}")

    return None


def run_checked(cmd, cwd: Path | None = None):
    return subprocess.run(
        [str(part) for part in cmd],
        cwd=str(cwd) if cwd else None,
        check=True,
        capture_output=True,
        text=True,
    )


def first_existing(*paths):
    for item in paths:
        path = Path(item)
        if path.exists():
            return path
    return None


@dataclass
class OperationResult:
    ok: bool
    title: str
    message: str
    output_path: str = ""


def format_result(result: OperationResult) -> str:
    status = "OK" if result.ok else "FAIL"
    extra = f" -> {result.output_path}" if result.output_path else ""
    return f"[{status}] {result.title}: {result.message}{extra}"
