r"""
VMwareAdapter v4 – vmrun runProgramInGuest với argument đúng cú pháp.

Root cause v1/v2:
  vmrun runProgramInGuest <vmx> <program> <args>
  → program và args là 2 tham số RIÊNG BIỆT, không được ghép vào nhau.
  → Sai:  vmrun ... "C:\cmd.exe /c start url"   (ghép)
  → Đúng: vmrun ... "C:\cmd.exe" "/c start url"  (tách)

Fix v4:
  - Dùng explorer.exe để mở URL (không cần Firefox cài)
  - Dùng cmd.exe /c copy để tạo file text
  - Argument truyền đúng kiểu subprocess list (không shell=True)
"""
import csv
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    from PIL import ImageGrab  # pyright: ignore[reportMissingImports]
except Exception:
    ImageGrab = None

LOG_DIR = Path("logs");        LOG_DIR.mkdir(exist_ok=True)
SS_DIR  = Path("screenshots"); SS_DIR.mkdir(exist_ok=True)
_fh = None

# ── Logging ────────────────────────────────────────────────────────────

def log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    if _fh:
        _fh.write(line + "\n")
        _fh.flush()

# ── vmrun wrappers ─────────────────────────────────────────────────────

def vmrun(*args) -> subprocess.CompletedProcess:
    """vmrun không cần guest auth (host-level ops)."""
    if not args:
        raise ValueError("vmrun requires at least one operation argument")

    op, *rest = args
    cmd = [config.VMRUN, "-T", "ws", op, config.VMX, *rest]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  vmrun ERR[{r.returncode}]: {r.stderr.strip()[:120]}")
    return r

def vmrun_g(op: str, program: str, args: str = "",
            no_wait: bool = True,
            interactive: bool = False) -> subprocess.CompletedProcess:
    """
    vmrun guest op với program và args tách biệt.
    Cú pháp đúng: vmrun [flags] <op> <vmx> <program> [args]
    """
    cmd = [
        config.VMRUN, "-T", "ws",
        "-gu", config.GUEST_USER,
        "-gp", config.GUEST_PASS,
    ]
    if op == "runProgramInGuest":
        cmd += [op]
        cmd.append(config.VMX)
        if no_wait:
            cmd.append("-noWait")
        if interactive:
            cmd.append("-interactive")
        cmd.append(program)
        if args:
            cmd.append(args)
    else:
        cmd += [op, config.VMX, program]
        if args:
            cmd.append(args)

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  vmrun_g ERR[{r.returncode}]: {r.stderr.strip()[:120]}")
    return r

def vmrun_capture_screen(path: str) -> subprocess.CompletedProcess:
    cmd = [
        config.VMRUN, "-T", "ws",
        "-gu", config.GUEST_USER,
        "-gp", config.GUEST_PASS,
        "captureScreen",
        config.VMX,
        path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  vmrun ERR[{r.returncode}]: {r.stderr.strip()[:120]}")
    return r

def ss(label: str):
    path = str(SS_DIR / f"{label}_{datetime.now().strftime('%H%M%S')}.png")
    r = vmrun_capture_screen(path)
    if r.returncode == 0:
        log(f"  📸 {Path(path).name}")
        return

    try:
        if ImageGrab is None:
            raise RuntimeError("Pillow is not available")
        ImageGrab.grab(all_screens=True).save(path)
        log(f"  📸 {Path(path).name} (host fallback)")
    except Exception as exc:
        log(f"  screenshot failed: {exc}")

# ── URL open via explorer (không cần Firefox) ──────────────────────────

def open_url_in_guest(url: str) -> bool:
    """
    Mở URL bằng explorer.exe — gọi default browser của Windows.
    Không cần biết Firefox cài ở đâu, hoặc dùng Edge cũng được.
    explorer.exe <url> là cách Windows-native, không để trace automation.
    """
    r = vmrun_g(
        "runProgramInGuest",
        r"C:\Windows\System32\cmd.exe",
        f'/c start "" "{url}"',
        no_wait=False,
        interactive=True,
    )
    return r.returncode == 0

# ── File creation via temp file + CopyFileFromHostToGuest ─────────────

def copy_file_to_guest(local_path: str, guest_path: str) -> bool:
    """
    vmrun CopyFileFromHostToGuest — cú pháp: vmrun op vmx src dst
    (không phải runProgramInGuest, khác cú pháp)
    """
    cmd = [
        config.VMRUN, "-T", "ws",
        "-gu", config.GUEST_USER,
        "-gp", config.GUEST_PASS,
        "CopyFileFromHostToGuest",
        config.VMX,
        local_path,
        guest_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"  CopyFile ERR[{r.returncode}]: {r.stderr.strip()[:120]}")
    return r.returncode == 0

# ── Commands ───────────────────────────────────────────────────────────

def wait_for_guest_ready(timeout=120):
    """Chờ đến khi listProcessesInGuest thành công."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        cmd = [config.VMRUN, "-T", "ws",
               "-gu", config.GUEST_USER, "-gp", config.GUEST_PASS,
               "listProcessesInGuest", config.VMX]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            log("  Guest ready ✓")
            return True
        log("  Guest not ready, retry in 10s...")
        time.sleep(10)
    return False

def start_computer(a1, a2):
    log("Starting VM...")
    vmrun("start", "gui")
    log("Waiting for VMware Tools to be ready...")
    
    # Chờ tối đa 3 phút, poll mỗi 15s
    deadline = time.time() + 180
    while time.time() < deadline:
        time.sleep(15)
        cmd = [
            config.VMRUN, "-T", "ws",
            "-gu", config.GUEST_USER,
            "-gp", config.GUEST_PASS,
            "listProcessesInGuest", config.VMX
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            log("  ✓ Guest ready!")
            break
        log(f"  still booting... ({int(deadline - time.time())}s left)")
    else:
        log("  ⚠ Timeout waiting for guest – continuing anyway")
    
    time.sleep(5)  # thêm buffer nhỏ sau khi Tools sẵn sàng
    ss("desktop_ready")


def login_user(password, a2):
    # auto-login đã bật
    time.sleep(8)
    ss("after_login")

def firefox_first_search(term, a2):
    url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
    log(f"Open browser → '{term}'")
    ok = open_url_in_guest(url)
    if not ok:
        log("  explorer failed, retrying...")
        time.sleep(3)
        open_url_in_guest(url)
    time.sleep(9)
    ss(f"s_{term[:20].replace(' ','_')}")

def firefox_new_search(term, a2):
    url = f"https://www.google.com/search?q={term.replace(' ', '+')}"
    log(f"New search → '{term}'")
    open_url_in_guest(url)
    time.sleep(6)
    ss(f"s_{term[:20].replace(' ','_')}")

def create_text_file(fname, content_esc):
    content = content_esc.replace("\\n", "\n")

    # Ghi ra file tạm trên host
    tmp = Path(tempfile.mktemp(suffix=".txt"))
    tmp.write_text(content, encoding="utf-8-sig")  # utf-8-sig để Notepad hiển thị đúng

    guest_path = f"C:\\Users\\{config.GUEST_USER}\\Desktop\\{fname}.txt"
    log(f"Copying file → {fname}.txt")
    ok = copy_file_to_guest(str(tmp), guest_path)
    tmp.unlink(missing_ok=True)

    if ok:
        log(f"  File copied OK → Desktop/{fname}.txt")
    time.sleep(3)
    ss(f"f_{fname}")

def shutdown_computer(a1, a2):
    log("Shutdown via vmrun stop soft...")
    r = vmrun("stop", "soft")
    if r.returncode != 0:
        log("  soft failed → hard stop")
        vmrun("stop", "hard")
    time.sleep(15)
    log("VM off")

DISPATCH = {
    "start_computer":        start_computer,
    "login_user":            login_user,
    "firefox_first_search":  firefox_first_search,
    "firefox_new_search":    firefox_new_search,
    "create_text_file":      create_text_file,
    "shutdown_computer":     shutdown_computer,
}

# ── Debug ──────────────────────────────────────────────────────────────

def debug_check():
    print("=== DEBUG v4 ===\n")

    print(f"[config]")
    print(f"  VMRUN      = {config.VMRUN}")
    print(f"  VMX        = {config.VMX}")
    print(f"  GUEST_USER = {config.GUEST_USER}")

    print("\n[1] listProcessesInGuest (auth test)...")
    cmd = [config.VMRUN, "-T", "ws",
           "-gu", config.GUEST_USER, "-gp", config.GUEST_PASS,
           "listProcessesInGuest", config.VMX]
    r = subprocess.run(cmd, capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    print(f"  rc={r.returncode} | {lines[0] if lines else 'no output'}")
    # Show user-owned processes
    user_procs = [l for l in lines if config.GUEST_USER.lower() in l.lower()]
    for p in user_procs[:5]:
        print(f"    {p.strip()}")

    print("\n[2] CopyFileFromHostToGuest test...")
    tmp = Path(tempfile.mktemp(suffix=".txt"))
    tmp.write_text("vmrun copy test OK", encoding="utf-8")
    guest_path = f"C:\\Users\\{config.GUEST_USER}\\Desktop\\copy_test.txt"
    ok = copy_file_to_guest(str(tmp), guest_path)
    tmp.unlink(missing_ok=True)
    print(f"  ok={ok} → check Desktop in VM for copy_test.txt")

    print("\n[3] open_url_in_guest (explorer.exe https://google.com)...")
    ok3 = open_url_in_guest("https://www.google.com")
    print(f"  ok={ok3} → check VM screen: browser should open")
    time.sleep(5)
    ss("debug_browser_test")
    print(f"  Screenshot saved to screenshots/")

    print("\n[4] vmrun captureScreen...")
    ss("debug_screen")
    print(f"  Check screenshots/ folder")

    print("\n=== DEBUG DONE ===")
    print("Nếu [2] và [3] đều OK → chạy: python src/vm_executor.py khoa")

# ── Main ───────────────────────────────────────────────────────────────

def run(pid: str):
    global _fh
    script_path = Path(f"vm_scripts/vm_script_{pid}.csv")
    if not script_path.exists():
        sys.exit(f"[ERROR] {script_path} not found\n"
                 f"Run: python src/translation.py")

    log_path = LOG_DIR / f"exec_{pid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    _fh = log_path.open("w", encoding="utf-8")

    rows = list(csv.DictReader(script_path.open(encoding="utf-8")))
    log(f"=== START persona={pid} ({len(rows)} commands) ===")

    for i, row in enumerate(rows, 1):
        cmd = row["command"]
        a1  = row.get("arg1", "")
        a2  = row.get("arg2", "")
        log(f"[{i:02d}/{len(rows)}] {cmd}  {a1[:50]}")
        fn = DISPATCH.get(cmd)
        if fn:
            fn(a1, a2)
        else:
            log(f"  [SKIP] unknown: {cmd}")
        time.sleep(2)

    log(f"=== DONE. Log → {log_path} ===")
    _fh.close()
    print(f"\n✓ Xong. VM đã tắt. Tiếp theo: ewfacquire trong WSL.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/vm_executor.py khoa|phuc|debug")
        sys.exit(1)
    if sys.argv[1] == "debug":
        debug_check()
    else:
        run(sys.argv[1])