# ============================================================
# Android Firmware Full Toolkit (AFFT) v2.0.2
# Author. soe1hom-arch / Wandi
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
    repack_dtbo,
    repack_recovery,
    repack_vbmeta,
    repack_vendor_kernel_boot,
    unpack_boot,
    unpack_init_boot,
    unpack_vendor_boot,
    unpack_dtbo,
    unpack_recovery,
    unpack_vbmeta,
    unpack_vendor_kernel_boot,
)
import modules.common as _common
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

APP_VERSION = "2.0.2"


def show_header(title: str = ""):
    """Tampilkan header box untuk submenu."""
    if title:
        # Center title in box
        padded = f" {title} "
        print(f"""{GREEN}╔══════════════════════════════════════════════╗
║{padded:^44s}║
╚══════════════════════════════════════════════╝{RESET}""")
    else:
        print(f"{GREEN}=============================={RESET}")
        print(f"{CYAN}   ANDROID FIRMWARE FULL TOOLKIT{RESET}")
        print(f"{YELLOW}   AFFT v{APP_VERSION} — Author. soe1hom-arch / Wandi{RESET}")
        print(f"{GREEN}=============================={RESET}")


def show_banner():
    """Tampilkan banner utama (hanya di menu utama)."""
    print(f"""
{GREEN}╔══════════════════════════════════════════════╗
║      {CYAN}ANDROID FIRMWARE FULL TOOLKIT{RESET}{GREEN}           ║
║      {CYAN}AFFT v{APP_VERSION}{RESET}{GREEN}                       ║
║      {YELLOW}Author .soe1hom-arch/ Wandi{RESET}{GREEN}         ║
╚══════════════════════════════════════════════╝{RESET}
""")




def menu_wizard():
    """Wizard: auto-detect files & folders, ask user what to do."""
    from modules.filesystem import unpack_filesystem, repack_filesystem
    from modules.common import safe_mkdir
    from pathlib import Path
    import shutil
    
    show_header("WIZARD MODE")
    
    # Scan locations
    scan_locations = [
        ("input/", INPUT_DIR),
        ("temp/img/", TEMP_DIR / "img"),
        ("temp/payload/", TEMP_DIR / "payload"),
        ("temp/contents/", TEMP_DIR / "contents"),
    ]
    
    print(f"{CYAN}Scanning for .img files and contents...{RESET}")
    
    all_imgs = []
    all_contents = []
    
    for label, path in scan_locations:
        if path.exists():
            for f in sorted(path.iterdir()):
                if f.is_file() and f.suffix.lower() == '.img' and f.name not in ('super.img', 'super_raw.img'):
                    all_imgs.append((label, f))
                if f.is_dir() and label == 'temp/contents/':
                    all_contents.append((label, f))
    
    print(f"\n{GREEN}[i] Found {len(all_imgs)} .img files{RESET}")
    print(f"{GREEN}[i] Found {len(all_contents)} content directories{RESET}")
    
    if _common.DEBUG:
        print(f"\n{YELLOW}[DEBUG] .img files:{RESET}")
        for label, f in all_imgs:
            print(f"  {label}{f.name}")
        print(f"{YELLOW}[DEBUG] Content dirs:{RESET}")
        for label, d in all_contents:
            print(f"  {label}{d.name}")
    
    print(f"""
{CYAN}[1]{RESET} Unpack .img files to filesystem contents
{CYAN}[2]{RESET} Repack content directories to .img files
{CYAN}[3]{RESET} Choose custom folder
{CYAN}[4]{RESET} Back
""")
    
    choice = input("Select : ").strip()
    
    if choice == "1":
        if not all_imgs:
            print(f"{RED}[X] No .img files found!{RESET}")
            input(f"{YELLOW}Press Enter...{RESET}")
            return
        
        print(f"{CYAN}Choose source:{RESET}")
        unique_sources = list(dict.fromkeys([label for label, _ in all_imgs]))
        for i, src in enumerate(unique_sources, 1):
            count = sum(1 for l, _ in all_imgs if l == src)
            print(f"  [{i}] {src} ({count} files)")
        print(f"  [{len(unique_sources)+1}] All sources")
        
        src_choice = input("\nSelect source : ").strip()
        
        if src_choice.isdigit():
            idx = int(src_choice) - 1
            if idx < len(unique_sources):
                selected_label = unique_sources[idx]
                selected_imgs = [f for l, f in all_imgs if l == selected_label]
            elif idx == len(unique_sources):
                selected_imgs = [f for _, f in all_imgs]
            else:
                print(f"{RED}[X] Invalid{RESET}")
                return
        else:
            return
        
        dest = TEMP_DIR / "contents"
        print(f"\n{YELLOW}Output: {dest}/{RESET}")
        ok = fail = 0
        for img in selected_imgs:
            r = unpack_filesystem(img, output_base=dest)
            if r.ok:
                ok += 1
                print(f"  {GREEN}[V] {img.name}{RESET}")
            else:
                fail += 1
                print(f"  {RED}[X] {img.name}: {r.message}{RESET}")
        print(f"\n{GREEN}Done: {ok} success, {fail} failed{RESET}")
        input(f"{YELLOW}Press Enter...{RESET}")
    
    elif choice == "2":
        if not all_contents:
            print(f"{RED}[X] No content directories found!{RESET}")
            input(f"{YELLOW}Press Enter...{RESET}")
            return
        
        print(f"\n{CYAN}Content directories available:{RESET}")
        for i, (_, d) in enumerate(all_contents, 1):
            print(f"  [{i}] {d.name}")
        print(f"  [A] All")
        print(f"  [C] Choose custom folder")
        
        sel = input("\nSelect : ").strip()
        
        if sel.lower() == 'a':
            selected = [d for _, d in all_contents]
        elif sel.lower() == 'c':
            custom = input("Enter folder path: ").strip()
            p = Path(custom)
            if p.exists() and p.is_dir():
                selected = [p]
            else:
                print(f"{RED}[X] Invalid path{RESET}")
                return
        elif sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(all_contents):
                selected = [all_contents[idx][1]]
            else:
                print(f"{RED}[X] Invalid{RESET}")
                return
        else:
            return
        
        out_dir = TEMP_DIR / "img"
        print(f"\n{YELLOW}Output: {out_dir}/{RESET}")
        
        ok = fail = 0
        for item in selected:
            img_name = item.name + '.img'
            output_img = TEMP_DIR / "repacking" / img_name
            output_img.parent.mkdir(parents=True, exist_ok=True)
            
            fs_result = repack_filesystem(item, output_img=output_img)
            if fs_result.ok:
                shutil.copy2(output_img, out_dir / img_name)
                output_img.unlink(missing_ok=True)
                ok += 1
                print(f"  {GREEN}[V] {img_name}{RESET}")
            else:
                fail += 1
                print(f"  {RED}[X] {img_name} gagal: {fs_result.message}{RESET}")
        print(f"\n{GREEN}Done: {ok} success, {fail} failed{RESET}")
        input(f"{YELLOW}Press Enter...{RESET}")
    
    elif choice == "3":
        custom_path = input("Enter folder path: ").strip()
        p = Path(custom_path)
        if not p.exists():
            print(f"{RED}[X] Path not found{RESET}")
            return
        
        print(f"""
{CYAN}[1]{RESET} Unpack .img files in this folder
{CYAN}[2]{RESET} Repack subdirectories to .img
{CYAN}[3]{RESET} Back
""")
        sub = input("Select : ").strip()
        
        if sub == "1":
            imgs = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() == '.img' and f.name not in ('super.img', 'super_raw.img')]
            if _common.DEBUG:
                print(f"  [DEBUG] Found {len(imgs)} .img files in {p}")
            if not imgs:
                print(f"{RED}[X] No .img files in that folder{RESET}")
                return
            dest = TEMP_DIR / "contents"
            ok = fail = 0
            for img in imgs:
                r = unpack_filesystem(img, output_base=dest)
                if r.ok:
                    ok += 1
                else:
                    fail += 1
                    print(f"  {RED}[X] {img.name}: {r.message}{RESET}")
            print(f"\n{GREEN}Done: {ok} success, {fail} failed{RESET}")
        
        elif sub == "2":
            dirs = [d for d in p.iterdir() if d.is_dir()]
            if not dirs:
                print(f"{RED}[X] No subdirectories found{RESET}")
                return
            out_dir = TEMP_DIR / "img"
            ok = fail = 0
            for item in dirs:
                img_name = item.name + '.img'
                output_img = TEMP_DIR / "repacking" / img_name
                output_img.parent.mkdir(parents=True, exist_ok=True)
                fs_result = repack_filesystem(item, output_img=output_img)
                if fs_result.ok:
                    shutil.copy2(output_img, out_dir / img_name)
                    output_img.unlink(missing_ok=True)
                    ok += 1
                else:
                    fail += 1
                    print(f"  {RED}[X] {img_name}: {fs_result.message}{RESET}")
            print(f"\n{GREEN}Done: {ok} success, {fail} failed{RESET}")
        
        input(f"{YELLOW}Press Enter...{RESET}")

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
    "lucky-arch",
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
    candidates = []
    for folder in [INPUT_DIR, TEMP_DIR / "img"]:
        if folder.exists():
            for p in folder.iterdir():
                if p.is_file() and (predicate(p) if predicate else True):
                    if p not in candidates:
                        candidates.append(p)
    candidates = sorted(set(candidates))

    if not candidates:
        print(f"\n{RED}[✗] Tidak ada file ditemukan di input/ atau temp/img/{RESET}")
        return None

    print(f"\n{CYAN}{prompt}{RESET}\n")
    for index, item in enumerate(candidates, start=1):
        size_mb = item.stat().st_size / (1024 * 1024)
        folder_label = item.parent.name
        print(f"[{index}] {item.name}  ({size_mb:.1f} MB)  [{folder_label}]")

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
    return path.name.lower() in ("boot.img", "recovery.img", "dtbo.img", "dtb.img")


def is_vendor_boot_candidate(path: Path) -> bool:
    return path.name.lower() in ("vendor_boot.img", "init_boot.img")


def is_vbmeta_candidate(path: Path) -> bool:
    return path.name.lower() in ("vbmeta.img", "vbmeta_vendor.img", "vbmeta_system.img", "vendor_kernel_boot.img")


def is_super_candidate(path: Path) -> bool:
    return path.name.lower() == "super.img"


# =========================================================
# MENU 1: PAYLOAD.BIN
# =========================================================

def menu_payload():
    show_header("EXTRACT PAYLOAD.BIN")
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
    if _common.DEBUG:
        print(f"  [DEBUG] Extracting payload.bin to {TEMP_DIR / 'payload'}")
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
        if _common.DEBUG:
            print(f"  [DEBUG] payload file: {f.name} (img={f.suffix.lower() == '.img'})")
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
    show_header("SUPER.IMG")
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
                        print(f"\n{GREEN}[✓] Extracted {len(imgs)} partitions (non-zero):{RESET}")
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
            NON_FS_PARTS = {
                "abl", "aop", "aop_config", "bluetooth", "boot", "countrycode",
                "cpucp", "cpucp_dtb", "devcfg", "dsp", "dtbo", "featenabler",
                "hyp", "idmanager", "imagefv", "init_boot", "keymaster", "modem",
                "modemfirmware", "multiimgqti", "soccp_debug", "spuservice",
                "tz", "uefi", "uefisecapp", "vbmeta", "vm-bootsys", "xbl",
                "xbl_config", "xbl_ramdump", "vbmeta_system", "vbmeta_vendor",
                "vendor_boot", "vendor_kernel_boot", "recovery",
                "qupfw", "shrm", "slim_audiop", "storage", "xm_edid", "pvmfw", "soccp_dcd",
            }


            for item in sorted(filesystem_dir.iterdir()):
                if not item.is_dir():
                    continue
                img_name = item.name + ".img"
                if _common.DEBUG:
                    print(f"  [DEBUG] Processing: {item.name} -> {img_name}")
                    print(f"  [DEBUG]   src_img={super_img_dir / img_name}, exists={(super_img_dir / img_name).exists()}")
                src_img = super_img_dir / img_name
                if not src_img.exists():
                    continue

                # Skip known non-filesystem partitions (firmware/bootloader)
                if item.name.lower() in NON_FS_PARTS:
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
    show_header("FILESYSTEM (EROFS/ext4)")
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
                    out_img = TEMP_DIR / "img" / f"{target_folder.name}_repack.img"
                    result = run_with_progress(
                        f"Repacking {target_folder.name}...",
                        lambda: repack_filesystem(target_folder, output_img=out_img)
                    )
                    print_result(result)
                    input(f"\n{YELLOW}Press Enter...{RESET}")

                elif sub == "2":
                    ok = fail = 0
                    for folder in folders:
                        out_img = TEMP_DIR / "img" / f"{folder.name}_repack.img"
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
    show_header("BOOT FAMILY")
    while True:
        print(f"""
{CYAN}[1]{RESET} Check boot family
{CYAN}[2]{RESET} Unpack boot/recovery/dtbo
{CYAN}[3]{RESET} Unpack vendor_boot/init_boot
{CYAN}[4]{RESET} Unpack vbmeta/vendor_kernel_boot
{CYAN}[5]{RESET} Repack boot/recovery/dtbo
{CYAN}[6]{RESET} Repack vendor_boot/init_boot
{CYAN}[7]{RESET} Repack vbmeta/vendor_kernel_boot
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
                name_lower = image.name.lower()
                if name_lower == "recovery.img":
                    fn = lambda: unpack_recovery(image)
                    label = "recovery.img"
                elif name_lower in ("dtbo.img", "dtb.img"):
                    fn = lambda: unpack_dtbo(image)
                    label = "dtbo.img"
                else:
                    fn = lambda: unpack_boot(image)
                    label = "boot.img"
                result = run_with_progress(f"Unpacking {label}...", fn)
                print_result(result)
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "3":
            image = choose_image("Choose vendor_boot/init_boot image:", is_vendor_boot_candidate)
            if image:
                name_lower = image.name.lower()
                if name_lower == "init_boot.img":
                    fn = lambda: unpack_init_boot(image)
                    label = "init_boot.img"
                else:
                    fn = lambda: unpack_vendor_boot(image)
                    label = "vendor_boot.img"
                result = run_with_progress(f"Unpacking {label}...", fn)
                print_result(result)
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "4":
            image = choose_image("Choose vbmeta/kernel_boot image:", is_vbmeta_candidate)
            if image:
                name_lower = image.name.lower()
                if name_lower == "vendor_kernel_boot.img":
                    fn = lambda: unpack_vendor_kernel_boot(image)
                    label = "vendor_kernel_boot.img"
                else:
                    fn = lambda: unpack_vbmeta(image)
                    label = "vbmeta.img"
                result = run_with_progress(f"Unpacking {label}...", fn)
                print_result(result)
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "5":
            print(f"""
{CYAN}[1]{RESET} Repack boot.img
{CYAN}[2]{RESET} Repack recovery.img
{CYAN}[3]{RESET} Repack dtbo.img
{CYAN}[4]{RESET} Back
""")
            sub = input("Select : ").strip()
            if sub == "1":
                result = run_with_progress("Repacking boot.img...", repack_boot)
            elif sub == "2":
                result = run_with_progress("Repacking recovery.img...", repack_recovery)
            elif sub == "3":
                result = run_with_progress("Repacking dtbo.img...", repack_dtbo)
            else:
                continue
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "6":
            print(f"""
{CYAN}[1]{RESET} Repack vendor_boot.img
{CYAN}[2]{RESET} Repack init_boot.img
{CYAN}[3]{RESET} Back
""")
            sub = input("Select : ").strip()
            if sub == "1":
                result = run_with_progress("Repacking vendor_boot.img...", repack_vendor_boot)
            elif sub == "2":
                result = run_with_progress("Repacking vendor_kernel_boot.img...", repack_vendor_kernel_boot)
            else:
                continue
            print_result(result)
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
        elif choice == "7":
            print(f"""
{CYAN}[1]{RESET} Repack vbmeta.img
{CYAN}[2]{RESET} Repack vendor_kernel_boot.img
{CYAN}[3]{RESET} Back
""")
            sub = input("Select : ").strip()
            if sub == "1":
                result = run_with_progress("Repacking vbmeta.img...", repack_vbmeta)
            elif sub == "2":
                result = run_with_progress("Repacking vendor_kernel_boot.img...", repack_vendor_kernel_boot)
            else:
                continue
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
    show_header("CLEAN OUTPUT")
    
    # Scan subfolder di TEMP_DIR
    folders = []
    if TEMP_DIR.exists():
        for item in sorted(TEMP_DIR.iterdir()):
            if item.is_dir():
                size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                size_mb = size / (1024**2)
                folders.append((item.name, item, size_mb))
    
    if not folders:
        print(f"\n{GREEN}[i] Tidak ada folder untuk dibersihkan.{RESET}")
        input(f"{YELLOW}Press Enter to continue...{RESET}")
        return
    
    print(f"\n{CYAN}Pilih folder yang ingin dibersihkan:{RESET}\n")
    for i, (name, path, size_mb) in enumerate(folders, 1):
        print(f"  [{i}] {name}/  ({size_mb:.1f} MB)")
    print(f"  [A] Bersihkan SEMUA")
    print(f"  [0] Batal")
    
    choice = input("\nSelect : ").strip()
    
    if choice.lower() == 'a':
        count = 0
        for name, path, _ in folders:
            try:
                shutil.rmtree(path)
                count += 1
            except Exception:
                pass
        for f in TEMP_DIR.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                except Exception:
                    pass
        print(f"\n{GREEN}[✓] {count} folder dibersihkan{RESET}")
    
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(folders):
            name, path, size_mb = folders[idx]
            try:
                shutil.rmtree(path)
                print(f"\n{GREEN}[✓] {name}/ dibersihkan{RESET}")
            except Exception as e:
                print(f"\n{RED}[✗] Gagal membersihkan {name}/: {e}{RESET}")
        else:
            print(f"\n{YELLOW}[i] Dibatalkan{RESET}")
    else:
        print(f"\n{YELLOW}[i] Dibatalkan{RESET}")
    
    input(f"{YELLOW}Press Enter...{RESET}")
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
{CYAN}[W]{RESET} Wizard mode - auto scan & choose action
{CYAN}[D]{RESET} Toggle debug mode (current: {'ON' if _common.DEBUG else 'OFF'})
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
    elif choice.lower() == "w":
        menu_wizard()
    elif choice.lower() == "d":
        import modules.common as _common
        _common.DEBUG = not _common.DEBUG
        status = "ON" if _common.DEBUG else "OFF"
        print(f"{GREEN}[V] Debug mode: {status}{RESET}")
        input(f"{YELLOW}Press Enter...{RESET}")
    elif choice == "6":
        print(f"\n{CYAN}Thank you for using this tool!{RESET}")
        break
    else:
        print(f"\n{RED}[✗] Invalid menu{RESET}")
        input(f"\n{YELLOW}Press Enter to try again...{RESET}")
