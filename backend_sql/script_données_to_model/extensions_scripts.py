import os


def check_lock_file(LOCK_FILE):
    return os.path.exists(LOCK_FILE)


def create_lock_file(LOCK_FILE, sys_argv=None):
    """
    Create a lock file with sys.argv information and a URL derived from sys.argv.

    Parameters:
    LOCK_FILE (str): Path to the lock file to create.
    sys_argv (list of str, optional): Arguments to include in the lock file. 
    """
    # Format sys.argv as a string
    if sys_argv is not None and len(sys_argv) > 1:
        argv_info = ' '.join(sys_argv)
        url = sys_argv[1]  # Extract the URL from the second argument
    else:
        argv_info = 'None'
        url = None

    # Write the lock file with sys.argv and URL information
    with open(LOCK_FILE, "w") as lock_file:
        lock_file.write("Locked\n")
        lock_file.write(f"Arguments: {argv_info} \n")
        if url is not None:
            lock_file.write(f"url: http://localhost:8000/{url}\n")



def remove_lock_file(LOCK_FILE):
    os.remove(LOCK_FILE)