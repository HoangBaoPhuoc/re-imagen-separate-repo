RE-IMAGEN SEPARATE REPO GUIDE
================================

Muc tieu
- Tao mot repo rieng cho du an Re-imagen.
- Bam sat source goc o Prototype/re-imagen.
- Ho tro 2 huong trien khai:
  1. Reproduction sat ban goc: QEMU + pyautoqemu.
  2. Adaptation cho Windows 11 + VMware neu bat buoc phai dung moi truong nay.

Ghi chu quan trong
- Ban goc dung QEMU, pyautoqemu, templates trong shared/templates, va pipeline translator -> vm_instructor.
- Neu chuyen sang VMware, can ghi ro do la bien the trien khai, khong coi la tuong duong 1:1 voi ban goc neu chua kiem chung.
- Moi thu trong huong dan nay uu tien Python 3.10 va venv de tranh loi cai Pillow tren Python 3.13.

De xuat cau truc repo moi
- README.txt
- Prototype/
  - re-imagen/
    - requirements.txt
    - shared/
    - translator/
    - vm_instructor/
- Demonstration-Examples/
- reports/
- screenshots/
- logs/
- evidence/

Buoc 1: Chuan bi moi truong
1. Cài Python 3.10 hoac 3.11.
2. Kiem tra:
   - python --version
   - pip --version
3. Clone source code goc.
4. Tao venv:
   - py -3.10 -m venv venv
   - venv\Scripts\Activate.ps1
   - python -m pip install --upgrade pip
   - venv\Scripts\python -m pip install -r requirements.txt

Buoc 2: Kiem tra cac file co san trong repo goc
- translator/translator.py: chuyen Activity Description Script thanh VM Interaction Script.
- vm_instructor/vm_instructor.py: thuc thi cac lenh automation tren VM.
- vm_instructor/activities.py: lay nhieu hoat dong mau va co pyautoqemu.
- shared/templates/: chua template GUI cho click/nhan dien.
- requirements.txt: danh sach dependency can cai.

Buoc 3: Chay pipeline co ban cua repo goc
1. Tao Activity Description Script JSON cho persona.
2. Chay translator de sinh VM Interaction Script CSV.
3. Chay vm_instructor tren VM da chuan bi san.
4. Tao disk image E01 tu VM da xu ly.
5. Mo E01 bang Autopsy de trich artifact.

Buoc 4: Neu dung phuong an Windows 11 + VMware
- Ghi ro trong README cua repo moi rang day la adaptation.
- Neu van muon bam sat repository goc, nen tach thanh 2 che do:
  - mode reproduction: dung QEMU/pyautoqemu.
  - mode adaptation: dung VMware va adapter rieng.
- Trong bao cao, neu khong co QEMU, phai noi ro pham vi thay doi va han che.

Buoc 5: Huong dan tao persona va script
1. Tao persona JSON (vi du: sinh vien IT, giao vien tieu hoc).
2. Tao Activity Description Script voi cac truong:
   - time
   - activity
   - search_term
   - file_name
   - content
3. Dam bao timestamp hop ly voi boi canh.
4. Dam bao search term phu hop persona.

Buoc 6: Huong dan chay translation
- Input: activity_script_*.json
- Output: vm_script_*.csv
- Kiem tra cac command chinh:
  - start_computer
  - login_user
  - firefox_open_and_search
  - firefox_new_tab_search
  - notepad_create
  - shutdown_via_menu

Buoc 7: Huong dan chay vm instructor
- Can VM dang chay va cau hinh template dung.
- Kiem tra lai duong dan VMX / disk image.
- Luu screenshot va log trong thu muc rieng.
- Neu automation bi loi click, uu tien keyboard nhu ghi trong repo goc.

Buoc 8: Thu thap va bao toan disk image
1. Tat VM sau khi chay xong.
2. Tao image E01 tu disk cua VM.
3. Ghi hash MD5/SHA1 vao evidence log.
4. Luu thu muc evidence/ cho moi lan chay.

Buoc 9: Phan tich Autopsy
- Add Data Source -> Disk Image -> chon file E01.
- Kiem tra:
  - Web History
  - Cookies
  - Bookmarks
  - Recent Activity
  - File text tao ra
  - Search terms
- Export report HTML/Excel.

Buoc 10: Danh gia
- Coherence Score: do do phu hop giua search term va persona.
- Artifact Recovery Rate: do so artifact tim thay so voi artifact da tao.
- Neu dung adaptation VMware, co the them contamination rate de xem co trace automation bat thuong hay khong.

Checklist truoc khi tao repo rieng
- [ ] Co source code goc trong thu muc con hoac da copy sang repo moi.
- [ ] Co README.txt huong dan day du.
- [ ] Co thu muc results/, logs/, screenshots/, evidence/.
- [ ] Co it nhat 1 persona va 1 activity script mau.
- [ ] Co ke hoach reproduction va adaptation trong cung tai lieu.

Goi y ten repo
- re-imagen-reproduction
- re-imagen-vmware-adaptation
- re-imagen-private-repo

Loi khuyen cuoi
- Neu muc tieu cua ban la bao cao gan voi paper goc, uu tien reproduction sat ban goc.
- Neu muc tieu la lam demo trong moi truong Windows 11 ca nhan, tach ro phan adaptation de tranh nham voi implementation goc.
