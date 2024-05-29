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
    
def get_temp_filepath(suffix='EDB', filename='test', random=False) -> Path:
    import tempfile
    if random:
        return Path(tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=True).name)
    temp_path = Path(tempfile.gettempdir())
    temp_file_path = temp_path / f"{filename}.{suffix}"
    return temp_file_path

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

def change_unit(force=None, length=None):
    def decorator(original_method):
        def wrapper(self, *args, **kwargs):
            # Get the unit from etabs
            curr_force, curr_length = self.etabs.get_current_unit()
            force_to_use = force if force is not None else curr_force
            length_to_use = length if length is not None else curr_length
            self.etabs.set_current_unit(force_to_use, length_to_use)

            # Call the original method
            result = original_method(self, *args, **kwargs)

            # Set the unit back in etabs
            self.etabs.set_current_unit(curr_force, curr_length)

            return result

        return wrapper
    return decorator

def has_attribs(
        obj,
        attribs: list,
        function=any   # all
        ):
    return function(hasattr(obj, attr) for attr in attribs)
    
