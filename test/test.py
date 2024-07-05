import sys
import os
import time
from multiprocessing import Process
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

    def try_lock_task_1():
        num = 1
        lock = LockablePidFile(pidfile_path, lockfile_path, group_name)
        if(lock.acquire()):
            print(f"task {num} got lock")
            time.sleep(300)
            lock.release()
        else:
            print(f"task {num} failed message -  {lock.error_msg}")

    def try_lock_task_2():
        num = 2
        lock = LockablePidFile(pidfile_path, lockfile_path, group_name)
        if(lock.acquire()):
            print(f"task {num} got lock")
            time.sleep(30)
            lock.release()
        else:
            print(f"task {num} failed message -  {lock.error_msg}")


    p1 = Process(target = try_lock_task_1)
    p1.start()
    p2 = Process(target = try_lock_task_2)
    p2.start()
    p1.join()
    p2.join()


main()