# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0.1
# Author. soe1hom-arch / Wandi
# ============================================================

import os
from pathlib import Path
import shutil
import subprocess

from .common import OperationResult, TEMP_DIR, resolve_binary, safe_mkdir
from .validate import is_sparse_image, detect_fs_type, raw_to_sparse


FILESYSTEM_OUTPUT_DIR = TEMP_DIR / "contents"
FILESYSTEM_REPACK_DIR = TEMP_DIR / "img"
FILESYSTEM_WORK_DIR = TEMP_DIR / "filesystem_work"


def _extract_erofs():
    return resolve_binary("extract.erofs")


def _debugfs():
    return resolve_binary("debugfs")


def _clear_dir(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write_readme(out_dir: Path, image_name: str, fs_kind: str):
    text = (
        f"Filesystem unpack result: {image_name}\n\n"
        f"Detected filesystem: {fs_kind}\n"
        "Files in this folder were extracted for easier browsing.\n"
    )
    (out_dir / "README.txt").write_text(text, encoding="utf-8")


def _format_proc_error(exc: subprocess.CalledProcessError) -> str:
    parts = [f"Command failed (exit code {exc.returncode})"]
    stderr = (exc.stderr or "").strip()
    stdout = (exc.output or "").strip()
    # Deteksi SIGSYS (exit -31) — binary crash karena system call diblokir
    if exc.returncode == -31:
        parts.append("Binary crash (SIGSYS). Coba: pkg install erofs-utils (utk mkfs.erofs)")
    if stderr:
        parts.append(f"stderr: {stderr}")
    if stdout:
        parts.append(f"stdout: {stdout}")
    if not stderr and not stdout and exc.returncode != -31:
        parts.append("(tidak ada output dari proses)")
    return " | ".join(parts)


def unpack_filesystem(image_path: Path, output_base: Path | None = None) -> OperationResult:
    out_dir = safe_mkdir((output_base or FILESYSTEM_OUTPUT_DIR) / image_path.stem)

    erofs = _extract_erofs()
    debugfs = _debugfs()

    if erofs is None:
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message="Binary 'extract.erofs' tidak ditemukan di bin/ atau PATH.",
            output_path=str(out_dir),
        )
    if debugfs is None:
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message="Binary 'debugfs' tidak ditemukan di bin/ atau PATH.",
            output_path=str(out_dir),
        )

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        source_img = image_path

        if is_sparse_image(source_img):
            print(f"  [INFO] Terdeteksi sparse image, mengonversi dengan simg2img...")
            simg2img = resolve_binary("simg2img")
            if simg2img is None:
                return OperationResult(
                    ok=False,
                    title=f"Unpack {image_path.name}",
                    message="Binary 'simg2img' tidak ditemukan di bin/ atau PATH.",
                    output_path=str(out_dir),
                )
            raw_img = TEMP_DIR / f"{source_img.stem}_raw.img"
            if raw_img.exists():
                raw_img.unlink()
            convert = subprocess.run(
                [str(simg2img), str(source_img), str(raw_img)],
                check=False, capture_output=True, text=True,
            )
            if convert.returncode != 0:
                return OperationResult(
                    ok=False,
                    title=f"Unpack {image_path.name}",
                    message=f"Gagal konversi sparse: {convert.stderr.strip() or 'unknown error'}",
                    output_path=str(out_dir),
                )
            print(f"  [INFO] Konversi sparse selesai: {raw_img.name}")
            source_img = raw_img

        fs_kind = detect_fs_type(source_img)
        if fs_kind == "unknown":
            name = image_path.name.lower()
            erofs_keywords = ("system", "vendor", "product", "system_ext",
                              "vendor_dlkm", "system_dlkm", "mi_ext", "odm", "cust",
                              "my_product", "my_company", "my_preload", "my_region",
                              "my_stock", "oplus_product", "oplus_company",
                              "oplus_engineer", "oplus_vendor", "exclusive",
                              "prism", "optics", "opconfig", "preload", "dalvik")
            fs_kind = "erofs" if any(k in name for k in erofs_keywords) else "ext4"
            print(f"  [WARN] Magic bytes tidak dikenal, tebak dari nama: {fs_kind}")

        print(f"  [INFO] Filesystem terdeteksi: {fs_kind} untuk {image_path.name}")

        if fs_kind == "erofs":
            proc = subprocess.run(
                [str(erofs), "-i", str(source_img), "-x", "-o", str(out_dir)],
                cwd=str(out_dir),
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            ext4_root = out_dir / "ext4_extract"
            ext4_root.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [str(debugfs), "-R", f"rdump / {ext4_root}", str(source_img)],
                cwd=str(out_dir),
                check=False,
                capture_output=True,
                text=True,
            )

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args,
                output=proc.stdout, stderr=proc.stderr,
            )

        _write_readme(out_dir, image_path.name, fs_kind)
        return OperationResult(
            ok=True,
            title=f"Unpack {image_path.name}",
            message=f"{image_path.name} berhasil diekstrak sebagai {fs_kind}.",
            output_path=str(out_dir),
        )

    except subprocess.CalledProcessError as exc:
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message=_format_proc_error(exc),
            output_path=str(out_dir),
        )
    except Exception as exc:
        return OperationResult(
            ok=False,
            title=f"Unpack {image_path.name}",
            message=f"Error tidak terduga: {exc}",
            output_path=str(out_dir),
        )


def _find_ref_image(name: str) -> Path | None:
    """Cari referensi image untuk deteksi tipe filesystem.
    Cek di output/super/ dulu, lalu temp/super/."""
    for base in (TEMP_DIR / "img", TEMP_DIR / "img_src"):
        candidate = base / f"{name}.img"
        if candidate.exists():
            return candidate
    return None


def repack_filesystem(work_dir: Path, output_img: Path | None = None) -> OperationResult:
    safe_mkdir(FILESYSTEM_REPACK_DIR)

    if not work_dir.exists() or not work_dir.is_dir():
        return OperationResult(
            ok=False,
            title=f"Repack {work_dir.name}",
            message=f"Folder tidak ditemukan: {work_dir}",
            output_path=str(FILESYSTEM_REPACK_DIR),
        )

    if output_img is None:
        output_img = FILESYSTEM_REPACK_DIR / f"{work_dir.name}.img"
    output_img.parent.mkdir(parents=True, exist_ok=True)

    def _get_termux_env() -> dict:
        """Dapatkan environment dengan LD_LIBRARY_PATH untuk binary Termux.
        
        Binary yang dicopy dari $PREFIX/bin/ ke $HOME/ kehilangan
        library path-nya. Solusi: set LD_LIBRARY_PATH ke $PREFIX/lib/
        """
        env = os.environ.copy()
        prefix = env.get('PREFIX', '/data/data/com.termux/files/usr')
        lib_path = f"{prefix}/lib"
        current_ld = env.get('LD_LIBRARY_PATH', '')
        if lib_path not in current_ld:
            if current_ld:
                env['LD_LIBRARY_PATH'] = f"{lib_path}:{current_ld}"
            else:
                env['LD_LIBRARY_PATH'] = lib_path
        return env

    def _binary_from_home(bin_path: Path) -> bool:
        """Cek apakah binary ada di $HOME/ (hasil copy dari bin/).
        
        Binary yang di-copy dari bin/ ke $HOME/ kehilangan rpath,
        perlu LD_LIBRARY_PATH tambahan.
        """
        home = Path.home()
        return str(bin_path).startswith(str(home))

    # Cari referensi image untuk deteksi tipe filesystem
    ref_img = _find_ref_image(work_dir.name)
    fs_kind = "unknown"
    if ref_img and ref_img.exists():
        if is_sparse_image(ref_img):
            # Kalau sparse, skip magic detection, fallback ke keyword
            print(f"  [WARN] {ref_img.name} adalah sparse image, fallback deteksi dari nama")
        else:
            fs_kind = detect_fs_type(ref_img)

    if fs_kind == "unknown":
        keywords = ("system", "vendor", "product", "system_ext",
                    "vendor_dlkm", "system_dlkm", "mi_ext", "odm", "cust",
                    "my_product", "my_company", "my_preload", "my_region",
                    "my_stock", "oplus_product", "oplus_company",
                    "oplus_engineer", "oplus_vendor", "exclusive",
                    "prism", "optics", "opconfig", "preload", "dalvik")
        fs_kind = "erofs" if any(k in work_dir.name.lower() for k in keywords) else "ext4"
        print(f"  [WARN] Magic bytes tidak dikenal, tebak dari nama: {fs_kind}")

    # Deteksi apakah mkfs binary perlu env Termux (setelah fs_kind diketahui)
    _termux_env = _get_termux_env()
    _needs_termux_env = False
    if fs_kind == "erofs":
        _mkfs_check = resolve_binary("mkfs.erofs")
        if _mkfs_check and _binary_from_home(_mkfs_check):
            _needs_termux_env = True
    else:
        _mkfs_check = resolve_binary("make_ext4fs") or resolve_binary("mkfs.ext4")
        if _mkfs_check and _binary_from_home(_mkfs_check):
            _needs_termux_env = True

    try:
        # Hapus output_img dulu kalau sudah ada (mkfs.erofs & make_ext4fs nge-refuse overwrite)
        if output_img.exists():
            output_img.unlink()

        if fs_kind == "erofs":
            mkfs = resolve_binary("mkfs.erofs")
            if mkfs is None:
                return OperationResult(
                    ok=False,
                    title=f"Repack {work_dir.name}",
                    message="Binary 'mkfs.erofs' tidak ditemukan di bin/ atau PATH.",
                    output_path=str(FILESYSTEM_REPACK_DIR),
                )
            # Default compression (lz4), -z lz4hc bisa ditambah manual
            cmd = [str(mkfs), str(output_img), str(work_dir)]
        else:
            mkfs = resolve_binary("make_ext4fs") or resolve_binary("mkfs.ext4")
            if mkfs is None:
                return OperationResult(
                    ok=False,
                    title=f"Repack {work_dir.name}",
                    message="Binary 'make_ext4fs'/'mkfs.ext4' tidak ditemukan di bin/ atau PATH.",
                    output_path=str(FILESYSTEM_REPACK_DIR),
                )

            ref_size = 0
            if ref_img and ref_img.exists():
                ref_size = ref_img.stat().st_size
            if ref_size == 0:
                total = sum(f.stat().st_size for f in work_dir.rglob("*") if f.is_file())
                ref_size = int(total * 1.15) + (1024 * 1024)

            if "make_ext4fs" in str(mkfs):
                cmd = [str(mkfs), "-s", "-l", str(ref_size), "-a", work_dir.name,
                       str(output_img), str(work_dir)]
            else:
                cmd = [str(mkfs), "-F", str(ref_size), str(output_img), str(work_dir)]

        proc = subprocess.run(cmd, check=False, capture_output=True, text=True,
                              env=_termux_env if _needs_termux_env else None)
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args,
                output=proc.stdout, stderr=proc.stderr,
            )

        if not output_img.exists():
            return OperationResult(
                ok=False,
                title=f"Repack {work_dir.name}",
                message=f"Proses selesai tapi {output_img.name} tidak ditemukan.",
                output_path=str(FILESYSTEM_REPACK_DIR),
            )

        # Konversi raw -> sparse (kecuali make_ext4fs -s yg sudah sparse)
        if fs_kind == "erofs" or ("mkfs.ext4" in str(mkfs)):
            print(f"  [INFO] Mengonversi raw -> sparse: {output_img.name}")
            sparse_path = output_img.with_suffix(".sparse.img")
            ok = raw_to_sparse(output_img, sparse_path)
            if ok:
                # Ganti output_img dengan sparse version
                output_img.unlink()
                sparse_path.rename(output_img)
                print(f"  [INFO] Konversi sparse selesai")
            else:
                print(f"  [WARN] Konversi sparse gagal, tetap menggunakan raw")

        size_mb = output_img.stat().st_size / (1024**2)
        return OperationResult(
            ok=True,
            title=f"Repack {work_dir.name}",
            message=f"{work_dir.name} berhasil direpack sebagai {fs_kind}. ({size_mb:.1f} MB)",
            output_path=str(output_img),
        )

    except subprocess.CalledProcessError as exc:
        return OperationResult(
            ok=False,
            title=f"Repack {work_dir.name}",
            message=_format_proc_error(exc),
            output_path=str(FILESYSTEM_REPACK_DIR),
        )
    except Exception as exc:
        return OperationResult(
            ok=False,
            title=f"Repack {work_dir.name}",
            message=f"Error tidak terduga: {exc}",
            output_path=str(FILESYSTEM_REPACK_DIR),
        )
