# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0
# By. soe1hom-arch / Wandi
# ============================================================

import os
import shutil
import subprocess
import time
import threading
from pathlib import Path

from modules.boot import (
    boot_family_status,
    repack_boot,
    repack_init_boot,
    repack_vendor_boot,
    unpack_boot,
    unpack_init_boot,
    unpack_vendor_boot,
)
from modules.common import INPUT_DIR, TEMP_DIR, ensure_workspace, resolve_binary
from modules.super import repack_super, unpack_super, unpack_super_with_contents


# =========================================================
# COLORS
# =========================================================

RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

# =========================================================
# BANNER
# =========================================================

APP_VERSION = "2.0"


def show_header():
    """Tampilkan header sederhana untuk submenu."""
    print(f"{GREEN}=============================={RESET}")
    print(f"{CYAN}   ANDROID FIRMWARE TOOLKIT{RESET}")
    print(f"{YELLOW}   AFFT v{APP_VERSION} — By. soe1hom-arch / Wandi{RESET}")
    print(f"{GREEN}=============================={RESET}")


def show_banner():
    """Tampilkan banner utama (hanya di menu utama)."""
    print(f"""
{GREEN}╔══════════════════════════════════════════════╗
║        {CYAN}ANDROID FIRMWARE TOOLKIT{RESET}{GREEN}           ║
║        {CYAN}AFFT v{APP_VERSION}{RESET}{GREEN}                       ║
║        {YELLOW}By. soe1hom-arch / Wandi{RESET}{GREEN}         ║
╚══════════════════════════════════════════════╝{RESET}
""")


# =========================================================
# PREPARE WORKSPACE & BINARIES
# =========================================================

ensure_workspace()
show_banner()

print(f"{YELLOW}[•] Preparing binaries...{RESET}\n")

# Mengikuti pola main.py asli: copy dari bin/ ke HOME/, chmod +x
from modules.common import binary_path, RUNTIME_BIN_DIR, shutil, subprocess

BINARY_NAMES = [
    "payload-dumper-go",
    "lpunpack",
    "lpmake",
    "simg2img",
    "extract.erofs",
    "debugfs",
    "magiskboot",
    "mkfs.erofs",
    "make_ext4fs",
]

# Cek PATH dulu (binary system / pkg install)
for name in BINARY_NAMES:
    sysbin = shutil.which(name)
    if sysbin:
        print(f"{GREEN}[✓] {name} ready (system){RESET}")
        continue

    # Copy dari bin/ ke HOME/ (pola asli main.py)
    source = binary_path(name)
    target = RUNTIME_BIN_DIR / name
    if source.exists():
        try:
            if target.exists():
                target.unlink()
            shutil.copy2(source, target)
            subprocess.run(["chmod", "+x", str(target)],
                         capture_output=True, timeout=5)
            print(f"{GREEN}[✓] {name} ready (from bin/){RESET}")
        except Exception as e:
            print(f"{YELLOW}[!] Gagal install {name}: {e}{RESET}")
    else:
        print(f"{YELLOW}[!] Missing binary: {name}{RESET}")

# =========================================================
# ANIMATED PROGRESS
# =========================================================


def animated_progress(process, text):
    spinner = ["|", "/", "-", "\\"]
    i = 0
    percent = 0
    while process.poll() is None:
        if percent < 95:
            percent += 1
        print(f"\r{CYAN}[{percent}%] [{spinner[i % 4]}] {text}{RESET}", end="", flush=True)
        i += 1
        time.sleep(0.2)
    print(f"\r{GREEN}[100%] [✓] {text}{RESET}                    ")


def run_with_progress(text: str, fn):
    """Jalankan fungsi modules di thread terpisah sambil tampilkan spinner."""
    result_box = [None]
    spinner = ["|", "/", "-", "\\"]
    done = threading.Event()

    def worker():
        result_box[0] = fn()
        done.set()

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    i = 0
    percent = 0
    while not done.is_set():
        if percent < 95:
            percent += 1
        print(f"\r{CYAN}[{percent}%] [{spinner[i % 4]}] {text}{RESET}", end="", flush=True)
        i += 1
        time.sleep(0.2)

    t.join()
    result = result_box[0]
    if result.ok:
        print(f"\r{GREEN}[100%] [✓] {text}{RESET}                    ")
    else:
        print(f"\r{RED}[  0%] [✗] {text}{RESET}                    ")
    return result


def print_result(result):
    if result.ok:
        print(f"\n{GREEN}[✓] {result.title}: {result.message}{RESET}")
    else:
        print(f"\n{RED}[✗] {result.title}: {result.message}{RESET}")
    if result.output_path:
        print(f"Output : {result.output_path}")

# =========================================================
# CHOOSE IMAGE HELPER
# =========================================================


def choose_image(prompt: str, predicate=None) -> Path | None:
    candidates = sorted(
        [p for p in INPUT_DIR.iterdir() if p.is_file() and (predicate(p) if predicate else True)]
    )
    if not candidates:
        print(f"\n{RED}[✗] Tidak ada file ditemukan di input/{RESET}")
        return None

    print(f"\n{CYAN}{prompt}{RESET}\n")
    for index, item in enumerate(candidates, start=1):
        size_mb = item.stat().st_size / (1024 * 1024)
        print(f"[{index}] {item.name}  ({size_mb:.1f} MB)")

    try:
        choice = int(input("\nSelect file : ").strip())
        if 1 <= choice <= len(candidates):
            return candidates[choice - 1]
        print(f"{RED}[✗] Pilihan di luar jangkauan.{RESET}")
        return None
    except Exception:
        print(f"{RED}[✗] Input tidak valid.{RESET}")
        return None


def is_boot_candidate(path: Path) -> bool:
    return path.name.lower() == "boot.img"


def is_vendor_boot_candidate(path: Path) -> bool:
    return path.name.lower() == "vendor_boot.img"


def is_init_boot_candidate(path: Path) -> bool:
    return path.name.lower() == "init_boot.img"


def is_super_candidate(path: Path) -> bool:
    return path.name.lower() == "super.img"


# =========================================================
# MENU 1: PAYLOAD.BIN
# =========================================================

def menu_payload():
    show_header()
    payload_file = INPUT_DIR / "payload.bin"

    if not payload_file.exists():
        print(f"\n{RED}[✗] payload.bin not found in 'input' folder!{RESET}")
        input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        return

    tool = resolve_binary("payload-dumper-go")
    if tool is None:
        print(f"\n{RED}[✗] payload-dumper-go not found in bin/{RESET}")
        input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        return

    print(f"\n{GREEN}[✓] payload.bin detected{RESET}")
    process = subprocess.Popen(
        [str(tool), "-o", str(TEMP_DIR / "payload"), str(payload_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    animated_progress(process, "Extracting payload.bin...")
    print(f"Output : {TEMP_DIR / 'payload'}")
    # Copy .img files ke temp/img/ untuk dipakai menu lain
    payload_dir = TEMP_DIR / "payload"
    img_dir = TEMP_DIR / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    img_count = 0
    for f in payload_dir.iterdir():
        if f.is_file() and f.suffix.lower() == ".img":
            target = img_dir / f.name
            if not target.exists():
                shutil.copy2(f, target)
                img_count += 1
    if img_count > 0:
        print(f"{GREEN}[✓] {img_count} .img files copied to temp/img/ (ready for repack){RESET}")
    input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")


# =========================================================
# MENU 2: SUPER.IMG
# =========================================================

def menu_super():
    show_header()
    while True:
        print(f"""
{CYAN}[1]{RESET} Unpack super.img only
{CYAN}[2]{RESET} Unpack super.img + extract filesystem
{CYAN}[3]{RESET} Repack super.img only
{CYAN}[4]{RESET} Repack all filesystem (contents → .img)
{CYAN}[5]{RESET} Back
""")
        choice = input("Select Menu : ").strip()

        if choice == "1":
            image = choose_image("Choose super image:", is_super_candidate)
            if image:
                print(f"\n{GREEN}[✓] super.img detected ({image.stat().st_size / (1024**2):.1f} MB){RESET}")
                result = run_with_progress("Unpacking super.img...", lambda: unpack_super(image))
                print_result(result)
                if result.ok:
                    out = Path(result.output_path)
                    imgs = sorted([f.name for f in out.iterdir()
                                   if f.is_file() and f.suffix == ".img"
                                   and f.name not in {"super.img", "super_raw.img"} \
                                   and f.stat().st_size > 0])
                    if imgs:
                        print(f"\n{GREEN}[✓] Extracted {len(imgs)} partitions:{RESET}")
                        for name in imgs:
                            print(f"  \u2022 {name}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

        elif choice == "2":
            image = choose_image("Choose super image:", is_super_candidate)
            if image:
                print(f"\n{GREEN}[✓] super.img detected ({image.stat().st_size / (1024**2):.1f} MB){RESET}")

                print(f"\n{YELLOW}[•] Step 1/2 — Unpacking super.img{RESET}")
                base_result = run_with_progress("Unpacking super.img...", lambda: unpack_super(image))
                if not base_result.ok:
                    print_result(base_result)
                    input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                    continue

                out = Path(base_result.output_path)
                imgs = sorted([f for f in out.iterdir() if f.is_file() and f.suffix == ".img"
                               and f.name not in {"super.img", "super_raw.img"} \
                                   and f.stat().st_size > 0])
                print(f"{GREEN}[✓] Found {len(imgs)} partitions: {', '.join(f.name for f in imgs)}{RESET}")

                print(f"\n{YELLOW}[•] Step 2/2 — Extracting filesystem{RESET}")
                from modules.filesystem import unpack_filesystem
                contents_dir = TEMP_DIR / "contents"
                contents_dir.mkdir(parents=True, exist_ok=True)

                ok_count = 0
                fail_count = 0
                for img in imgs:
                    fs_result = run_with_progress(
                        f"Extracting {img.name}...",
                        lambda i=img: unpack_filesystem(i, output_base=contents_dir)
                    )
                    if fs_result.ok:
                        ok_count += 1
                    else:
                        fail_count += 1
                        print(f"  {RED}\u2192 {img.name}: {fs_result.message}{RESET}")

                print(f"\n{GREEN}[✓] Done! {ok_count} success{RESET}" +
                      (f", {RED}{fail_count} failed{RESET}" if fail_count else ""))
                print(f"Output : {out}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

        elif choice == "3":
            result = run_with_progress("Repacking super.img...", repack_super)
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

        elif choice == "4":
            # Repack all filesystem contents -> .img (reverse dari option 2)
            filesystem_dir = TEMP_DIR / "contents"
            super_img_dir = TEMP_DIR / "img"

            if not filesystem_dir.exists() or not any(filesystem_dir.iterdir()):
                print(f"\n{RED}[✗] Tidak ada filesystem contents ditemukan.{RESET}")
                print(f"{YELLOW}  Unpack super.img + extract filesystem dulu (menu [2] \u2192 [2]).{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            if not super_img_dir.exists():
                print(f"\n{RED}[✗] No partition images found in temp/img/!{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            # Step 1/2: Repack filesystem contents -> .img
            print(f"\n{YELLOW}[•] Step 1/1 — Repacking all filesystem contents into images{RESET}")
            from modules.filesystem import repack_filesystem

            ok_count = 0
            for item in sorted(filesystem_dir.iterdir()):
                if not item.is_dir():
                    continue
                img_name = item.name + ".img"
                src_img = super_img_dir / img_name
                if not src_img.exists():
                    continue

                temp_img = TEMP_DIR / "repacking" / img_name
                temp_img.parent.mkdir(parents=True, exist_ok=True)
                fs_result = repack_filesystem(item, output_img=temp_img)
                if fs_result.ok:
                    shutil.copy2(temp_img, src_img)
                    temp_img.unlink(missing_ok=True)
                    ok_count += 1
                else:
                    print(f"  {RED}\u2192 {img_name} gagal: {fs_result.message}{RESET}")
                temp_img.unlink(missing_ok=True)

            if ok_count > 0:
                print(f"  {GREEN}[✓] {ok_count} filesystem berhasil direpack{RESET}")
            else:
                print(f"{RED}[✗] Semua filesystem gagal direpack, abort.{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            # Hasil: .img files sudah diperbarui di super_out/ untuk repack super.img
            print(f"{GREEN}[✓] Semua filesystem berhasil direpack. .img ada di super_out/{RESET}")
            print(f"{YELLOW}  Gunakan menu [3] untuk repack super.img{RESET}")
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

        elif choice == "5":
            break
        else:
            print(f"\n{RED}[✗] Invalid menu{RESET}")
            input(f"\n{YELLOW}Press Enter to try again...{RESET}")


# =========================================================
# MENU 3: FILESYSTEM IMG
# =========================================================

def menu_filesystem():
    show_header()
    while True:
        print(f"""
{CYAN}[1]{RESET} Extract filesystem IMG (from input/)
{CYAN}[2]{RESET} Repack filesystem IMG (from temp/contents/)
{CYAN}[3]{RESET} Back
""")
        choice = input("Select Menu : ").strip()

        # =========== EXTRACT ===========
        if choice == "1":
            from modules.filesystem import unpack_filesystem
            candidates = sorted(
                [p for p in INPUT_DIR.iterdir()
                 if p.is_file() and p.suffix.lower() == ".img"
                 and p.name not in ("super.img", "payload.bin", "super_raw.img")]
            )
            # Also cari dari temp/img/ (hasil unpack super.img / payload)
            img_dir = TEMP_DIR / "img"
            if img_dir.exists():
                for p in img_dir.iterdir():
                    if p.is_file() and p.suffix.lower() == ".img"                        and p.name not in ("super.img", "payload.bin", "super_raw.img")                        and p not in candidates:
                        candidates.append(p)
                candidates = sorted(set(candidates))
            if not candidates:
                print(f"\n{RED}[✗] No filesystem IMG found!{RESET}")
                print(f"{YELLOW}  Letakkan .img di input/ atau extract dari super.img dulu.{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            while True:
                print(f"""
{CYAN}[1]{RESET} Extract single image
{CYAN}[2]{RESET} Extract ALL images
{CYAN}[3]{RESET} Back
""")
                sub = input("Select : ").strip()

                if sub == "1":
                    print(f"\n{CYAN}Choose filesystem image:{RESET}\n")
                    for idx, img in enumerate(candidates, 1):
                        size_mb = img.stat().st_size / (1024 * 1024)
                        print(f"[{idx}] {img.name}  ({size_mb:.1f} MB)")
                    try:
                        sel = int(input("\nSelect file : ").strip())
                        if 1 <= sel <= len(candidates):
                            chosen = candidates[sel - 1]
                        else:
                            print(f"{RED}[✗] Pilihan di luar jangkauan.{RESET}")
                            input(f"\n{YELLOW}Press Enter...{RESET}")
                            continue
                    except Exception:
                        print(f"{RED}[✗] Input tidak valid.{RESET}")
                        input(f"\n{YELLOW}Press Enter...{RESET}")
                        continue
                    result = run_with_progress(
                        f"Extracting {chosen.name}...",
                        lambda: unpack_filesystem(chosen)
                    )
                    print_result(result)
                    input(f"\n{YELLOW}Press Enter...{RESET}")

                elif sub == "2":
                    ok = fail = 0
                    for img in candidates:
                        r = run_with_progress(
                            f"Extracting {img.name}...",
                            lambda i=img: unpack_filesystem(i)
                        )
                        if r.ok:
                            ok += 1
                        else:
                            fail += 1
                            print(f"  {RED}\u2192 {img.name}: {r.message}{RESET}")
                    print(f"\n{GREEN}[✓] Done: {ok} success{RESET}" +
                          (f", {RED}{fail} failed{RESET}" if fail else ""))
                    input(f"\n{YELLOW}Press Enter...{RESET}")

                elif sub == "3":
                    break
                else:
                    print(f"{RED}[✗] Invalid{RESET}")

        # =========== REPACK ===========
        elif choice == "2":
            from modules.filesystem import repack_filesystem
            fs_root = TEMP_DIR / "contents"
            if not fs_root.exists():
                print(f"\n{RED}[✗] Folder temp/contents/ tidak ditemukan!{RESET}")
                print(f"{YELLOW}  Extract filesystem terlebih dahulu (menu [2] \u2192 [2] atau menu [3] \u2192 [1]).{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            folders = sorted([d for d in fs_root.iterdir() if d.is_dir()])
            if not folders:
                print(f"\n{RED}[✗] Tidak ada folder hasil extract di temp/contents/!{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            while True:
                print(f"""
{CYAN}[1]{RESET} Repack single folder
{CYAN}[2]{RESET} Repack ALL folders
{CYAN}[3]{RESET} Back
""")
                sub = input("Select : ").strip()

                if sub == "1":
                    print(f"\n{CYAN}Choose folder to repack:{RESET}\n")
                    for idx, folder in enumerate(folders, 1):
                        size_mb = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file()) / (1024 * 1024)
                        print(f"[{idx}] {folder.name}  ({size_mb:.1f} MB)")
                    try:
                        sel = int(input("\nSelect folder : ").strip())
                        if 1 <= sel <= len(folders):
                            target_folder = folders[sel - 1]
                        else:
                            print(f"{RED}[✗] Pilihan di luar jangkauan.{RESET}")
                            input(f"\n{YELLOW}Press Enter...{RESET}")
                            continue
                    except Exception:
                        print(f"{RED}[✗] Input tidak valid.{RESET}")
                        input(f"\n{YELLOW}Press Enter...{RESET}")
                        continue

                    print(f"\n{GREEN}[✓] Selected : {target_folder.name}{RESET}")
                    out_img = TEMP_DIR / "img" / f"{target_folder.name}.img"
                    result = run_with_progress(
                        f"Repacking {target_folder.name}...",
                        lambda: repack_filesystem(target_folder, output_img=out_img)
                    )
                    print_result(result)
                    input(f"\n{YELLOW}Press Enter...{RESET}")

                elif sub == "2":
                    ok = fail = 0
                    for folder in folders:
                        out_img = TEMP_DIR / "img" / f"{folder.name}.img"
                        r = run_with_progress(
                            f"Repacking {folder.name}...",
                            lambda f=folder, o=out_img: repack_filesystem(f, output_img=o)
                        )
                        if r.ok:
                            ok += 1
                        else:
                            fail += 1
                            print(f"  {RED}\u2192 {folder.name}: {r.message}{RESET}")
                    print(f"\n{GREEN}[✓] Done: {ok} success{RESET}" +
                          (f", {RED}{fail} failed{RESET}" if fail else ""))
                    input(f"\n{YELLOW}Press Enter...{RESET}")

                elif sub == "3":
                    break
                else:
                    print(f"{RED}[✗] Invalid{RESET}")

        elif choice == "3":
            break
        else:
            print(f"\n{RED}[✗] Invalid menu{RESET}")
            input(f"\n{YELLOW}Press Enter to try again...{RESET}")


# =========================================================
# MENU 4: BOOT FAMILY
# =========================================================

def menu_boot():
    show_header()
    while True:
        print(f"""
{CYAN}[1]{RESET} Check boot family
{CYAN}[2]{RESET} Unpack boot.img
{CYAN}[3]{RESET} Unpack vendor_boot.img
{CYAN}[4]{RESET} Unpack init_boot.img
{CYAN}[5]{RESET} Repack boot.img
{CYAN}[6]{RESET} Repack vendor_boot.img
{CYAN}[7]{RESET} Repack init_boot.img
{CYAN}[8]{RESET} Back
""")
        choice = input("Select Menu : ").strip()

        if choice == "1":
            from modules.boot import boot_family_status
            result = boot_family_status(INPUT_DIR)
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "2":
            image = choose_image("Choose boot image:", is_boot_candidate)
            if image:
                result = run_with_progress("Unpacking boot.img...", lambda: unpack_boot(image))
                print_result(result)
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "3":
            image = choose_image("Choose vendor_boot image:", is_vendor_boot_candidate)
            if image:
                result = run_with_progress("Unpacking vendor_boot.img...", lambda: unpack_vendor_boot(image))
                print_result(result)
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "4":
            image = choose_image("Choose init_boot image:", is_init_boot_candidate)
            if image:
                result = run_with_progress("Unpacking init_boot.img...", lambda: unpack_init_boot(image))
                print_result(result)
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "5":
            result = run_with_progress("Repacking boot.img...", repack_boot)
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "6":
            result = run_with_progress("Repacking vendor_boot.img...", repack_vendor_boot)
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "7":
            result = run_with_progress("Repacking init_boot.img...", repack_init_boot)
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "8":
            break
        else:
            print(f"\n{RED}[✗] Invalid menu{RESET}")
            input(f"\n{YELLOW}Press Enter to try again...{RESET}")


# =========================================================
# MENU 5: CLEAN OUTPUT
# =========================================================

def menu_clean():
    show_header()
    for folder in [TEMP_DIR]:
        if folder.exists():
            for item in folder.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)
                except Exception:
                    pass
    print(f"\n{GREEN}[✓] Output cleaned{RESET}")
    input(f"\n{YELLOW}Press Enter to continue...{RESET}")


# =========================================================
# MAIN LOOP
# =========================================================

while True:
    show_banner()
    print(f"""
{CYAN}[1]{RESET} Extract payload.bin
{CYAN}[2]{RESET} Unpack super.img
{CYAN}[3]{RESET} Extract filesystem IMG
{CYAN}[4]{RESET} Boot family (unpack/repack)
{CYAN}[5]{RESET} Clean output
{CYAN}[6]{RESET} Exit
""")

    choice = input("Select Menu : ").strip()

    if choice == "1":
        menu_payload()
    elif choice == "2":
        menu_super()
    elif choice == "3":
        menu_filesystem()
    elif choice == "4":
        menu_boot()
    elif choice == "5":
        menu_clean()
    elif choice == "6":
        print(f"\n{CYAN}Thank you for using this tool!{RESET}")
        break
    else:
        print(f"\n{RED}[✗] Invalid menu{RESET}")
        input(f"\n{YELLOW}Press Enter to try again...{RESET}")
