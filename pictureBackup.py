#!/usr/bin/env python3
import subprocess
import sys
import os
import json
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

def list_partitions():
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,SIZE,MOUNTPOINT,MODEL,TYPE"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to run lsblk: {e}")
        sys.exit(1)

    data = result.stdout
    blkinfo = json.loads(data)
    partitions = []

    def parse_blockdevices(devices):
        for dev in devices:
            if dev["type"] == "part":
                partitions.append((
                    dev["name"],
                    dev.get("size", ""),
                    dev.get("mountpoint") or "",
                    dev.get("model") or "",
                ))
            if "children" in dev:
                parse_blockdevices(dev["children"])

    parse_blockdevices(blkinfo["blockdevices"])
    return partitions

def select_partition():
    partitions = list_partitions()
    if not partitions:
        print("No partitions found.")
        sys.exit(1)

    print("\nAvailable partitions:\n")
    for i, (name, size, mount, model) in enumerate(partitions):
        print(f"{i}: /dev/{name} Size: {size} Mounted: {mount or '-'} Model: {model or '-'}")
    print("\nq: Cancel and exit")

    while True:
        choice = input("Select the partition number you want to use: ").strip()
        if choice.lower() == 'q':
            print("Exiting.")
            sys.exit(0)
        try:
            idx = int(choice)
            if 0 <= idx < len(partitions):
                return f"/dev/{partitions[idx][0]}"
            else:
                print("Invalid number. Try again.")
        except ValueError:
            print("Please enter a valid number.")

def mount_device(device):
    device_name = os.path.basename(device)

    # Get mount info from lsblk
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,MOUNTPOINT"],
            capture_output=True,
            text=True,
            check=True,
        )
        blkinfo = json.loads(result.stdout)
    except Exception as e:
        print(f"Failed to check lsblk info: {e}")
        sys.exit(1)

    def find_mount(devices):
        for dev in devices:
            if f"/dev/{dev['name']}" == device:
                return dev.get("mountpoint")
            if "children" in dev:
                mp = find_mount(dev["children"])
                if mp:
                    return mp
        return None

    mount_point = find_mount(blkinfo["blockdevices"])

    if mount_point:
        print(f"✅ Device {device} is already mounted at {mount_point}")
        return mount_point
    else:
        mount_point = f"/mnt/{device_name}"
        try:
            print(f"🛠 Creating mount point {mount_point} (requires sudo)...")
            subprocess.run(["sudo", "mkdir", "-p", mount_point], check=True)
            print(f"🛠 Mounting device {device} at {mount_point} (requires sudo)...")
            subprocess.run(["sudo", "mount", device, mount_point], check=True)
            print(f"✅ Mounted {device} at {mount_point}")
            return mount_point
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to mount device: {e}")
            sys.exit(1)

def unmount_device(mount_point):
    try:
        print(f"🛠 Unmounting {mount_point} (requires sudo)...")
        subprocess.run(["sudo", "umount", mount_point], check=True)
        print(f"✅ Unmounted {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to unmount {mount_point}: {e}")

def select_source_directories():
    print("\nPlease enter the full paths of the source directories to back up.")
    print("Enter one directory at a time, use Tab to autocomplete.")
    print("Press Enter on an empty line to finish.\n")

    path_completer = PathCompleter(only_directories=True, expanduser=True)
    selected_dirs = []

    while True:
        user_input = prompt("Source directory (empty to finish): ", completer=path_completer).strip()
        if not user_input:
            if selected_dirs:
                break
            else:
                print("Please enter at least one directory.")
                continue

        expanded = os.path.abspath(os.path.expanduser(user_input))
        if not os.path.isdir(expanded):
            print(f"'{expanded}' is not a valid directory. Try again.")
            continue

        if expanded in selected_dirs:
            print("Directory already added. Choose another or press Enter to finish.")
            continue

        selected_dirs.append(expanded)
        print(f"Added: {expanded}")

    return selected_dirs

def ask_delete_option():
    print("\n🧩 Do you want to enable mirror mode?")
    print("This will DELETE files from the backup if they no longer exist in the source.")
    print("Useful for syncing exactly, but unsafe if you want an archive.\n")
    while True:
        choice = input("Mirror deletions with --delete? (y/N): ").strip().lower()
        if choice in ('y', 'n', ''):
            return choice == 'y'
        else:
            print("Please enter 'y' or 'n'.")

def run_backup(source_dirs, dest, use_delete):
    command = [
        "sudo", "rsync", "-aAXvh", "--progress", "--checksum",
        "--no-owner", "--no-group"
    ]
    if use_delete:
        command.append("--delete")

    command += source_dirs + [dest]

    print(f"\n🛰 Running rsync {'with --delete (mirror mode)' if use_delete else '(archive mode)'}...\n")
    try:
        subprocess.run(command, check=True)
        print("✅ Backup completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)

def check_disk_usage(mount_point):
    print(f"\nDisk usage for {mount_point}:")
    subprocess.run(["df", "-h", mount_point])

def main():
    print("=== Backup External SSD Tool ===")

    device = select_partition()
    mount_point = mount_device(device)
    check_disk_usage(mount_point)

    source_dirs = select_source_directories()
    use_delete = ask_delete_option()
    run_backup(source_dirs, mount_point, use_delete)

    check_disk_usage(mount_point)
    unmount_device(mount_point)

if __name__ == "__main__":
    main()
