import sys
import os
print(sys.path)

print(f"{os.path.realpath(__file__)}")
print(f"{os.path.realpath(os.path.dirname(__file__))}")
print(f"{os.path.realpath(os.path.dirname(os.path.dirname(__file__)))}")
project_dir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_dir)
sys.path.insert(1, os.path.join(project_dir, "pid_file"))

from pid_file.lockable_pid_file import LockablePidFile                

def main():
    lockfile_path = "./lockfile" 
    pidfile_path = "pidfile"
    group_name = "everyone"

    lock = LockablePidFile(pidfile_path, lockfile_path, group_name)

    if(lock.acquire()):
        print("got lock")
        x = lock.acquire()
        lock.release()
    else:
        print(f"{lock.error_message}")

    print(f"lockfile: {lockfile_path} pidfile: {pidfile_path}  group_name: {group_name}")

main()