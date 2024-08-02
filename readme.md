# Pid File

This repo contains a small python module that is intended to allow multiple instances of a program
to lock a resource and in the event that the resurce is already locked to report who has locked the resource.

# Installing 

I have recently added the `resource_lock` project to __pypi__. As a result the module can be installed with

```bash
cd to your project folder
source venv/bin/activate
python3 -m pip install resource_lock
```

# Installing - backdoor way

Without using __pypi__ the simplest way to install this module into a project is:

```bash

cd .../Projects/my_project
cd ..
git clone git@github.com:robertblackwell/resource_lock.git
cd ../my_project
source ./env/bin/activate
pip install ../resource_lock

```

Where yout python project that wants to use `resource_lock` resides in `.../Projects/my_project` 

The repo `github.com:robertblackwell/resource_lock_example` demonstrates this

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
-   provide a globally unique name for the resource to be protected `resource_name`
-   provide a path to a directory in which a lock file and pid file will be created
-   derive the name of the lock file as `f"{resource_name}.lock"`
-   derive the name of the pid file as `f"{resource_name}.pid"`
-   apply `flock` to the lock file and 
    -   if successful write the process  pid into the pid file
    -   if `flock` failed read the pid of the holder of the lock from the pid file and use that pid to get the user name of the lock holder
  
Then the following code segment demonstrates how to use this module

```python

from resource_lock.resource_lock import ResourceLock

resource_name = "....."
lockfile_dir_path = "....."

lock = ResourceLock(resource_name, lockfile_dir_path)

token = lock.acquire():
if token is not None:
    # the lock is successfully acquired
    send_file_to_remote_device(.....)
    # or whatever other stuff you need to do here

    lock.release(token)
else:
    # failed to acquire lock - print an error message

    print(f"Failed to acquire lock details are : {lock.error_msg}")


```
