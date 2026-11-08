import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ZIP_NAME = "YottaFlex-Manufacturing-Submission.zip"
ZIP_PATH = ROOT_DIR / ZIP_NAME

EXCLUDE_DIRS = {
    ".git",
    "venv",
    ".venv",
    "node_modules",
    ".pytest_cache",
    ".vscode",
    ".idea",
    "dist",
    "__pycache__",
    "backups",
    "services_backup",
}

EXCLUDE_FILES = {
    ".env",
    ZIP_NAME,
    ".DS_Store",
    "Thumbs.db",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
}


def package_clean_submission():
    print(f"Creating clean submission archive: {ZIP_NAME}")
    included_count = 0

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                if file.startswith(".env.") and file != ".env.example":
                    continue
                file_path = Path(root) / file
                if file_path.suffix.lower() in EXCLUDE_EXTENSIONS:
                    continue

                arcname = file_path.relative_to(ROOT_DIR)
                zipf.write(file_path, arcname)
                included_count += 1

    zip_size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    print(f"Submission archive created successfully:")
    print(f"  Path: {ZIP_PATH}")
    print(f"  Size: {zip_size_mb:.2f} MB")
    print(f"  Total Files Packaged: {included_count}")

    # Verify no secrets in zip
    with zipfile.ZipFile(ZIP_PATH, "r") as zipf:
        names = zipf.namelist()
        assert ".env" not in names, "SECURITY ERROR: .env found in ZIP!"
        assert any(n == ".env.example" for n in names), "ERROR: .env.example missing from ZIP!"
        assert not any("node_modules" in n for n in names), "ERROR: node_modules found in ZIP!"
        assert not any("venv" in n for n in names), "ERROR: venv found in ZIP!"
        assert not any(".git/" in n for n in names), "ERROR: .git found in ZIP!"
    print("  Verification: Security and clean packaging checks ALL PASSED!")


if __name__ == "__main__":
    package_clean_submission()
