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
sys.path.insert(1, os.path.join(project_dir, "resource_lock"))

from resource_lock.resource_lock import ResourceLock                

    

def main():
    lockfile_path = "./lockfile" 
    pidfile_path = "pidfile"
    resource_name = "test_resource"
    lockfile_dir = os.path.dirname(__file__)

    def try_lock_task_1():
        num = 1
        lock = ResourceLock(resource_name, lockfile_dir)
        lockfd = lock.acquire()
        if(lockfd is not None):
            print(f"task {num} got lock")
            time.sleep(300)
            lock.release(lockfd)
        else:
            print(f"task {num} failed message -  {lock.error_msg}")

    def try_lock_task_2():
        num = 2
        lock = ResourceLock(resource_name, lockfile_dir)
        lockfd = lock.acquire()
        if(lockfd is not None):
            print(f"task {num} got lock")
            time.sleep(300)
            lock.release(lockfd)
        else:
            print(f"task {num} failed message -  {lock.error_msg}")


    p1 = Process(target = try_lock_task_1)
    p1.start()
    p2 = Process(target = try_lock_task_2)
    p2.start()
    p1.join()
    p2.join()


main()