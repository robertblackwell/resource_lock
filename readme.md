# Pid File

This repo contains a small python module that is intended to allow multiple instances of a program
to lock a resource and in the event that the resurce is already locked to report who has locked the resource.

# Installing

# Usage

Consider a situation where an application wishes to perform an action on an external resource. For example
sending a configuration file to an external device. 

The following points define the situations:

-   there may be multiple instances of the application running at any time for multiple users.

-   only one instance of the application is permitted to try sending to the device at the same time
as there is no locking mechanism in the remote device.

Thus this external device is a resource that cannot be shared.

A mechanism is required to ensure this device is "locked" while one instance of the app sends the
file. 

The basic mechansim is as follows:

-   use the `Linux` advisory locking mechanism `flock`.
-   agree a full path to a file which will be the subjest of an `flock` call. `lockfile_path`
-   agree a full path to a file which will hold the `pid` of the process currently holding the lock. `pidfile_path`
-   agree the Linux group name of all the users allowed to lock the resource. `group_name`

Then the following code segment should be included in the application

```python

pidfile_path = "....."
lockfile_path = "....."
group_name = "...."

lock = LockablePidFile(pidfile_path, lockfile_path, group_name)

if lock.acquire*():
    # the lock is successfully acquired
    send_file_to_remote_device(.....)

    lock.release()
else:
    # failed to acquire lock - print an error message

    print(f"Failed to acquire lock details are : {lock.error_message }")


```