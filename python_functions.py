

def flatten_list(nested_list):
    return [item for sublist in nested_list for item in (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]

def is_text_in_list_elements(
        text_list: list,
        partial_text: str,
        ):
    matching_elements = [text for text in text_list if partial_text in text]
    return len(matching_elements) > 0