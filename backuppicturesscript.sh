#!/bin/bash

# Define the SSD model and partition
SSD_MODEL="PSSD T7 Shield"  # From your disk info
SSD_DEVICE="/dev/sda1"  # Using the correct partition
SSD_MOUNT_POINT="/mnt/externalssd"

# Define source directories
SOURCE_DIRS=("$HOME/Pictures/Camera" "$HOME/Pictures/Digikam")

# Check if rsync is installed
if ! command -v rsync &>/dev/null; then
    echo "Error: rsync is not installed. Please install it and try again."
    exit 1
fi

# Check if the source directories exist
for dir in "${SOURCE_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Error: Source directory '$dir' does not exist. Exiting."
        exit 1
    fi
done

# Check if the SSD is already mounted
if mount | grep "$SSD_MOUNT_POINT" > /dev/null; then
    echo "The SSD is already mounted at $SSD_MOUNT_POINT."
else
    # If the SSD is not mounted, attempt to mount it
    echo "Mounting the SSD at $SSD_MOUNT_POINT..."
    sudo mount $SSD_DEVICE $SSD_MOUNT_POINT
    if [ $? -ne 0 ]; then
        echo "Failed to mount the SSD. Exiting."
        exit 1
    fi
fi

# Check disk usage before backup
echo "Checking disk usage on the SSD..."
df -h $SSD_MOUNT_POINT

# Show space used by the SSD folder specifically
echo "Checking space used by the SSD folder..."
du -sh $SSD_MOUNT_POINT

# Run rsync to back up files (Camera and DigiKam)
echo "Starting backup process..."
sudo rsync -aAXvh --progress --checksum --no-owner --no-group "${SOURCE_DIRS[@]}" $SSD_MOUNT_POINT

# Verify if the backup was successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully!"
else
    echo "Backup failed. Please check the logs."
    exit 1
fi

# Check if the SSD is still mounted before attempting to unmount
if mount | grep "$SSD_MOUNT_POINT" > /dev/null; then
    # Unmount the SSD after the backup
    echo "Unmounting the SSD..."
    sudo umount $SSD_MOUNT_POINT

    # Check if the unmount was successful
    if [ $? -eq 0 ]; then
        echo "SSD unmounted successfully!"
    else
        echo "Failed to unmount the SSD. Please check manually."
        exit 1
    fi
else
    echo "The SSD is not mounted. No need to unmount."
fi

# Check final disk usage after backup
echo "Checking disk usage on the SSD after backup..."
df -h $SSD_MOUNT_POINT

