"""This script keeps files on the pyboard in sync with a directory on your
computer."""
import argparse
import os
import shutil
import time

import serial
import watchdog.observers
import watchdog.events


def parse_args():
    """These are the script arguments."""
    parser = argparse.ArgumentParser(
        description="Watch a directory and flash the pyboard"
    )
    parser.add_argument(
        "path",
        help="The path to watch",
        default="."
    )
    parser.add_argument(
        "drive",
        help="The drive letter of the pyboard"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="If set, all actions are logged to the console (default=TRUE)",
        default=True
    )
    parser.add_argument(
        "-r",
        "--reboot",
        action="store_true",
        help="If set, soft reboot board on save (default=TRUE)",
        default=True
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Serial port for the pyboard (e.g. COM4)"
    )
    parser.add_argument(
        "-m",
        "--main",
        help="Main file referenced by boot.py (typically main.py)",
        default="main.py"
    )
    return parser.parse_args()


class PyboardSync(watchdog.events.FileSystemEventHandler):
    """Uploads new files to the pyboard when they are changed in the
    source directory."""
    def __init__(
            self,
            args
    ):
        """Uploads new files to the pyboard when they are changed in the
        source directory."""
        self.path = args.path
        self.drive = args.drive
        self.verbose = args.verbose
        self.reboot = args.reboot
        self.port = args.port
        self.main_file = args.main

        if self.reboot and not self.port:
            raise Exception("Port must be set when using reboot mode")

        self.print_if_verbose("Watching files")


    def get_drive_path(self, src_path):
        """Get the path on the Pyboard drive given the input path"""
        real_path = src_path.replace(self.path, '')
        if real_path[0] == "\\" or real_path[0] == "/":
            real_path = real_path[1:]
        return f"{self.drive}:{real_path}"


    def print_if_verbose(self, string: str):
        """Print a message if the -v/--verbose flag has been set"""
        if self.verbose:
            print(string)


    def reboot_board(self):
        """Soft reboot the pyboard to load the new code."""
        # Initiate serial communication
        com = serial.Serial(self.port, 115200, timeout=1)

        self.print_if_verbose("Soft rebooting board")

        # Send ETX a.k.a. Ctrl+C a.k.a. ^C to interrupt running code and launch
        # interactive shell
        com.write("\x03".encode())
        time.sleep(0.1)

        # Then send EOT a.k.a. Ctrl+D a.k.a ^D to soft reboot the board and
        # reload all the code.
        com.write("\x04".encode())
        time.sleep(0.1)

        # Close port
        com.close()

        self.print_if_verbose("Soft rebooting complete")


    def upload_file(self, src_path: str, retries: int):
        """Upload or overwrite a file on the pyboard."""
        try:
            drive_path = self.get_drive_path(src_path)
            if self.main_file in src_path:
                self.print_if_verbose(f"Removing {self.main_file}")
                os.remove(drive_path)
            shutil.copyfile(src_path, drive_path)
            if self.reboot:
                self.reboot_board()
        except OSError:
            if retries > 0:
                self.print_if_verbose("Failed to upload. Retrying in a second.")
                time.sleep(1)
                self.upload_file(src_path, retries-1)
            else:
                self.print_if_verbose("Maximum retries exceeded. "
                                      "If you have an open REPL session, "
                                      "please close it or send Ctrl+C to continue.")


    def delete_file(self, src_path: str, retries: int):
        """Delete a file on the pyboard."""
        try:
            drive_path = self.get_drive_path(src_path)
            os.remove(drive_path)
            if self.reboot:
                self.reboot_board()
        except OSError:
            if retries > 0:
                self.print_if_verbose("Failed to upload. Retrying in a second.")
                time.sleep(1)
                self.upload_file(src_path, retries-1)
            else:
                self.print_if_verbose("Maximum retries exceeded. "
                                      "If you have an open REPL session, "
                                      "please close it or send Ctrl+C to continue.")


    def on_modified(self, event):
        """Called when a file or directory is modified."""
        self.print_if_verbose(
            "Modifying file at " + self.get_drive_path(event.src_path)
        )
        self.upload_file(event.src_path, retries=4)


    def on_created(self, event):
        """Called when a file or directory is created."""
        self.print_if_verbose(
            "Creating file at " + self.get_drive_path(event.src_path)
        )
        self.upload_file(event.src_path, retries=4)


    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        self.print_if_verbose(
            "Deleting file at " + self.get_drive_path(event.src_path)
        )
        self.delete_file(event.src_path, retries=4)


def main():
    """Update the pyboard whenever a file changes"""
    args = parse_args()
    observer = watchdog.observers.Observer()
    observer.schedule(
        event_handler=PyboardSync(args),
        path=args.path,
        recursive=True
    )
    observer.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
