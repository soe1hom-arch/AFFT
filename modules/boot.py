# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0.2
# Author. soe1hom-arch / Wandi
# ============================================================

from pathlib import Path
import subprocess
import shutil

from .common import (
    OperationResult,
    BIN_DIR,
    INPUT_DIR,
    TEMP_DIR,
    resolve_binary,
    safe_mkdir,
)


BOOT_OUTPUT_DIR = TEMP_DIR / "boot_out"
BOOT_WORK_DIR = TEMP_DIR / "boot"


def _magiskboot():
    return resolve_binary("magiskboot")


def _clear_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def boot_family_status(input_dir: Path) -> OperationResult:
    """Cek tipe boot image yang ada di input/ dan temp/img/."""
    found = []
    scan_dirs = [input_dir]
    img_dir = input_dir.parent / "temp" / "img"
    if img_dir.exists():
        scan_dirs.append(img_dir)

    boot_keywords = (
        "boot.img", "vendor_boot.img", "init_boot.img",
        "dtbo.img", "vbmeta.img", "vbmeta_vendor.img",
        "vbmeta_system.img", "recovery.img", "dtb.img",
        "vendor_kernel_boot.img",
    )

    for folder in scan_dirs:
        for f in folder.iterdir():
            name = f.name.lower()
            if name in boot_keywords:
                size_mb = f.stat().st_size / (1024 * 1024)
                loc = folder.name
                found.append(f"{f.name} ({size_mb:.1f} MB) [{loc}]")

    if found:
        msg = "Ditemukan:\n  " + "\n  ".join(found)
    else:
        msg = "Tidak ada boot image ditemukan."

    return OperationResult(
        ok=True,
        title="Boot family status",
        message=msg,
        output_path=str(input_dir),
    )


def _unpack_boot_common(image_path: Path, out_dir: Path) -> OperationResult:
    magiskboot = _magiskboot()
    if magiskboot is None:
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message="Binary 'magiskboot' tidak ditemukan di bin/ atau PATH.",
            output_path=str(out_dir),
        )

    try:
        _clear_dir(out_dir)
        target = out_dir / image_path.name
        shutil.copy2(image_path, target)

        proc = subprocess.run(
            [str(magiskboot), "unpack", str(target)],
            cwd=str(out_dir),
            check=False,
            capture_output=True,
            text=True,
        )
        # Exit codes: 0=valid, 1=error, 2=chromeos, 3=vendor_boot
        # Code 3 = vendor_boot detected, unpack tetap berhasil
        if proc.returncode not in (0, 3):
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args,
                output=proc.stdout, stderr=proc.stderr,
            )

        # Jangan hapus file image dari work_dir — diperlukan untuk repack
        # (magiskboot repack butuh original image sebagai referensi header)

        return OperationResult(
            ok=True,
            title=f"Unpack {image_path.name}",
            message=(
                f"{image_path.name} berhasil di-unpack."
                if proc.returncode == 0
                else f"{image_path.name} berhasil di-unpack (vendor_boot detected)."
            ),
            output_path=str(out_dir),
        )

    except subprocess.CalledProcessError as exc:
        parts = [f"Command failed (exit code {exc.returncode})"]
        stderr = (exc.stderr or "").strip()
        stdout = (exc.output or "").strip()
        if stderr:
            parts.append(f"stderr: {stderr}")
        if stdout:
            parts.append(f"stdout: {stdout}")
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message=" | ".join(parts),
            output_path=str(out_dir),
        )
    except Exception as exc:
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message=f"Error tidak terduga: {exc}",
            output_path=str(out_dir),
        )


def _repack_boot_common(image_name: str, work_dir: Path) -> OperationResult:
    magiskboot = _magiskboot()
    if magiskboot is None:
        return OperationResult(
            ok=False,
            title=f"Repack {image_name}",
            message="Binary 'magiskboot' tidak ditemukan di bin/ atau PATH.",
            output_path=str(BOOT_OUTPUT_DIR),
        )

    out_dir = safe_mkdir(BOOT_OUTPUT_DIR)

    try:
        src_img = work_dir / image_name
        if not src_img.exists():
            return OperationResult(
                ok=False,
                title=f"Repack {image_name}",
                message=f"Image sumber tidak ditemukan: {src_img}\nUnpack terlebih dahulu.",
                output_path=str(BOOT_OUTPUT_DIR),
            )

        proc = subprocess.run(
            [str(magiskboot), "repack", str(src_img)],
            cwd=str(work_dir),
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args,
                output=proc.stdout, stderr=proc.stderr,
            )

        # Cari hasil repack (magiskboot menghasilkan new-boot.img)
        new_img = work_dir / "new-boot.img"
        repack_name = image_name.replace(".img", "_repack.img")
        out_path = out_dir / repack_name

        if new_img.exists():
            shutil.copy2(new_img, out_path)
            new_img.unlink()
        elif (work_dir / f"{image_name}").exists():
            # If new-boot.img not found but original still exists, repack likely in-place
            shutil.copy2(work_dir / image_name, out_path)
            print(f"  [INFO] Repack output: {out_path}")
        else:
            # Coba cari file boot lain hasil repack
            candidates = list(work_dir.glob("*.img"))
            if candidates:
                shutil.copy2(candidates[0], out_path)

        if not out_path.exists():
            return OperationResult(
                ok=False,
                title=f"Repack {image_name}",
                message=f"Output repack tidak ditemukan di {out_dir}.",
                output_path=str(BOOT_OUTPUT_DIR),
            )

        return OperationResult(
            ok=True,
            title=f"Repack {image_name}",
            message=f"{repack_name} berhasil direpack.",
            output_path=str(out_dir),
        )

    except subprocess.CalledProcessError as exc:
        parts = [f"Command failed (exit code {exc.returncode})"]
        stderr = (exc.stderr or "").strip()
        stdout = (exc.output or "").strip()
        if stderr:
            parts.append(f"stderr: {stderr}")
        if stdout:
            parts.append(f"stdout: {stdout}")
        return OperationResult(
            ok=False,
            title=f"Repack {image_name}",
            message=" | ".join(parts),
            output_path=str(out_dir),
        )
    except Exception as exc:
        return OperationResult(
            ok=False,
            title=f"Repack {image_name}",
            message=f"Error tidak terduga: {exc}",
            output_path=str(out_dir),
        )


def unpack_boot(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "boot")


def unpack_vendor_boot(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "vendor_boot")


def unpack_init_boot(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "init_boot")


def unpack_dtbo(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "dtbo")


def unpack_recovery(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "recovery")


def unpack_vbmeta(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "vbmeta")


def unpack_vendor_kernel_boot(image_path: Path) -> OperationResult:
    return _unpack_boot_common(image_path, BOOT_WORK_DIR / "vendor_kernel_boot")


def repack_boot():
    return _repack_boot_common("boot.img", BOOT_WORK_DIR / "boot")


def repack_vendor_boot():
    return _repack_boot_common("vendor_boot.img", BOOT_WORK_DIR / "vendor_boot")


def repack_init_boot():
    return _repack_boot_common("init_boot.img", BOOT_WORK_DIR / "init_boot")


def repack_dtbo():
    return _repack_boot_common("dtbo.img", BOOT_WORK_DIR / "dtbo")


def repack_recovery():
    return _repack_boot_common("recovery.img", BOOT_WORK_DIR / "recovery")


def repack_vbmeta():
    return _repack_boot_common("vbmeta.img", BOOT_WORK_DIR / "vbmeta")


def repack_vendor_kernel_boot():
    return _repack_boot_common("vendor_kernel_boot.img", BOOT_WORK_DIR / "vendor_kernel_boot")
