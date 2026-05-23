# Re-Imagen — Digital Forensics Persona Simulator

Công cụ tự động mô phỏng hành vi người dùng trên máy ảo Windows để tạo disk image phục vụ phân tích pháp y kỹ thuật số.  
Pipeline: **Tạo persona → Dịch script → Snapshot → Chạy VM → Thu thập ảnh đĩa → Phân tích Autopsy → Đánh giá**

---

## Cấu trúc thư mục

```text
re-imagen-separate-repo/
├── src/
│   ├── generate_personas.py   # Tạo persona và activity script qua GPT-4o
│   ├── translation.py         # Dịch activity JSON → CSV lệnh VM
│   ├── vm_executor.py         # Thực thi lệnh trên máy ảo qua vmrun
│   └── evaluator.py           # Đánh giá độ coherence của activity script
├── personas/
│   ├── persona_<id>.json      # Profile người dùng (GPT sinh)
│   ├── activity_<id>.json     # Kịch bản hoạt động (GPT sinh)
│   └── sample_personas.txt    # File tham khảo để nhập thông tin
├── vm_scripts/
│   └── vm_script_<id>.csv     # Script lệnh đã dịch (input cho vm_executor)
├── logs/                      # Log chạy VM
├── screenshots/               # Screenshot tự động trong quá trình chạy
├── disk_images/               # File E01 sau khi thu thập
├── results/                   # Kết quả đánh giá coherence
├── config.py                  # Cấu hình đường dẫn VMware, credentials
└── requirements.txt
```

---

## Yêu cầu

### Phần mềm host (Windows)

| Phần mềm | Mục đích |
| --- | --- |
| Python 3.10+ | Chạy pipeline |
| VMware Workstation | Máy ảo Windows |
| WSL (Windows Subsystem for Linux) | Chạy `qemu-img` và `ewfacquire` |
| Autopsy | Phân tích ảnh đĩa |

### Cài qemu-img và ewftools trong WSL

```bash
sudo apt update
sudo apt install qemu-utils libewf-dev ewf-tools
```

### Cài Python dependencies

```powershell
cd re-imagen-separate-repo
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Cấu hình `config.py`

```python
OPENAI_API_KEY = "sk-..."

VMRUN      = r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
VMX        = r"E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx"
VMDK       = r"E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmdk"

GUEST_USER = "testuser"
GUEST_PASS = "P@ssword123"
DESKTOP    = r"C:\Users\testuser\Desktop"
```

---

## Pipeline đầy đủ

### Bước 1 — Tạo Persona & Activity Script

```powershell
python src/generate_personas.py
```

Chương trình hỏi từng trường thông tin. Tham khảo `personas/sample_personas.txt` để biết cách điền.  
Ví dụ nhập cho một persona:

```text
Số lượng persona cần tạo [1]: 1

── Persona 1/1 ──────────────────────────────
  ID ngắn: khoa
  Họ và tên đầy đủ: Huynh Dang Khoa
  Tuổi [22]: 22
  Địa điểm [Ho Chi Minh City, Vietnam]:
  Nghề nghiệp / chuyên ngành: Undergraduate student, Computer Science
  Trường / tổ chức: University of Information Technology (UIT)
  Ngôn ngữ [...]:
  Lịch sử dụng máy: Saturday June 14 2025, 20:00-23:00 UTC+7
  Số file text cần tạo [1]: 1
```

**Output:** `personas/persona_khoa.json` và `personas/activity_khoa.json`

Activity script sẽ gồm các loại hoạt động:

- `google_search` — tìm kiếm Google
- `create_folder` — tạo folder trên Desktop
- `create_text_document` — tạo file `.txt` vào folder
- `download_file` — tải file từ URL công khai
- `delete_file` — xoá file sau khi đọc

---

### Bước 2 — Dịch sang VM Script

```powershell
python src/translation.py
```

**Output:** `vm_scripts/vm_script_khoa.csv`

File CSV gồm các lệnh: `start_computer`, `login_user`, `firefox_first_search`, `firefox_new_search`, `create_folder`, `create_text_file`, `download_file`, `delete_file`, `shutdown_computer`.

---

### Bước 3 — Chuẩn bị Snapshot

> **Quan trọng:** Phải restore snapshot sạch trước mỗi lần chạy để đảm bảo tính toàn vẹn pháp lý và khả năng tái tạo.

#### Tạo snapshot sạch (làm một lần)

Bật VM, đăng nhập, đảm bảo desktop sạch, rồi chạy:

```powershell
& "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -T ws snapshot "E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx" clean_baseline
```

Tắt VM sau khi snapshot xong:

```powershell
& "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -T ws stop "E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx" soft
```

#### Restore snapshot trước mỗi lần chạy persona

```powershell
& "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -T ws revertToSnapshot "E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx" clean_baseline
```

Sau đó chạy `vm_executor.py` — script tự bật VM, không cần mở thủ công.

---

### Bước 4 — Chạy VM Executor

```powershell
python src/vm_executor.py khoa
```

Script sẽ tự động:

1. Bật máy ảo (`vmrun start`)
2. Chờ VMware Tools sẵn sàng (tối đa 3 phút)
3. Thực thi từng lệnh trong CSV theo thứ tự
4. Chụp screenshot tại mỗi bước → `screenshots/`
5. Tắt máy ảo (`vmrun stop soft`) khi xong

**Log** được lưu tự động tại `logs/exec_khoa_<timestamp>.log`.

Theo dõi tiến trình:

```text
[01/16] start_computer
[02/16] login_user
[03/16] firefox_first_search  latest advancements in artificial intelligence
  📸 s_latest_advancements__203215.png
...
[16/16] shutdown_computer
✓ Xong. VM đã tắt. Tiếp theo: ewfacquire trong WSL.
```

---

### Bước 5 — Thu thập Ảnh Đĩa (EWF/E01)

Chạy trong WSL sau khi VM đã tắt hoàn toàn:

```bash
# Chuyển VMDK sang raw image
qemu-img convert -p -O raw \
    "/mnt/e/VMWare/Virtual Machines/Windows 10 x64/Windows 10 x64.vmdk" \
    windows10.img
```

```bash
# Thu thập ảnh E01
sudo ewfacquire \
    -t "/mnt/e/UIT/HK6/Forensics/project/re-imagen-separate-repo/disk_images/khoa" \
    -f encase6 \
    -c best \
    -m removable \
    -e "Re-imagen" \
    -d "Persona Huynh Dang Khoa – CS student HCMC" \
    "windows10.img"
```

Tham số `ewfacquire`:

| Flag | Ý nghĩa |
| --- | --- |
| `-t` | Đường dẫn output (không cần đuôi `.E01`) |
| `-f encase6` | Format EnCase 6 (tương thích Autopsy) |
| `-c best` | Nén tốt nhất |
| `-m removable` | Loại media |
| `-e` | Tên examiner |
| `-d` | Mô tả case |

```bash
# Xác minh tính toàn vẹn
ewfverify "/mnt/e/UIT/HK6/Forensics/project/re-imagen-separate-repo/disk_images/khoa.E01"

# Dọn raw image sau khi xác minh thành công
rm windows10.img
```

---

### Bước 6 — Phân tích với Autopsy

1. Mở Autopsy → **New Case** → điền tên case
2. **Add Data Source** → chọn `disk_images/khoa.E01`
3. Bật các Ingest Module:
   - **Recent Activity** — browser history, recent documents
   - **Web Artifacts** — Google searches, downloads
   - **Keyword Search** — tìm kiếm từ khoá trong file
   - **File Type Identification** — phân loại file
4. Chờ ingest hoàn tất
5. Xuất artifact: **Generate Report → HTML/CSV**

Các artifact cần chú ý:

| Autopsy node | Nội dung kỳ vọng |
| --- | --- |
| Web Search | Các search term từ activity script |
| Web Downloads | File đã download |
| Recent Documents | File `.txt` đã tạo trên Desktop |
| Deleted Files | File đã xoá (`delete_file`) |
| Web History | URLs Google đã truy cập |

---

### Bước 7 — Đánh giá Coherence

```powershell
python src/evaluator.py
# hoặc chỉ định ID cụ thể:
python src/evaluator.py khoa
python src/evaluator.py khoa phuc
```

Output mẫu:

```text
────────────────────────────────────────────────────────
Khoa
Searches : 10  |  Coherence: 90.0%
Folders  : Cyber_Resources
Docs     : cert_notes.txt
Download : NIST_FIPS.pdf  ← https://nvlpubs.nist.gov/...
Deleted  : NIST_FIPS.pdf

  ✓ latest advancements in artificial intelligence   ['artificial', 'intelligence']
  ✓ best practices in cybersecurity for beginners    ['cybersecurity']
  ...
```

Kết quả JSON được lưu tại `results/coherence_<id>.json`.

---

## Chạy nhiều Persona

Với mỗi persona, **phải restore snapshot trước khi chạy**:

```powershell
# Persona 1
& "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -T ws revertToSnapshot "E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx" clean_baseline
python src/vm_executor.py khoa

# Sau khi VM tắt → thu thập E01 cho khoa

# Persona 2
& "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" -T ws revertToSnapshot "E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx" clean_baseline
python src/vm_executor.py phuc

# Sau khi VM tắt → thu thập E01 cho phuc
```

---

## Tóm tắt lệnh

```text
[Chỉ chạy một lần]
python src/generate_personas.py      ← nhập thông tin persona
python src/translation.py            ← dịch sang CSV

[Lặp lại cho mỗi persona]
vmrun revertToSnapshot ... clean_baseline   ← restore snapshot
python src/vm_executor.py <id>              ← chạy VM
(trong WSL) qemu-img convert ... + ewfacquire + ewfverify

[Sau khi có E01]
Autopsy → phân tích artifacts
python src/evaluator.py              ← đánh giá coherence
```

---

## Checklist

- [ ] `config.py` đã cấu hình đúng VMRUN, VMX, VMDK, credentials
- [ ] Snapshot `clean_baseline` đã tạo
- [ ] `python src/generate_personas.py` → persona + activity JSON OK
- [ ] `python src/translation.py` → CSV OK
- [ ] Snapshot đã restore trước khi chạy
- [ ] `python src/vm_executor.py <id>` → VM tắt, log + screenshots OK
- [ ] `qemu-img convert` → `windows10.img` OK
- [ ] `ewfacquire` → `disk_images/<id>.E01` OK
- [ ] `ewfverify` → hash OK
- [ ] Autopsy ingest hoàn tất, artifacts xuất ra
- [ ] `python src/evaluator.py` → coherence report OK
