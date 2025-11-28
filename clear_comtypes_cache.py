import os
import sys
import shutil

def get_next_cache_dir():
    work_dir = os.getcwd()
    try:
        # change working directory to avoid import from local folder
        # during installation process
        os.chdir(os.path.dirname(sys.executable))
        import comtypes.client
        return comtypes.client._code_cache._find_gen_dir()
    except ImportError:
        return None
    finally:
        os.chdir(work_dir)


def _remove(directory):
    shutil.rmtree(directory)
    print('Removed directory "%s"' % directory)


def remove_directory(directory):
    if directory:
        _remove(directory)
    return True


# First iteration may get folder with restricted rights.
# Second iteration always gets temp cache folder (writable for all).
def clear_cache():
    directory = get_next_cache_dir()
    removed = remove_directory(directory)

    if removed:
        directory = get_next_cache_dir()

        # do not request the second confirmation
        # if the first folder was already removed
        remove_directory(directory)
