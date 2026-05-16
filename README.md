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
├── Prototype/
├── reports/
├── screenshots/
├── logs/
├── evidence/
├── README.md
└── readme.txt
```

If you copy the original prototype into this repo, keep the internal structure close to the source project:

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

For the full step-by-step plan, use the detailed guide in `readme.txt`.
