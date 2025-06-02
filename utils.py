def separate_errors(dict_list):
    """Separates dictionaries into errors and non-errors based on 'type' field"""
    errors = []
    for item in dict_list:
        if isinstance(item.get('type'), str) and 'error' in item['type'].lower():
            errors.append(item)

    return errors

def print_clean(dict_list):
    str_list = []
    for item in dict_list:
        if isinstance(item, dict):
            str_list.append(
                f'{item.get('type')}: {item.get('message')} '
                f'at line {item.get('line')}, position {item.get('position')}.'
            )
        elif isinstance(item, str):
            str_list.append(item)
    return '\n'.join(str_list)