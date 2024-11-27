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

def get_unique_load_combinations(
        data: list,
        sequence_numbering: bool=False,
        prefix : str = 'COMBO',
        suffix : str = '',
        ):
    '''
    it gives a list contain load combinations and return the unique load combinations
    '''
    combos = {}
    for i in range(0, len(data) - 3, 4):
        name = data[i]
        lc = data[i+2]
        sf = data[i+3]
        content = combos.get(name, None)
        if content is None:
            combos[name] = f"{lc} {sf}"
        else:
            combos[name] += f" {lc} {sf}"
    un_combos = {}
    un_combo_list = []
    j = 1
    for comb, content in combos.items():
        name = un_combos.get(content, None)
        if name is None:
            un_combos[content] = comb
            split_content = content.split(" ")
            if sequence_numbering:
                comb = f"{prefix}{j}{suffix}"
                j += 1
            for i in range(0, len(split_content) - 1, 2):
                lc = split_content[i]
                sf = float(split_content[i+1])
                un_combo_list.extend([comb, "Linear Add", lc, sf])
    return un_combo_list
    

def filter_and_sort(elements):
    """
    Filters and sorts a list of floats and bounding ranges.

    Parameters:
    elements (list): A list containing floats and bounding ranges (lists of two floats).

    Returns:
    list: A sorted list of floats and bounding ranges, with floats within any bounding range removed.
    """
    floats = []
    bounds = []
    
    # Separate floats and bounds
    for elem in elements:
        if isinstance(elem, list):
            bounds.append(elem)
        else:
            floats.append(elem)

    # Filter out floats that are within any bounding range
    filtered_floats = []
    for f in floats:
        if not any(b[0] <= f <= b[1] for b in bounds):
            filtered_floats.append(f)
    bounds.sort(key=lambda x: x[0])
    combined_list = filtered_floats + bounds
    sorted_combined = sorted(combined_list, key=lambda x: x[0] if isinstance(x, list) else x)
    return sorted_combined

def rectangle_vertexes(
                       bx,
                       by,
                       center=(0, 0),
                       ):
    dx = bx / 2
    dy = by / 2
    v1 = (center[0] - dx, center[1] - dy)
    v2 = (center[0] + dx, center[1] - dy)
    v3 = (center[0] + dx, center[1] + dy)
    v4 = (center[0] - dx, center[1] + dy)
    return [v1, v2, v3, v4, v1]

def rebar_centers(
    width: float,
    height: float,
    N: int,
    M: int,
    corner_diameter: int,
    longitudinal_diameter: int,
    tie_diameter: int = 10,
    cover: int = 40,
    center=(0, 0),
):
    corners = []
    longitudinals = []
    c = cover + tie_diameter + corner_diameter / 2
    # c1 = cover + tie_diameter + longitudinal_diameter / 2
    b = width - 2 * (cover + tie_diameter) - corner_diameter
    dx = b / (N - 1)
    h = height - 2 * (cover + tie_diameter) - corner_diameter
    dy = h / (M - 1)
    x1 = -width / 2 + c
    y1 = -height / 2 + c
    x2 = width / 2 - c
    y2 = height / 2 - c
    for i in range(N):
        for j in range(M):
            if i in (0, N -1) and j in (0, M - 1):
                x = -width / 2 + (c + i * dx)
                y = -height / 2 + (c + j * dy)
                corners.append((x + center[0], y + center[1]))
                continue
            x = -width / 2 + (c + i * dx)
            y = -height / 2 + (c + j * dy)
            if x1 + 1 < x < x2 - 1 and y1 + 1 < y < y2 - 1:
                continue
            epsilon = (corner_diameter - longitudinal_diameter) / 2
            if i == 0:
                x -= epsilon
            if i == N - 1:
                x += epsilon
            if j == 0:
                y -= epsilon
            if j == M - 1:
                y += epsilon
            longitudinals.append((x + center[0], y + center[1]))
    return corners, longitudinals


