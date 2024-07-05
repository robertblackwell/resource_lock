import os
import pwd
import grp
from typing import Union

def get_groupname_from_pid(pid) -> Union[str, None]:
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

def user_from_pid(pid) -> Union[str, None]:
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


def derive_lockfile_path(pid_file_path):
    d = os.path.dirname(pid_file_path)
    bn, ext = os.path.splitext(os.path.basename(pid_file_path))
    lock_path = os.path.join(d, "{}{}".format(bn, ".lock"))
    return lock_path
