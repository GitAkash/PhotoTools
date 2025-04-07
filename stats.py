import os
import exifread
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import concurrent.futures
from datetime import datetime
import numpy as np

# Constants
LENS_DATABASE_FILE = "lens_database.csv"
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.tiff', '.dng', '.nef', '.cr2', '.arw'}
OUTPUT_FOLDER = "analyzed_data"


def get_exif_data(image_path, min_rating):
    """Extracts EXIF metadata from an image file. Skips unsupported formats silently."""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag=None, details=False)
    except Exception:
        # Skip unsupported file formats silently
        return None

    def parse_exif(tag):
        if tag in tags:
            value = tags[tag]
            value = str(value)  # Convert IfdTag to string
            if '/' in value:
                num, denom = value.split('/')
                return float(num) / float(denom) if float(denom) != 0 else None
            try:
                return float(value)
            except ValueError:
                return None
        return None

    rating = parse_exif('Image Rating')
    if rating is None or rating < min_rating:
        return None

    return {
        'File': image_path,
        'Rating': rating,
        'F-Stop': parse_exif('EXIF FNumber'),
        'ISO': parse_exif('EXIF ISOSpeedRatings'),
        'Shutter Speed': parse_exif('EXIF ExposureTime'),
        'Focal Length': parse_exif('EXIF FocalLength'),
        'Lens': str(tags.get('EXIF LensModel', ''))
    }


def analyze_folder(folder_path, min_rating=1, selected_lens=None, f_stop_steps=None):
    """Scans all images and computes metadata statistics."""
    image_paths = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                image_paths.append(os.path.join(root, file))

    print(f"Found {len(image_paths)} images. Extracting metadata...")

    data = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda path: get_exif_data(path, min_rating), image_paths))

    for metadata in results:
        if metadata and (selected_lens is None or metadata['Lens'] == selected_lens):
            data.append(metadata)

    if not data:
        print(f"No valid images with rating >= {min_rating} and lens '{selected_lens}' found.")
        return

    df = pd.DataFrame(data)
    numeric_cols = ['F-Stop', 'ISO', 'Shutter Speed', 'Focal Length']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df.dropna(inplace=True)

    if df.empty:
        print("No valid EXIF data extracted.")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Print the number of pictures analyzed
    print(f"Number of pictures analyzed: {len(df)}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'{OUTPUT_FOLDER}/photo_metadata_analysis_{timestamp}.csv'
    df.to_csv(csv_filename, index=False)
    print(f"Analysis saved to '{csv_filename}'")

    # Define standard shutter speeds for Fujifilm X-S10
    shutter_speeds = [1 / 4000, 1 / 2000, 1 / 1000, 1 / 500, 1 / 250, 1 / 125, 1 / 60, 1 / 30, 1 / 15, 1 / 8, 1 / 4,
                      1 / 2, 1, 2, 4, 8, 15, 30, 60]
    shutter_labels = ["1/4000", "1/2000", "1/1000", "1/500", "1/250", "1/125", "1/60", "1/30", "1/15", "1/8", "1/4",
                      "1/2", "1", "2", "4", "8", "15", "30", "60"]

    # Convert shutter speeds to log scale for better visualization
    df['Shutter Speed Log'] = np.log10(df['Shutter Speed'])

    # Visualization
    sns.set(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # F-Stop Plot
    if f_stop_steps:
        sns.histplot(df['F-Stop'], bins=f_stop_steps, kde=True, ax=axes[0, 0], color="blue")
    else:
        sns.histplot(df['F-Stop'], bins=10, kde=True, ax=axes[0, 0], color="blue")
    axes[0, 0].set_title("F-Stop Distribution")

    # ISO Plot
    sns.histplot(df['ISO'], bins=10, kde=True, ax=axes[0, 1], color="red")
    axes[0, 1].set_title("ISO Distribution")

    # Shutter Speed Plot
    sns.histplot(df['Shutter Speed Log'], bins=len(shutter_speeds), kde=True, ax=axes[1, 0], color="green")
    axes[1, 0].set_title("Shutter Speed Distribution")
    axes[1, 0].set_xticks(np.log10(shutter_speeds))
    axes[1, 0].set_xticklabels(shutter_labels, rotation=45)
    axes[1, 0].set_xlabel("Shutter Speed")

    # Focal Length Plot
    sns.histplot(df['Focal Length'], bins=10, kde=True, ax=axes[1, 1], color="purple")
    axes[1, 1].set_title("Focal Length Distribution")

    plt.tight_layout()
    plot_filename = f'{OUTPUT_FOLDER}/photo_metadata_plots_{timestamp}.png'
    plt.savefig(plot_filename)
    plt.show()
    print(f"Plots saved as '{plot_filename}'")


def select_lens():
    """Prompts the user to select a lens from the database."""
    if not os.path.exists(LENS_DATABASE_FILE):
        print(f"Error: '{LENS_DATABASE_FILE}' not found. Please create it with the top 10 lenses.")
        return None, None

    lenses = pd.read_csv(LENS_DATABASE_FILE)
    print("Available Lenses:")
    for i, lens in enumerate(lenses['Lens'], 1):
        print(f"{i}. {lens}")

    try:
        choice = int(input("Select a lens by number (or 0 to analyze all lenses): "))
        if choice == 0:
            return None, None
        selected_lens = lenses.iloc[choice - 1]['Lens']
        f_stop_steps = list(map(float, lenses.iloc[choice - 1]['FStopSteps'].split(',')))
        return selected_lens, f_stop_steps
    except (ValueError, IndexError):
        print("Invalid selection. Analyzing all lenses.")
        return None, None


# Main Execution
if __name__ == "__main__":
    folder_path = "../Camera"  # Change this to your actual folder path
    min_rating = 1  # Adjust the minimum rating required

    selected_lens, f_stop_steps = select_lens()
    analyze_folder(folder_path, min_rating, selected_lens, f_stop_steps)