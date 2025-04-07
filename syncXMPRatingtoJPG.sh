#!/bin/bash

# Parse command-line options
while getopts p: flag
do
    case "${flag}" in
        p) BASE_PATH=${OPTARG};;
    esac
done

if [ -z "$BASE_PATH" ]; then
    echo "Usage: $0 -p \"path_to_date_folder\""
    exit 1
fi

RAF_FOLDER="$BASE_PATH/RAF"
JPG_FOLDER="$BASE_PATH/JPG"
applied_any=false  # Flag to track if any ratings are applied

if [ ! -d "$RAF_FOLDER" ] || [ ! -d "$JPG_FOLDER" ]; then
    echo "Error: RAF or JPG folder does not exist in $BASE_PATH"
    exit 1
fi

# Iterate over .RAF.xmp files in the RAF folder
for xmp_file in "$RAF_FOLDER"/*.RAF.xmp; do
    if [ -f "$xmp_file" ]; then
        # Extract rating from multiple possible sources
        rating=$(exiftool -s3 -Rating "$xmp_file" | tr -d '[:space:]')

        # Ensure rating is between 1 and 5
        if [[ "$rating" =~ ^[1-5]$ ]]; then
            # Convert rating to Microsoft 100-point scale
            ms_rating=$((rating * 20))  # Microsoft scale: 1★=20, 2★=40, ..., 5★=100

            # Find corresponding JPG file
            jpg_file="$JPG_FOLDER/$(basename "${xmp_file%.RAF.xmp}.JPG")"
            if [ -f "$jpg_file" ]; then
                # Apply the extracted ratings to JPG
                exiftool -overwrite_original \
                    -Rating="$rating" \
                    -XMP:Rating="$rating" \
                    -EXIF:Rating="$rating" \
                    -XMP-acdsee:Rating="$rating" \
                    "$jpg_file"

                echo "Applied rating $rating to $jpg_file"
                applied_any=true  # Set flag to true since a rating was applied
            else
                echo "JPG counterpart not found for $xmp_file"
            fi
        fi
    fi
done

# If no ratings were applied, output a message
if ! $applied_any; then
    echo "No ratings were applied to any files."
fi
