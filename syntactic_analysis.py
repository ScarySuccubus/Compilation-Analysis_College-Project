from objects import Token, SymbolTable

def parser(tokens: list[Token]):
    errors = []
    preproc_lines = {t['line'] for t in tokens if t['type'] == 'PREPROCESSOR'}
    filtered_tokens = [t for t in tokens if t['type'] not in {'COMMENT_LINE', 'COMMENT_BLOCK'} and t['line'] not in preproc_lines]

    pos = 0
    symbol_table = SymbolTable()
    bracket_stack = []

    def synchronize():
        nonlocal pos
        while pos < len(filtered_tokens) and filtered_tokens[pos]['token'] not in {';', '}'}:
            pos += 1
        if pos < len(filtered_tokens):
            pos += 1

    def match(expected_type, expected_value=None) -> bool:
        nonlocal pos
        if pos < len(filtered_tokens):
            token = filtered_tokens[pos]
            if token['type'] == expected_type and (expected_value is None or token['token'] == expected_value):
                if expected_value in {'(', '{', '['}:
                    bracket_stack.append((expected_value, token['line'], token['position']))
                elif expected_value in {')', '}', ']'}:
                    if bracket_stack and {'(': ')', '{': '}', '[': ']'}[bracket_stack[-1][0]] == expected_value:
                        bracket_stack.pop()
                    else:
                        errors.append({
                            'line': token['line'],
                            'position': token['position'],
                            'type': 'SYNTAX_ERROR',
                            'message': f"Unmatched closing bracket '{expected_value}'"
                        })
                pos += 1
                return True
        return False

    def expression() -> bool:
        nonlocal pos
        def primary():
            return match('IDENTIFIER') or match('NUMBER') or (match('PUNCTUATION', '(') and expression() and match('PUNCTUATION', ')'))

        def term():
            nonlocal pos
            if not primary():
                return False
            while pos < len(filtered_tokens) and filtered_tokens[pos]['type'] == 'OPERATOR' and filtered_tokens[pos]['token'] in '*/':
                pos += 1
                if not primary():
                    return False
            return True

        def additive():
            nonlocal pos
            if not term():
                return False
            while pos < len(filtered_tokens) and filtered_tokens[pos]['type'] == 'OPERATOR' and filtered_tokens[pos]['token'] in '+-':
                pos += 1
                if not term():
                    return False
            return True

        def comparison():
            nonlocal pos
            if not additive():
                return False
            while pos < len(filtered_tokens) and filtered_tokens[pos]['type'] == 'OPERATOR' and filtered_tokens[pos]['token'] in ['<', '<=', '>', '>=', '==', '!=']:
                pos += 1
                if not additive():
                    return False
            return True

        return comparison()

    def statement():
        nonlocal pos
        start_pos = pos
        if match('KEYWORD', 'return'):
            if not expression() or not match('PUNCTUATION', ';'):
                errors.append({
                    'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                    'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                    'type': 'SYNTAX_ERROR',
                    'message': "Invalid return statement syntax"
                })
                synchronize()
                return False
            return True

        if match('KEYWORD'):
            var_type = filtered_tokens[pos - 1]['token']
            while True:
                if not match('IDENTIFIER'):
                    errors.append({
                        'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                        'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                        'type': 'SYNTAX_ERROR',
                        'message': "Expected variable name after type"
                    })
                    synchronize()
                    return False
                var_name = filtered_tokens[pos - 1]['token']
                symbol_table.insert(var_name, {'type': var_type, 'used': False}, errors)
                if match('OPERATOR', '=') and not expression():
                    errors.append({
                        'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                        'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                        'type': 'SYNTAX_ERROR',
                        'message': "Invalid assignment expression"
                    })
                    synchronize()
                    return False
                if not match('PUNCTUATION', ','):
                    break
            if not match('PUNCTUATION', ';'):
                errors.append({
                    'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                    'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                    'type': 'SYNTAX_ERROR',
                    'message': "Expected ';' after declaration"
                })
                synchronize()
                return False
            return True

        if match('IDENTIFIER'):
            var_name = filtered_tokens[pos - 1]['token']
            if match('OPERATOR', '='):
                if expression() and match('PUNCTUATION', ';'):
                    symbol_table.insert(var_name, {'type': 'inferred', 'used': True}, errors)
                    return True
                else:
                    errors.append({
                        'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                        'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                        'type': 'SYNTAX_ERROR',
                        'message': "Invalid assignment statement"
                    })
                    synchronize()
                    return False
            elif match('PUNCTUATION', '('):
                while not match('PUNCTUATION', ')'):
                    if not expression():
                        errors.append({
                            'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                            'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                            'type': 'SYNTAX_ERROR',
                            'message': "Invalid function call arguments"
                        })
                        synchronize()
                        return False
                    if not match('PUNCTUATION', ',') and (pos >= len(filtered_tokens) or filtered_tokens[pos]['token'] != ')'):
                        errors.append({
                            'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                            'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                            'type': 'SYNTAX_ERROR',
                            'message': "Expected ',' or ')' in function call"
                        })
                        synchronize()
                        return False
                if not match('PUNCTUATION', ';'):
                    errors.append({
                        'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                        'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                        'type': 'SYNTAX_ERROR',
                        'message': "Expected ';' after function call"
                    })
                    synchronize()
                    return False
                return True
        pos = start_pos
        return False

    def control_structure():
        nonlocal pos
        start_pos = pos
        if match('KEYWORD', 'while') or match('KEYWORD', 'if'):
            if not match('PUNCTUATION', '(') or not expression() or not match('PUNCTUATION', ')') or not match('PUNCTUATION', '{'):
                errors.append({
                    'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                    'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                    'type': 'SYNTAX_ERROR',
                    'message': "Invalid control structure syntax"
                })
                synchronize()
                return False
            while pos < len(filtered_tokens) and not match('PUNCTUATION', '}'):
                if not statement() and not control_structure():
                    synchronize()
                    return False
            return True
        pos = start_pos
        return False

    while pos < len(filtered_tokens):
        if not (control_structure() or statement()):
            errors.append({
                'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                'type': 'SYNTAX_ERROR',
                'message': f"Unexpected token '{filtered_tokens[pos]['token']}'" if pos < len(filtered_tokens) else "Unexpected end of input"
            })
            synchronize()

    if bracket_stack:
        for bracket, line, position in bracket_stack:
            errors.append({
                'line': line,
                'position': position,
                'type': 'SYNTAX_ERROR',
                'message': f"Unmatched opening bracket '{bracket}'"
            })

    if pos < len(filtered_tokens):
        errors.append({
            'type': 'SYNTACTIC_ERROR',
            'message': 'Extra tokens after valid input',
            'line': filtered_tokens[pos]['line'],
            'column': filtered_tokens[pos]['column']
        })

    if errors: 
        return False, symbol_table, errors
    
    return True, symbol_table, errors
