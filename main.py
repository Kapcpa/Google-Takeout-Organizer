import os
import json
import shutil
import re
from datetime import datetime


FILE_OP_COPY = 0
FILE_OP_MOVE = 1


def organize_google_photos(src_root: str, dst_root: str, file_operation: int):
    months: dict[int, str] = {
        1: "styczeń", 2: "luty", 3: "marzec", 4: "kwiecień",
        5: "maj", 6: "czerwiec", 7: "lipiec", 8: "sierpień",
        9: "wrzesień", 10: "październik", 11: "listopad", 12: "grudzień"
    }

    ext_pattern = re.compile(r"\.(jpg|jpeg|png|mp4|mov|heic|webp|gif|avi)$", re.IGNORECASE)
    global_metadata = {}
    stats = {"json_match": 0, "fallback": 0, "errors": 0}

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Indexing JSON files...")

    for root, _, files in os.walk(src_root):
        for f in files:
            if f.lower().endswith('.json') and f.lower() != 'metadata.json':
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as jfile:
                        data = json.load(jfile)
                        title = data.get('title')
                        ts = data.get('photoTakenTime', {}).get('timestamp')
                        if title and ts:
                            global_metadata[title] = datetime.fromtimestamp(int(ts))
                except:
                    continue

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Indexed {len(global_metadata)} metadata entries.")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing files...")

    # Counting total files for progress tracking
    total_files = sum([len(files) for r, d, files in os.walk(src_root)])
    processed_count = 0

    for root, _, files in os.walk(src_root):
        for file in files:
            processed_count += 1
            if not ext_pattern.search(file):
                continue

            # Log progress every N files
            if processed_count % 100 == 0:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {processed_count}/{total_files} files scanned...")

            file_path = os.path.join(root, file)
            photo_date = global_metadata.get(file)

            if photo_date:
                stats["json_match"] += 1
            else:
                stats["fallback"] += 1
                photo_date = datetime.fromtimestamp(os.path.getmtime(file_path))

            target_dir = os.path.join(dst_root, str(photo_date.year), months.get(photo_date.month))
            os.makedirs(target_dir, exist_ok=True)

            dest_path = os.path.join(target_dir, file)
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(file)
                counter = 1
                while os.path.exists(os.path.join(target_dir, f"{base}_{counter}{ext}")):
                    counter += 1
                dest_path = os.path.join(target_dir, f"{base}_{counter}{ext}")

            try:
                if file_operation == FILE_OP_COPY:
                    shutil.copy2(file_path, dest_path)
                elif file_operation == FILE_OP_MOVE:
                    shutil.move(file_path, dest_path)
            except Exception as e:
                print(f"\n[ERROR] Could not copy {file}: {e}")
                stats["errors"] += 1

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] FINISHED")
    print(f"JSON matches: {stats['json_match']}")
    print(f"Fallbacks:    {stats['fallback']}")
    print(f"Errors:       {stats['errors']}")


if __name__ == "__main__":
    src = input("Source (Takeout) path: ").strip().strip('"')
    dst = input("Destination path: ").strip().strip('"')
    file_op = int(input("Operation type: 0 (COPY), 1 (MOVE): ").strip())

    if os.path.isdir(src):
        organize_google_photos(src, dst, file_op)
    else:
        print("[ERROR] Source directory not found.")

    input("Press enter to exit...")
