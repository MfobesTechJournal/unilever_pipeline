import os
import shutil
from datetime import date

today_str = date.today().isoformat()

raw_folder = os.path.join("raw_data", today_str)
staging_folder = "staging"
archive_folder = os.path.join("raw_data", "archive", today_str)

os.makedirs(staging_folder, exist_ok=True)
os.makedirs(archive_folder, exist_ok=True)

# Move files to staging
for file in os.listdir(raw_folder):
    full_path = os.path.join(raw_folder, file)

    # Copy to staging
    shutil.copy(full_path, staging_folder)

    # Move original to archive
    shutil.move(full_path, archive_folder)

print("Files moved to staging and archived successfully.")
