# Re-imagen Separate Repo

Project workspace for a standalone copy of the Re-imagen prototype.

This repository is organized to support two possible execution paths:

1. **Reproduction path** - stay close to the original Re-imagen repository structure and behavior.
2. **Adaptation path** - use a Windows 11 + VMware environment when QEMU is not available, while clearly documenting the differences.

## Goals

- Keep the prototype easy to copy into a new GitHub repository.
- Preserve the original pipeline idea: `translator -> vm_instructor -> Autopsy`.
- Make the environment setup explicit and repeatable.
- Separate generated artifacts, logs, screenshots, and evidence from source code.

## Suggested Repository Layout

```text
re-imagen-separate-repo/
├── src/
├── tests/
├── personas/
├── vm_scripts/
├── logs/
├── screenshots/
├── evidence/
├── reports/
├── Prototype/
└── README.md
```

If you copy the original prototype into this repo, keep the internal structure close to the source project, but do not treat it as the active source root:

```text
Prototype/
└── re-imagen/
    ├── requirements.txt
    ├── shared/
    ├── translator/
    └── vm_instructor/
```

## Environment Setup

### 1. Install Python

Use **Python 3.10** or **Python 3.11**.

Check your version:

```powershell
python --version
pip --version
```

### 2. Create a virtual environment

From the project root:

```powershell
py -3.10 -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt
```

### 3. Install external tools

Depending on the path you choose, install the following tools on the host machine:

- **QEMU** for the original pyautoqemu-based workflow.
- **Autopsy** for forensic analysis.
- **Tesseract OCR** for text recognition.
- **FTK Imager** or `ewfacquire` for disk image creation.

## Workflow Overview

### Reproduction path

1. Prepare the VM and templates.
2. Create an Activity Description Script in JSON.
3. Run the translator to create a VM Interaction Script in CSV.
4. Run the VM instructor to execute the VM actions.
5. Shut down the VM and create an E01 disk image.
6. Analyze the image in Autopsy.

### Adaptation path

1. Prepare the VM in VMware.
2. Keep the same persona and script structure.
3. Document any differences from the original QEMU workflow.
4. Record screenshots, logs, and evidence separately.
5. Compare artifacts and note limitations clearly in the report.

## Real VMware Run Demo

Use this section when you want to demo the pipeline on a real VMware VM instead of the dummy dry-run.

### Prerequisites

- VMware Workstation installed on the host.
- A Windows guest VM already prepared and bootable.
- A clean snapshot created before the demo run.
- `vmrun.exe` available, usually at `C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe`.
- Guest credentials that match the VM account used in the scripts.

### Recommended demo flow

1. Restore the VM to the clean snapshot.
2. Start the guest and confirm it reaches the Windows desktop.
3. Run the pipeline in real mode with `main_pipeline.py`.
4. Wait for the VM to finish the activity script and shut down.
5. Collect the generated log and screenshot files from `logs/` and `screenshots/`.
6. Create the E01 disk image with FTK Imager or `ewfacquire`.
7. Import the image into Autopsy and export the artifacts you need for the report.

### Real run command

From the project root, run:

```powershell
$env:PYTHONPATH = "re-imagen-separate-repo"
python re-imagen-separate-repo\src\main_pipeline.py re-imagen-separate-repo\personas\activity_script_A.json "E:\VMWare\Virtual Machines\Windows 10 x64\Windows 10 x64.vmx" testuser Password123 --vmrun-path "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
```

If you want to rehearse the demo first without touching the VM, add `--dry-run`:

```powershell
$env:PYTHONPATH = "re-imagen-separate-repo"
python re-imagen-separate-repo\src\main_pipeline.py re-imagen-separate-repo\personas\activity_script_A.json "C:\Path\To\YourVM.vmx" testuser Password123 --vmrun-path "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" --dry-run
```

### What to show in the demo

- The persona JSON and activity script JSON.
- The generated CSV in `vm_scripts/`.
- The execution log in `logs/`.
- The screenshots in `screenshots/`.
- The E01 image hash and the Autopsy artifact export.

### If something fails

- Check that the VM snapshot is clean and the guest is powered on correctly.
- Verify the `vmrun.exe` path.
- Confirm the guest username and password in the command line.
- Re-run once with `--dry-run` if you only need to verify the pipeline logic.

## What Goes Where

- `Prototype/`: source code and prototype assets.
- `reports/`: final report drafts, tables, and exported results.
- `screenshots/`: screenshots from automation runs and Autopsy.
- `logs/`: execution logs, run logs, and debug output.
- `evidence/`: hashes, disk image references, and chain-of-custody notes.

## Minimum Files to Prepare

- `persona_*.json`
- `activity_script_*.json`
- `vm_script_*.csv`
- `execution_log_*.txt`
- `evidence_log.txt`
- `autopsy_export_*.csv` or report exports

## Recommended Execution Order

1. Set up the Python environment.
2. Verify the prototype runs with the required dependencies.
3. Generate the persona and activity scripts.
4. Run translation.
5. Run VM instruction automation.
6. Create the disk image.
7. Analyze with Autopsy.
8. Save evidence and report outputs.

## Quick Start — Run pipeline end-to-end

Use these condensed steps to run the pipeline from this repository root and produce an EWF image ready for Autopsy.

1. On the Windows host (PowerShell), from the repository root:

```powershell
cd re-imagen-separate-repo
python src/generate_personas.py
python src/translation.py
python src/vm_executor.py khoa   # or: python src/vm_executor.py phuc
```

Wait until the script prints `✓ VM tắt xong`.

2. In WSL (convert VMDK → raw, then acquire EWF):

```bash
# run in WSL or via `wsl qemu-img ...` from PowerShell
qemu-img convert -p -O raw "/mnt/e/VMWare/Virtual Machines/Windows 10 x64/Windows 10 x64.vmdk" windows10.img

sudo ewfacquire \
    -t "/mnt/e/UIT/HK6/Forensics/project/re-imagen-separate-repo/disk_images/khoa" \
    -f encase6 -c best -m removable \
    -e "Re-imagen" \
    -d "Persona Huynh Dang Khoa – IT student HCMC" \
    "windows10.img"

# verify the created E01
ewfverify "/mnt/e/UIT/HK6/Forensics/project/re-imagen-separate-repo/disk_images/khoa.E01"
```

3. Import into Autopsy: New Case → Add Data Source → point to `disk_images/khoa.E01`. Use ingest modules: Recent Activity, Web Artifacts, Keyword Search, File Type ID.

4. Evaluate coherence (host):

```powershell
python src/evaluator.py
```

5. Cleanup: after `ewfverify` succeeds you can remove `windows10.img` to free space.

See `Re-imagen-guide-deploy.md` for full step-by-step details and troubleshooting.

## Notes

- Keep the source copy and the working copy separate if you want to maintain a clean Git history.
- If you use the VMware adaptation path, note that it is a practical variant, not a drop-in replacement for the QEMU workflow.
- Prefer keyboard automation when GUI clicks are unreliable.

## Checklist

- [ ] Prototype folder copied into this repo
- [ ] Python venv created with Python 3.10 or 3.11
- [ ] Dependencies installed successfully
- [ ] Persona JSON prepared
- [ ] Activity Description Script prepared
- [ ] Translator run completed
- [ ] VM instruction run completed
- [ ] Disk image created
- [ ] Autopsy analysis exported
- [ ] Screenshots, logs, and evidence saved

## Reference
