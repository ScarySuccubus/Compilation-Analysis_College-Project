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
        str_list.append(
            f'{item.get('type')}: {item.get('message')} '
            f'at line {item.get('line')}, position {item.get('position')}.'
        )
    return '\n'.join(str_list)