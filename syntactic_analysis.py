from objects import Token, SymbolTable

def parser(tokens: list[Token]):
    errors = []

    # Collect lines that contain preprocessor directives
    preproc_lines = {t['line'] for t in tokens if t['type'] == 'PREPROCESSOR'}

    # Remove comments and lines with preprocessor directives
    filtered_tokens = [
        t for t in tokens
        if t['type'] not in {'COMMENT_LINE', 'COMMENT_BLOCK'} and t['line'] not in preproc_lines
    ]

    pos = 0
    symbol_table = SymbolTable()
    bracket_stack = []

    # Skips to next statement end on error
    def synchronize():
        nonlocal pos
        while pos < len(filtered_tokens) and filtered_tokens[pos]['token'] not in {';', '}'}:
            token = filtered_tokens[pos]
            if token['type'] == 'PUNCTUATION' and token['token'] in {')', '}', ']'}:
                match('PUNCTUATION', token['token'])  # Trigger bracket check
            else:
                pos += 1
        if pos < len(filtered_tokens):
            pos += 1

    # Match a token by type and optionally by exact value
    def match(expected_type, expected_value=None) -> bool:
        nonlocal pos
        if pos < len(filtered_tokens):
            token = filtered_tokens[pos]
            if token['type'] == expected_type and (expected_value is None or token['token'] == expected_value):

                # Track opening brackets
                if expected_value in {'(', '{', '['}:
                    bracket_stack.append((expected_value, token['line'], token['position']))
                # Track and verify closing brackets
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

    # Parses an expression with recursive precedence levels
    def expression() -> bool:
        nonlocal pos

        def primary():
            return (
                match('IDENTIFIER') or
                match('NUMBER') or
                (match('PUNCTUATION', '(') and expression() and match('PUNCTUATION', ')'))
            )

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

    # Parses a single statement or declaration
    def statement():
        nonlocal pos
        start_pos = pos

        # Handle return statements
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

        # Handle variable declarations
        if match('KEYWORD'):  # Type or 'const'
            var_type = filtered_tokens[pos - 1]['token']
            is_const = False

            if var_type == 'const':
                is_const = True
                if not match('KEYWORD'):
                    errors.append({
                        'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                        'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                        'type': 'SYNTAX_ERROR',
                        'message': "Expected type after 'const'"
                    })
                    synchronize()
                    return False
                var_type = filtered_tokens[pos - 1]['token']

            while True:
                # Expect variable name
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
                attributes = {
                    'type': var_type,
                    'used': False,
                    'initialized': False,
                    'const': is_const
                }

                # Optional initialization
                if match('OPERATOR', '='):
                    if not expression():
                        errors.append({
                            'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                            'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                            'type': 'SYNTAX_ERROR',
                            'message': "Invalid assignment expression"
                        })
                        synchronize()
                        return False
                    attributes['initialized'] = True

                symbol_table.insert(var_name, attributes, errors)

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

        # Handle assignments or function calls
        if match('IDENTIFIER'):
            var_name = filtered_tokens[pos - 1]['token']
            if match('OPERATOR', '='):
                if expression() and match('PUNCTUATION', ';'):
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

            elif match('PUNCTUATION', '('):  # Function call
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

    # Parses if/while control structures with block bodies
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

            # Parse block body
            while pos < len(filtered_tokens) and not match('PUNCTUATION', '}'):
                if not statement() and not control_structure():
                    synchronize()
                    return False
            return True

        pos = start_pos
        return False

    # Main parsing loop
    while pos < len(filtered_tokens):
        token = filtered_tokens[pos]

        # Detect unmatched closing brackets early
        if token['type'] == 'PUNCTUATION' and token['token'] in {')', '}', ']'}:
            match('PUNCTUATION', token['token'])
            continue

        if not (control_structure() or statement()):
            errors.append({
                'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                'type': 'SYNTAX_ERROR',
                'message': f"Unexpected token '{filtered_tokens[pos]['token']}'" if pos < len(filtered_tokens) else "Unexpected end of input"
            })
            synchronize()

    # Add unmatched opening brackets to errors
    for bracket, line, position in bracket_stack:
        errors.append({
            'line': line,
            'position': position,
            'type': 'SYNTAX_ERROR',
            'message': f"Unmatched opening bracket '{bracket}'"
        })

    # Extra token(s) at end
    if pos < len(filtered_tokens):
        errors.append({
            'type': 'SYNTAX_ERROR',
            'message': 'Extra tokens after valid input',
            'line': filtered_tokens[pos]['line'],
            'position': filtered_tokens[pos]['position']
        })

    return (False, symbol_table, errors) if errors else (True, symbol_table, errors)
