import os
import shutil
import subprocess
import time

# =========================================================
# PATH
# =========================================================

HOME = os.path.expanduser("~")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# =========================================================
# COLORS
# =========================================================

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# =========================================================
# CREATE FOLDERS
# =========================================================

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# =========================================================
# =========================================================
# BINARIES (Hanya yang dipakai saja)
# =========================================================

BINARIES = {
    "payload-dumper-go": os.path.join(BIN_DIR, "payload-dumper-go"),
    "lpunpack":          os.path.join(BIN_DIR, "lpunpack"),
    "simg2img":          os.path.join(BIN_DIR, "simg2img"),
    "extract.erofs":     os.path.join(BIN_DIR, "extract.erofs"),
    "debugfs":           os.path.join(BIN_DIR, "debugfs"),
}

INSTALLED_BIN = {}

# =========================================================
# HEADER
# =========================================================

print(f"""
{CYAN}
╔══════════════════════════════════════════════╗
║         ANDROID FIRMWARE TOOLKIT            ║
║        By. soe1hom-arch / Wandi             ║
╚══════════════════════════════════════════════╝
{RESET}
""")

# =========================================================
# INSTALL BINARIES
# =========================================================

print(f"{YELLOW}[•] Preparing binaries...{RESET}\n")

for name, source in BINARIES.items():
    target = os.path.join(HOME, name)
    if not os.path.exists(source):
        print(f"{YELLOW}[!] Missing binary: {name}{RESET}")
        continue

    try:
        if os.path.exists(target):
            try:
                os.remove(target)
            except:
                pass

        shutil.copy2(source, target)
        subprocess.run(
            ["chmod", "+x", target],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        INSTALLED_BIN[name] = target
        print(f"{GREEN}[✓] {name} ready{RESET}")
    except Exception as e:
        print(f"{RED}[✗] Failed install {name}{RESET}")
        print(e)

if len(INSTALLED_BIN) == 0:
    print(
        f"{YELLOW}[!] Source-only build detected: helper binaries are not bundled in this repository.{RESET}"
    )
    print(
        f"{YELLOW}[!] Place compatible binaries in the 'bin/' folder before running extraction tasks.{RESET}\n"
    )

# =========================================================
# CLEAN OUTPUT
# =========================================================

def clean_output():
    for folder in [OUTPUT_DIR, TEMP_DIR]:
        if os.path.exists(folder):
            for item in os.listdir(folder):
                path = os.path.join(folder, item)
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                except:
                    pass

# =========================================================
# CHECK SPARSE
# =========================================================

def is_sparse(path):
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
        return magic == b'\x3A\xFF\x26\xED'
    except:
        return False

# =========================================================
# PROGRESS ANIMATION
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

# =========================================================
# LOOP UTAMA TOOLS
# =========================================================

while True:
    print(f"""
{CYAN}[1]{RESET} Extract payload.bin
{CYAN}[2]{RESET} Unpack super.img
{CYAN}[3]{RESET} Extract filesystem IMG
{CYAN}[4]{RESET} Clean output
{CYAN}[5]{RESET} Exit
""")

    choice = input("Select Menu : ")

    # =========================================================
    # MENU 4: CLEAN OUTPUT
    # =========================================================
    if choice == "4":
        clean_output()
        print(f"\n{GREEN}[✓] Output cleaned{RESET}")
        input(f"\n{YELLOW}Press Enter to continue...{RESET}")

    # =========================================================
    # MENU 5: EXIT
    # =========================================================
    elif choice == "5":
        print(f"\n{CYAN}Thank you for using this tool!{RESET}")
        break  # Keluar dari loop while, otomatis menutup script

    # =========================================================
    # MENU 1: PAYLOAD.BIN
    # =========================================================
    elif choice == "1":
        payload_file = os.path.join(INPUT_DIR, "payload.bin")

        if not os.path.exists(payload_file):
            print(f"\n{RED}[✗] payload.bin not found in 'input' folder!{RESET}")
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
            continue # Kembali ke awal menu tanpa menutup program

        print(f"\n{GREEN}[✓] payload.bin detected{RESET}")
        process = subprocess.Popen(
            [INSTALLED_BIN["payload-dumper-go"], "-o", OUTPUT_DIR, payload_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        animated_progress(process, "Extracting payload.bin...")
        print(f"Output : {OUTPUT_DIR}")
        input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

    # =========================================================
    # MENU 2: SUPER.IMG
    # =========================================================
    elif choice == "2":
        super_file = os.path.join(INPUT_DIR, "super.img")

        if not os.path.exists(super_file):
            print(f"\n{RED}[✗] super.img not found in 'input' folder!{RESET}")
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
            continue

        print(f"\n{GREEN}[✓] super.img detected{RESET}")

        if is_sparse(super_file):
            print(f"{YELLOW}[*] Sparse super.img detected{RESET}")

            raw_super = os.path.join(
                TEMP_DIR,
                "super_raw.img"
            )

            convert = subprocess.run(
                [
                    INSTALLED_BIN["simg2img"],
                    super_file,
                    raw_super
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if convert.returncode != 0:
                print(f"\n{RED}[✗] Failed converting super.img{RESET}")
                input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
                continue

            super_file = raw_super
            print(f"{GREEN}[✓] Converted to raw super.img{RESET}")

        process = subprocess.Popen(
            [
                INSTALLED_BIN["lpunpack"],
                super_file,
                OUTPUT_DIR
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        animated_progress(process, "Unpacking super.img...")
        process.wait()

        extracted = [
            f for f in os.listdir(OUTPUT_DIR)
            if f.endswith(".img")
        ]

        if len(extracted) == 0:
            print(f"\n{RED}[✗] No partition extracted{RESET}")
        else:
            print(f"\n{GREEN}[✓] Extracted {len(extracted)} partitions{RESET}")

        try:
            raw_super = os.path.join(TEMP_DIR, "super_raw.img")
            if os.path.exists(raw_super):
                os.remove(raw_super)
        except:
            pass

        print(f"Output : {OUTPUT_DIR}")
        input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

    # =========================================================
    # MENU 3: FILESYSTEM IMG
    # =========================================================
    elif choice == "3":
        filesystem_keywords = ["system", "vendor", "product", "odm", "system_ext", "mi_ext", "vendor_dlkm", "system_dlkm", "cust"]
        img_files = []

        for file in os.listdir(INPUT_DIR):
            if file.endswith(".img") and file != "super.img":
                lower = file.lower()
                for keyword in filesystem_keywords:
                    if keyword in lower:
                        img_files.append(file)
                        break

        if len(img_files) == 0:
            print(f"\n{RED}[✗] No filesystem IMG found in 'input' folder!{RESET}")
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
            continue

        print(f"\n{CYAN}Available Filesystem IMG:{RESET}\n")
        for index, file in enumerate(img_files):
            print(f"[{index + 1}] {file}")

        try:
            select = int(input("\nSelect IMG : "))
            target_img = os.path.join(INPUT_DIR, img_files[select - 1])
        except:
            print(f"\n{RED}[✗] Invalid selection{RESET}")
            input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")
            continue

        img_name = os.path.basename(target_img).replace(".img", "")
        img_output = os.path.join(OUTPUT_DIR, img_name)
        os.makedirs(img_output, exist_ok=True)

        print(f"\n{GREEN}[✓] Selected : {img_name}.img{RESET}")

        # --- SPARSE CHECK ---
        if is_sparse(target_img):
            print(f"{YELLOW}[*] Sparse image detected{RESET}")
            raw_img = os.path.join(TEMP_DIR, f"{img_name}_raw.img")
            subprocess.run(
                [INSTALLED_BIN["simg2img"], target_img, raw_img],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            target_img = raw_img
            print(f"{GREEN}[✓] Sparse converted{RESET}")

        # --- EROFS PARTITIONS CHECK ---
        erofs_partitions = ["system", "system_ext", "system_dlkm", "vendor", "vendor_dlkm", "product", "mi_ext", "odm", "cust"]
        force_erofs = False
        for part in erofs_partitions:
            if part in img_name.lower():
                force_erofs = True
                break

        # --- EXTRACTION ---
        if force_erofs:
            print(f"{GREEN}[✓] Using EROFS extraction{RESET}")
            process = subprocess.Popen(
                [INSTALLED_BIN["extract.erofs"], "-i", target_img, "-x", "-o", img_output],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            animated_progress(process, f"Extracting {img_name}.img...")
        else:
            print(f"{GREEN}[✓] Using EXT4 extraction{RESET}")
            ext4_output = os.path.join(img_output, "ext4_extract")
            os.makedirs(ext4_output, exist_ok=True)
            process = subprocess.Popen(
                [INSTALLED_BIN["debugfs"], "-R", f"rdump / {ext4_output}", target_img],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            animated_progress(process, f"Extracting {img_name}.img...")

        # --- CLEAN TEMP ---
        for file in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, file))
            except:
                pass

        print(f"Output : {img_output}")
        input(f"\n{YELLOW}Press Enter to return to menu...{RESET}")

    # =========================================================
    # INVALID MENU
    # =========================================================
    else:
        print(f"\n{RED}[✗] Invalid menu{RESET}")
        input(f"\n{YELLOW}Press Enter to try again...{RESET}")
