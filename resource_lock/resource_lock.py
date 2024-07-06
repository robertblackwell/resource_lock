from genericpath import isfile
import os
import sys
import calendar
import time
import signal
from typing import Union, Tuple, List
from subprocess import Popen, PIPE
import fcntl
from pprint import pprint
import pwd, grp, getpass
import os, pathlib, stat

debug = False

def get_groupname_from_pid(pid: int) -> Union[str, None]:
    # the /proc/PID is owned by process creator
    proc_fpath = "/proc/{}".format(pid)
    exists = os.path.isdir(proc_fpath)
    if exists:
        proc_stat_file = os.stat("/proc/%d" % pid)
        # get UID via stat call
        uid = proc_stat_file.st_uid
        gid = proc_stat_file.st_gid
        # look up the username from uid
        username = pwd.getpwuid(uid)[0]
        groupname = grp.getgrgid(gid)[0]
        return groupname
    return None

def user_from_pid(pid: int) -> Union[str, None]:
    """
    Example of an internal function - function inside a function.
    Keeps this function private and allows the use of a simpler name
    """
    proc_dir = "/proc/{}".format(pid)
    if os.path.isdir(proc_dir):
        proc_stat_file = os.stat(proc_dir)
        # get UID via stat call
        uid = proc_stat_file.st_uid
        # look up the username from uid
        username = pwd.getpwuid(uid)[0]
        return username
    return None


def get_all_users_groups()->List[str]:
    user = getpass.getuser()
    groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
    return groups

def open_with_permissions(fpath) -> int:
    """
    Should perhaps be called create_with_permissions.
    
    If the paths does not exists as a file create it and change its permissions
    to ugo=rwx

    return an fd
    """
    if not os.path.isfile(fpath):
        pathlib.Path(fpath).touch(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        os.chmod(fpath, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    return os.open(fpath, os.O_RDWR | os.O_CREAT | os.O_TRUNC)


def write_pid(filepath: str, pid: int):
    fd = open_with_permissions(filepath)
    fo = os.fdopen(fd, "w+")
    fo.write(str(pid))
    fo.close()

def read_piddata(filepath: str) -> Tuple[str, float, Union[str, None]]:
    pid_time=float(calendar.timegm(time.gmtime())  -  os.path.getmtime(filepath))
    fp = open(filepath,'r')
    pid_num = fp.readline()
    usr = user_from_pid(int(pid_num))
    fp.close()
    return pid_num, pid_time, usr


class ResourceLock:
    """This is a mechanism for protecting a resource via an advisory lock
    in a way that the pid of the owner is known to others who would like the resource
    
    Note that means 2 file
     * resource_name is a globally unique name for the resource to be protected
     * lockfile_dir is the directory in which the lockfile and pidfile will be created

    * lock_file_path - the path to the lock file. Derived as `resource_name.lock` 
    * pid_file_path  - the path to the file into which the holder of the lock puts its pid
    *                   this is derived from the resource_name as `resource_name.pid`
    
    This mechaism can be broken by abort signals so be sure to call `setup_handlers()`
    lower down in this file

    """
    def __init__(self, resource_name, lockfile_dir, retry_count=5, retry_interval_secs=1):
        d = os.path.realpath(lockfile_dir)
        lock_file_path = os.path.join(d, f"{resource_name}.lock")
        pid_file_path = os.path.join(d, f"{resource_name}.pid")
        self.pid_file_path = pid_file_path
        self.lock_file_path = lock_file_path
        self.lock_file_fd = None
        self.error_msg = ""
        self.retry_count = retry_count
        self.retry_interval_secs = retry_interval_secs

    def acquire(self) -> int | None:
        """Returns int on success and None on failure"""
        open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        fd = os.open(self.lock_file_path, open_mode)

        pid = os.getpid()
        lock_file_fd = None
        
        timeout = self.retry_interval_secs * self.retry_count
        start_time = current_time = time.time()
        while current_time < start_time + timeout:
            try:
                # The LOCK_EX means that only one process can hold the lock
                # The LOCK_NB means that the fcntl.flock() is not blocking
                # and we are able to implement termination of while loop,
                # when timeout is reached.
                # More information here:
                # https://docs.python.org/3/library/fcntl.html#fcntl.flock
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                write_pid(self.pid_file_path, pid)
                # self.pid_encoded_file.write(pid)
            except (IOError, OSError):
                # pid_num, pid_time, user = self.pid_encoded_file.read()
                pid_num, pid_time, user = read_piddata(self.pid_file_path)
                self.error_msg = f"failed to get lock help by pid: {pid_num} pid_time: {pid_time} user: {user}"
            else:
                lock_file_fd = fd
                break
            print(f'  {pid} waiting for lock')
            time.sleep(self.retry_interval_secs)
            current_time = time.time()
        if lock_file_fd is None:
            os.close(fd)
        return lock_file_fd

    def release(self, lockfile_fd):
        # Do not remove the lockfile:
        #
        #   https://github.com/benediktschmitt/py-filelock/issues/31
        #   https://stackoverflow.com/questions/17708885/flock-removing-locked-file-without-race-condition
        fcntl.flock(lockfile_fd, fcntl.LOCK_UN)
        os.close(lockfile_fd)
        return None

def keyboard_handler(a, b):
    print("keyboard handler")
    sys.exit()
def term_handler(a, b):
    print("term handler")
    sys.exit()
def setup_handlers():
    signal.signal(signal.SIGTERM,term_handler)
    signal.signal(signal.SIGINT, keyboard_handler)

