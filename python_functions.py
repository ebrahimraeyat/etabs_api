from pathlib import Path
import os, sys

def flatten_list(nested_list):
    return [item for sublist in nested_list for item in (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]

def flatten_set(nested_set):
    return {element for subset in nested_set for element in (flatten_set(subset) if isinstance(subset, set) else {subset})}

def is_text_in_list_elements(
        text_list: list,
        partial_text: str,
        ):
    matching_elements = [text for text in text_list if partial_text in text]
    return len(matching_elements) > 0


def get_exe_path(program_name):
    import subprocess
    try:
        result = subprocess.check_output(['where', program_name], shell=True, text=True)
        return result.strip()
    except subprocess.CalledProcessError:
        return None
    
def get_temp_filepath(suffix='EDB', filename='test') -> Path:
    import tempfile
    temp_path = Path(tempfile.gettempdir())
    temp_file_path = temp_path / f"{filename}.{suffix}"
    return temp_file_path

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])