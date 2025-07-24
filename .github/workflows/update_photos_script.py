import os
import json
import subprocess
from pathlib import Path

# --- Configuration ---
PHOTOS_DIR = os.getenv('PHOTOS_DIR', 'live/photos')
JSON_FILE = os.getenv('JSON_FILE', 'live/photos.json')
# --- End Configuration ---

def get_gps_from_exif(image_path):
    """
    Extracts GPS coordinates (latitude, longitude) from an image using exiftool.
    Returns [latitude, longitude] or None if not found/error.
    """
    try:
        # Use exiftool to extract GPS coordinates
        # -json: output in JSON format
        # -c "%+.6f": format coordinates with 6 decimal places and sign
        # -GPSLatitudeRef -GPSLongitudeRef: include reference (N/S, E/W)
        # -GPSLatitude -GPSLongitude: the actual coordinate tags
        command = [
            'exiftool',
            '-json',
            '-c', '%.6f', # Format coordinates directly
            '-GPSLatitude',
            '-GPSLongitude',
            str(image_path)
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        exif_data = json.loads(result.stdout)

        if exif_data and exif_data[0]:
            data = exif_data[0]
            lat = data.get('GPSLatitude')
            lon = data.get('GPSLongitude')

            # exiftool provides lat/lon as float, no need for ref
            if lat is not None and lon is not None:
                return [float(lat), float(lon)]
        return None
    except Exception as e:
        print(f"Error extracting EXIF for {image_path}: {e}")
        return None

def main():
    json_path = Path(JSON_FILE)
    photos_dir = Path(PHOTOS_DIR)

    # 1. Load existing photos from JSON
    existing_photos_map = {}
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                for photo in existing_data:
                    existing_photos_map[photo['name']] = photo
        except json.JSONDecodeError:
            print(f"Warning: {JSON_FILE} is malformed or empty. Starting fresh.")
            existing_data = []
    else:
        print(f"Info: {JSON_FILE} not found. Will create a new one.")
        existing_data = []

    # 2. Get current images in directory
    current_image_files = {f.name for f in photos_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']}

    # 3. Find new images
    existing_image_names = set(existing_photos_map.keys())
    new_image_names = current_image_files - existing_image_names

    photos_updated = False

    # 4. Process new images and add to existing data
    for image_name in sorted(list(new_image_names)): # Sort for consistent order
        image_path = photos_dir / image_name
        gps_coords = get_gps_from_exif(image_path)
        if gps_coords:
            new_entry = {"name": image_name, "gps": gps_coords}
            existing_data.append(new_entry)
            print(f"Added new photo: {image_name} with GPS: {gps_coords}")
            photos_updated = True
        else:
            print(f"Skipping {image_name}: No GPS data found or error extracting.")

    # 5. Handle removed images (optional, but good for sync)
    # This block identifies images that are in JSON but no longer in the directory
    removed_image_names = existing_image_names - current_image_files
    if removed_image_names:
        print(f"Found removed images: {removed_image_names}. Removing from JSON.")
        existing_data = [photo for photo in existing_data if photo['name'] not in removed_image_names]
        photos_updated = True


    # 6. Write updated JSON back
    if photos_updated:
        # Sort the entire list by name for consistency
        existing_data.sort(key=lambda x: x['name'])
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        print(f"{JSON_FILE} updated successfully.")
        print("json_updated=true") # Output for GitHub Actions
    else:
        print("No new photos found or photos.json is already up to date.")
        print("json_updated=false") # Output for GitHub Actions

if __name__ == "__main__":
    main()
