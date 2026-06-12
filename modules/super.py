# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0.1
# Author. soe1hom-arch / Wandi
# ============================================================

import sys
from pathlib import Path
import shutil
import subprocess

from .common import OperationResult, TEMP_DIR, resolve_binary, safe_mkdir
from . import common
from .filesystem import unpack_filesystem
from .validate import is_sparse_image


SUPER_WORK_DIR = TEMP_DIR / "img_src"
SUPER_OUTPUT_DIR = TEMP_DIR / "img"
SUPER_REPACK_DIR = TEMP_DIR / "repacked"


def _lpunpack():
    return resolve_binary("lpunpack")


def _simg2img():
    return resolve_binary("simg2img")


def _clear_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_super_results(work_dir: Path, out_dir: Path):
    copied = []
    for item in work_dir.iterdir():
        if item.is_file() and item.suffix.lower() == ".img" and item.stat().st_size > 0            and item.name not in {"super.img", "super_raw.img"}:
            target = out_dir / item.name
            shutil.copy2(item, target)
            copied.append(item.name)
    return copied


def _write_super_readme(out_dir: Path, items: list[str]):
    lines = [
        "Partition images from super.img unpack",
        "",
        "This folder contains copied partition images for easier browsing.",
        "",
    ]
    if items:
        lines.append("Extracted partitions:")
        for item in items:
            lines.append(f"- {item}")
    else:
        lines.append("No partition images were copied to the output folder.")

    (out_dir / "README.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _partition_images(scan_dir: Path):
    """Cari file .img partisi (kecuali super.img / super_raw.img) di scan_dir."""
    partitions = []
    for item in sorted(scan_dir.iterdir()):
        if item.is_file() and item.suffix.lower() == ".img" \
           and item.name not in {"super.img", "super_raw.img"} \
           and item.stat().st_size > 0:
            partitions.append(item)
    return partitions


def _format_proc_error(exc: subprocess.CalledProcessError) -> str:
    parts = [f"Command failed (exit code {exc.returncode})"]
    stderr = (exc.stderr or "").strip()
    stdout = (exc.output or "").strip()
    if stderr:
        parts.append(f"stderr: {stderr}")
    if stdout:
        parts.append(f"stdout: {stdout}")
    if not stderr and not stdout:
        parts.append("(tidak ada output dari proses)")
    return " | ".join(parts)


def unpack_super(image_path: Path) -> OperationResult:
    work_dir = SUPER_WORK_DIR
    out_dir = SUPER_OUTPUT_DIR

    lpunpack = _lpunpack()
    simg2img = _simg2img()

    if lpunpack is None:
        return OperationResult(
            ok=False,
            title="Unpack super.img",
            message="Binary 'lpunpack' tidak ditemukan di bin/ atau PATH.",
            output_path="",
        )
    if simg2img is None:
        return OperationResult(
            ok=False,
            title="Unpack super.img",
            message="Binary 'simg2img' tidak ditemukan di bin/ atau PATH.",
            output_path="",
        )

    try:
        _clear_dir(work_dir)
        safe_mkdir(out_dir)

        source_img = work_dir / image_path.name
        shutil.copy2(image_path, source_img)

        raw_img = source_img
        sparse = is_sparse_image(source_img)

        if sparse:
            print(f"  [INFO] Terdeteksi sparse image, mengonversi dengan simg2img...")
            raw_img = work_dir / "super_raw.img"
            convert = subprocess.run(
                [str(simg2img), str(source_img), str(raw_img)],
                cwd=str(work_dir),
                check=False,
                capture_output=True,
                text=True,
            )
            if convert.returncode != 0:
                raise subprocess.CalledProcessError(
                    convert.returncode, convert.args,
                    output=convert.stdout, stderr=convert.stderr,
                )
            print(f"  [INFO] Konversi sparse selesai: {raw_img.name}")
        else:
            print(f"  [INFO] Bukan sparse image, langsung unpack...")

        if common.DEBUG:
            print(f"  [DEBUG] lpunpack {raw_img.name} -> {work_dir}")
        print(f"  [INFO] Menjalankan lpunpack pada {raw_img.name}...")
        unpack = subprocess.run(
            [str(lpunpack), str(raw_img), str(work_dir)],
            cwd=str(work_dir),
            check=False,
            capture_output=True,
            text=True,
        )
        if unpack.returncode != 0:
            raise subprocess.CalledProcessError(
                unpack.returncode, unpack.args,
                output=unpack.stdout, stderr=unpack.stderr,
            )

        copied = _copy_super_results(work_dir, out_dir)
        _write_super_readme(out_dir, copied)

        # Hapus image partisi dari temp/ supaya tidak duplikat (hemat storage)
        for item in list(work_dir.iterdir()):
            if item.is_file() and item.suffix.lower() == ".img" \
               and item.name not in {"super.img", "super_raw.img"} \
           and item.stat().st_size > 0:
                item.unlink()

        if not copied:
            return OperationResult(
                ok=False,
                title="Unpack super.img",
                message=(
                    "lpunpack selesai tapi tidak ada partisi .img yang dihasilkan. "
                    "Kemungkinan super.img rusak, format tidak didukung, atau lpunpack versi lama. "
                    f"stdout: {unpack.stdout.strip() or '(kosong)'} | "
                    f"stderr: {unpack.stderr.strip() or '(kosong)'}"
                ),
                output_path=str(out_dir),
            )

        return OperationResult(
            ok=True,
            title="Unpack super.img",
            message=f"super.img berhasil di-unpack. Partisi: {', '.join(copied)}",
            output_path=str(out_dir),
        )

    except subprocess.CalledProcessError as exc:
        return OperationResult(
            ok=False,
            title="Unpack super.img",
            message=_format_proc_error(exc),
            output_path=str(out_dir),
        )
    except Exception as exc:
        return OperationResult(
            ok=False,
            title="Unpack super.img",
            message=f"Error tidak terduga: {exc}",
            output_path=str(out_dir),
        )


def unpack_super_with_contents(image_path: Path) -> OperationResult:
    """Unpack super.img, lalu extract filesystem dari setiap partisi.
    
    Membaca partisi dari TEMP_DIR/img/ (hasil unpack)
    karena unpack_super() sudah membersihkan temp/.
    """
    base_result = unpack_super(image_path)
    if not base_result.ok:
        return base_result

    super_dir = Path(base_result.output_path)  # temp/img/
    contents_dir = TEMP_DIR / "contents"
    safe_mkdir(contents_dir)

    # Baca partisi dari temp/img/ (unified .img storage)
    partitions = _partition_images(super_dir)
    if not partitions:
        return OperationResult(
            ok=False,
            title="Unpack super.img + contents",
            message="super.img berhasil di-unpack tapi tidak ada partisi untuk diekstrak lebih lanjut.",
            output_path=str(super_dir),
        )

    extracted = []
    for img in partitions:
        print(f"  [INFO] Mengekstrak filesystem: {img.name}...")
        fs_result = unpack_filesystem(img, output_base=contents_dir)
        if fs_result.ok:
            extracted.append(f"{img.name} -> {fs_result.output_path}")
        else:
            extracted.append(f"{img.name} -> GAGAL: {fs_result.message}")

    readme = contents_dir / "README.txt"
    existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
    extra = "\n".join(f"- {line}" for line in extracted) + "\n"
    readme.write_text(existing + extra, encoding="utf-8")

    ok_count = sum(1 for line in extracted if "GAGAL" not in line)
    return OperationResult(
        ok=True,
        title="Unpack super.img + contents",
        message=f"super.img dan filesystem dalam berhasil diekstrak. ({ok_count}/{len(extracted)} partisi sukses)",
        output_path=str(super_dir),
    )


def repack_super(work_dir: Path | None = None) -> OperationResult:
    """Repack super.img dari partisi .img di work_dir.
    
    Default: baca dari TEMP_DIR/img/ (hasil unpack).
    """
    safe_mkdir(SUPER_REPACK_DIR)
    if work_dir is None:
        work_dir = SUPER_OUTPUT_DIR

    lpmake = resolve_binary("lpmake")
    if lpmake is None:
        return OperationResult(
            ok=False,
            title="Repack super.img",
            message="Binary 'lpmake' tidak ditemukan di bin/ atau PATH.",
            output_path=str(SUPER_REPACK_DIR),
        )

    partitions = _partition_images(work_dir)
    if not partitions:
        return OperationResult(
            ok=False,
            title="Repack super.img",
            message=f"Tidak ada partisi .img ditemukan di {work_dir}.",
            output_path=str(SUPER_REPACK_DIR),
        )

    try:
        output_img = SUPER_REPACK_DIR / "super_repack.img"

        cmd = [str(lpmake)]
        cmd.extend(["--device-size=auto"])
        cmd.extend(["--metadata-size=65536"])
        cmd.extend(["--metadata-slots=3"])
        cmd.extend(["--super-name=super"])
        cmd.append("--sparse")

        groups = {}
        for p in partitions:
            name = p.stem
            if name.endswith("_a"):
                group = "group_a"
            elif name.endswith("_b"):
                group = "group_b"
            else:
                group = "default"
            groups.setdefault(group, []).append((name, p))

        for group_name, parts in sorted(groups.items()):
            group_size = sum(p.stat().st_size for _, p in parts)
            if group_size == 0:
                continue
            cmd.append(f"--group={group_name}:{group_size}")

        for group_name, parts in sorted(groups.items()):
            group_size = sum(p.stat().st_size for _, p in parts)
            if group_size == 0:
                continue
            for name, p in parts:
                size = p.stat().st_size
                if size == 0:
                    continue
                cmd.append(f"--partition={name}:readonly:{size}:{group_name}")
                cmd.append(f"--image={name}={p}")

        cmd.append(f"--output={output_img}")
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args,
                output=proc.stdout, stderr=proc.stderr,
            )

        if not output_img.exists():
            return OperationResult(
                ok=False,
                title="Repack super.img",
                message="lpmake selesai tapi super.img tidak ditemukan.",
                output_path=str(SUPER_REPACK_DIR),
            )

        size_gb = output_img.stat().st_size / (1024**3)
        return OperationResult(
            ok=True,
            title="Repack super.img",
            message=f"super.img berhasil direpack dengan {len(partitions)} partisi. ({size_gb:.2f} GB)",
            output_path=str(SUPER_REPACK_DIR),
        )

    except subprocess.CalledProcessError as exc:
        return OperationResult(
            ok=False,
            title="Repack super.img",
            message=_format_proc_error(exc),
            output_path=str(SUPER_REPACK_DIR),
        )
    except Exception as exc:
        return OperationResult(
            ok=False,
            title="Repack super.img",
            message=f"Error tidak terduga: {exc}",
            output_path=str(SUPER_REPACK_DIR),
        )
