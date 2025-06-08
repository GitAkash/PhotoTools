#!/usr/bin/env python3

import subprocess
import os
import sys

def check_command_exists(command):
    """Check if a command exists."""
    return subprocess.call(['which', command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def list_block_devices():
    """List external block devices using lsblk."""
    try:
        result = subprocess.run(["lsblk", "-o", "NAME,SIZE,MOUNTPOINT,MODEL"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error listing devices: {e}")
        sys.exit(1)

def select_block_device():
    """Prompt the user to select a block device."""
    output = list_block_devices()
    lines = output.splitlines()
    devices = []
    print("\nAvailable external devices:\n")
    for idx, line in enumerate(lines[1:], start=0):  # Skip header
        print(f"{idx}: {line}")
        devices.append(line)

    print("\nq: Cancel and exit")
    while True:
        choice = input("Select the device number you want to use: ")
        if choice.lower() == 'q':
            print("Exiting.")
            sys.exit(0)
        try:
            index = int(choice)
            if 0 <= index < len(devices):
                dev_line = devices[index]
                dev_name = dev_line.split()[0]
                return f"/dev/{dev_name}"
            else:
                print("Invalid index.")
        except ValueError:
            print("Please enter a valid number.")

def get_mount_point(device):
    """Check if the device is already mounted."""
    try:
        result = subprocess.run(["lsblk", "-o", "NAME,MOUNTPOINT", "-nr"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        for line in lines:
            parts = line.split()
            if parts[0] in device:
                return parts[1] if len(parts) > 1 else None
    except Exception as e:
        print(f"Error getting mount point: {e}")
    return None

def mount_device(device):
    """Attempt to mount the selected device."""
    try:
        mount_point = "/mnt/" + os.path.basename(device)
        os.makedirs(mount_point, exist_ok=True)
        subprocess.run(["sudo", "mount", device, mount_point], check=True)
        return mount_point
    except subprocess.CalledProcessError:
        print("❌ Failed to mount the device.")
        sys.exit(1)

def list_dirs(base_path):
    try:
        return [d for d in os.listdir(base_path)
                if os.path.isdir(os.path.join(base_path, d))]
    except Exception as e:
        print(f"Error reading {base_path}: {e}")
        return []

def prompt_for_directory(prompt_text, base_path=os.path.expanduser("~/Pictures")):
    dirs = list_dirs(base_path)
    print(f"\n{prompt_text}")
    for i, d in enumerate(dirs):
        print(f"{i}: {d}")
    print("c: Type a custom absolute path")
    print("q: Quit")

    while True:
        choice = input("Select a folder by number, 'c' for custom path, or 'q' to quit: ")
        if choice.lower() == 'q':
            print("Exiting.")
            sys.exit(0)
        elif choice.lower() == 'c':
            custom_path = input("Enter the full path to the folder: ")
            if os.path.isdir(custom_path):
                return os.path.abspath(custom_path)
            else:
                print("Invalid path. Try again.")
        else:
            try:
                idx = int(choice)
                selected = os.path.join(base_path, dirs[idx])
                return os.path.abspath(selected)
            except (ValueError, IndexError):
                print("Invalid selection. Try again.")

def check_source_dirs(source_dirs):
    for dir_path in source_dirs:
        if not os.path.isdir(dir_path):
            print(f"Error: Source directory '{dir_path}' does not exist.")
            sys.exit(1)

def check_disk_usage(path):
    subprocess.run(["df", "-h", path])
    subprocess.run(["du", "-sh", path])

def run_backup(source_dirs, dest):
    command = [
        "sudo", "rsync", "-aAXvh", "--progress", "--checksum",
        "--no-owner", "--no-group"
    ] + source_dirs + [dest]
    result = subprocess.run(command)
    if result.returncode == 0:
        print("✅ Backup completed successfully!")
    else:
        print("❌ Backup failed.")
        sys.exit(1)

def unmount_device(mount_point):
    choice = input("Do you want to unmount the SSD now? (y/n): ").lower()
    if choice == 'y':
        result = subprocess.run(["sudo", "umount", mount_point])
        if result.returncode == 0:
            print("✅ Unmounted successfully.")
        else:
            print("❌ Failed to unmount. Please do it manually.")

def main():
    # 1. Check rsync
    if not check_command_exists("rsync"):
        print("rsync is not installed. Please install it and try again.")
        sys.exit(1)

    # 2. Select source directories
    print("\n📁 Select the folders to back up:")
    camera_dir = prompt_for_directory("Select your 📷 Camera photo folder")
    digikam_dir = prompt_for_directory("Select your 📚 Digikam database folder")
    source_dirs = [camera_dir, digikam_dir]
    check_source_dirs(source_dirs)

    # 3. Select device
    print("\n💽 Select the external storage device:")
    device = select_block_device()
    mount_point = get_mount_point(device)

    if mount_point:
        print(f"🔌 Device is already mounted at {mount_point}")
    else:
        print(f"🛠 Mounting device {device}...")
        mount_point = mount_device(device)

    # 4. Disk usage before
    print("\n📊 Disk usage before backup:")
    check_disk_usage(mount_point)

    # 5. Run rsync backup
    print("\n🚀 Starting backup...")
    run_backup(source_dirs, mount_point)

    # 6. Disk usage after
    print("\n📊 Disk usage after backup:")
    check_disk_usage(mount_point)

    # 7. Optionally unmount
    unmount_device(mount_point)

if __name__ == "__main__":
    main()

