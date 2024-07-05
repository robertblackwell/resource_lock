from genericpath import isfile
import os
import sys
import calendar
import time
import signal
from typing import Union, Tuple
from subprocess import Popen, PIPE
import fcntl
from pprint import pprint
import pwd
import os, pathlib, stat
import pid_file.pidutil as pidutil

# myfpath = __file__
# mydirpath = os.path.dirname(myfpath)
# mypidfile = os.path.join(mydirpath, "pid_file.txt")
# mypid_lockfile = os.path.join(mydirpath, "pid_file.lock")
# pid_file = mypidfile
debug = False
# local_group = "robert"

def open_with_permissions(fpath):
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

class LockFile:
    """
    This class adds an advisory locking facility to a file using the
    linux fcntl.lockf() facility.

    Warning it is only targeted at Linux systems

    This is only a building block for the final pid file mechanism
    """
    def __init__(self, lock_file_path: str, grp_name: str):
        self.fpath = lock_file_path
        self.retry_max = 10
        self.retry_wait_secs = 0.5
        self.file_fd = None
        self.is_locked = False
        self.grp_name = grp_name


    def _open(self):
        """This is a private function - used only by other functions in this class"""
        if self.is_locked:
            raise RuntimeError("LockFile.open is_locked should be false ")
        if self.file_fd is not None:
            raise RuntimeError("LockFile.open file_fp should be None ")

        self.is_locked = False
        self.file_fd = open_with_permissions(self.fpath)
        if self.file_fd is None:
            raise RuntimeError("failed to open lockfile {}".format(self.fpath))

    def _close(self):
        if self.file_fd is None:
            raise RuntimeError("lock file is already closed")

        os.close(self.file_fd)
        self.file_fd = None
        self.is_locked = False

    def try_lock(self, timeout_secs=0) -> bool:
        self._open()
        if timeout_secs == 0:
            timeout_secs = self.retry_wait_secs
        count = 0
        while True:
            try:
                if self.file_fd is None:
                    raise RuntimeError("file_fp is None")
                else:
                    fcntl.lockf(self.file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.is_locked = True
                    return True
            except OSError as e:
                print("lock_file failed count: {}".format(count))
                time.sleep(timeout_secs)
                count += 1
                if count >= self.retry_max:
                    return False

    def unlock(self):
        if self.file_fd is None:
            raise RuntimeError("unlock - lock_file is not open")
        if not self.is_locked:
            raise RuntimeError("lock_file is not locked cannot unlock")
        fcntl.lockf(self.file_fd, fcntl.LOCK_UN)
        os.close(self.file_fd)
        self.file_fd = None
        self.is_locked = False

    def cleanup(self):
        """Called by finalize: to cleanup when things are in an unknown state"""
        print("LockFile.cleanup {}".format(self.fpath))
        if self.file_fd is not None:
            if self.is_locked:
                self.unlock()
            os.close(self.file_fd)
        if os.path.isfile(self.fpath):
            os.remove(self.fpath)
        self.file_fd = None
        self.is_locked = False

class PidEncodedFile:
    """This class provides a facility to read and write process id information into a file
    as a means of indicating which process owns a resource.
    
    In our case the resource is permission to build and send device config files.
    
    This is only a building block for the final pid file mechanism
    """
    def __init__(self, fpath, grp_name):
        self.fpath = fpath
        self.grp_name = grp_name

    def write(self, pid):
        # setPidPerm = 'chown :{} '.format(self.grp_name) + self.fpath
        fd = open_with_permissions(self.fpath)
        fo = os.fdopen(fd, "w+")
        fo.write(str(pid))
        fo.close()
        # Popen(setPidPerm, shell=True, stdout=PIPE)


    def read(self) -> Tuple[str, float, Union[str, None]]:

        # def user_from_pid(pid) -> Union[str, None]:
        #     """
        #     Example of an internal function - function inside a function.
        #     Keeps this function private and allows the use of a simpler name
        #     """
        #     proc_dir = "/proc/{}".format(pid)
        #     if os.path.isdir(proc_dir):
        #         proc_stat_file = os.stat(proc_dir)
        #         # get UID via stat call
        #         uid = proc_stat_file.st_uid
        #         # look up the username from uid
        #         username = pwd.getpwuid(uid)[0]
        #         return username
        #     return None

        pid_time=float(calendar.timegm(time.gmtime())  -  os.path.getmtime(self.fpath))
        fp = open(self.fpath,'r')
        pid_num = fp.readline()
        usr = pidutil.user_from_pid(pid_num)
        fp.close()
        return pid_num, pid_time, usr

    def cleanup(self):
        # print("PidEncodedFile.cleanup")
        if os.path.isfile(self.fpath):
            os.remove(self.fpath)

class LockablePidFile:
    """This is the final mechanism for protecting a resource via an advisory lock
    in a way that the pid of the owner is known to others who would like the resource
    
    This class combines LockableFile with PidEncodeFile.

    Note that means 2 file
     
    * one which is locked and unlocked 
    * one which contains the Pid information

    This mechaism can be broken by abort signals so be sure to call `setup_handlers()`
    lower down in this file
    """
    def __init__(self, pid_file_path, pid_lock_file_path, grp_name: str):
        self.pid_file_path = pid_file_path
        self.pid_lock_file_path = pid_lock_file_path
        self.grp_name = grp_name
        self.lock_file = LockFile(pid_lock_file_path, grp_name)
        self.pid_encoded_file = PidEncodedFile(pid_file_path, grp_name) 

    def acquire(self):

        pid = os.getpid()
        result = False
        # lock_file.open()
        if self.lock_file.try_lock():
            if os.path.isfile(self.pid_file_path):
                pid_num, pid_time, user = self.pid_encoded_file.read()
                if user is not None:
                    if debug:
                        print("acquire: user is NOT None PID: {}".format(os.getpid()))
                    result = False
                    self.error_msg = 'The script is in use by user:[' + user +'] pid:['+ str(pid) + ']. Please wait a few minutes before trying to run the script again.'
                else:
                    if debug: 
                        print("acquire: user is None PID: {}".format(os.getpid()))
                    self.pid_encoded_file.write(pid)
                    result = True
            else:
                if debug:
                    print("acquire: Pid file does not exist PID: {}".format(os.getpid()))
                self.pid_encoded_file.write(pid)
                result = True
            self.lock_file.unlock()
            return result
        else:
            self.error_msg = 'Failed to get pid file lock - someone is hogging the file.'
            self.lock_file.unlock()
            return False


    def release(self):
        # lock_file.open()
        if self.lock_file.try_lock():
            if os.path.isfile(self.pid_file_path):
                os.unlink(self.pid_file_path)
        else:
            raise RuntimeError('\nrelease - Failed to get pid file lock - some one is hogging the file.')
        self.lock_file.unlock()

    def cleanup(self):
        self.lock_file.cleanup()
        self.pid_encoded_file.cleanup()

def keyboard_handler(a, b):
    print("keyboard handler")
    sys.exit()
def term_handler(a, b):
    print("term handler")
    sys.exit()
def setup_handlers():
    signal.signal(signal.SIGTERM,term_handler)
    signal.signal(signal.SIGINT, keyboard_handler)

