import re
from typing import TypedDict

UNKNOWN = 'UNKNOWN'

# --- Symbol Table ---
class SymbolTable:
    def __init__(self):
        self.table = {}

    def insert(self, name, attributes, errors):
        if name in self.table:
            errors.append(f"Semantic Error: Redeclaration of variable '{name}'.")
        else:
            self.table[name] = attributes

    def lookup(self, name):
        return self.table.get(name, None)

    def mark_used(self, name):
        if name in self.table:
            self.table[name]['used'] = True

    def undeclared_variables(self, used_symbols):
        return [s for s in used_symbols if s not in self.table]

    def unused_variables(self):
        return [name for name, attr in self.table.items() if not attr.get('used', False)]

    def dump(self):
        # Optional: Could convert to string or dict if needed
        return {name: info for name, info in self.table.items()}


def get_token_type(token):
    token_types = [
        {'regex': r'\s+', 'type': 'WHITESPACE'},
        {'regex': r'/\*[\s\S]*?\*/', 'type': 'COMMENT_BLOCK'},
        {'regex': r'//.*', 'type': 'COMMENT_LINE'},
        {'regex': r'\d+\.\d+|\d+', 'type': 'NUMBER'},
        {'regex': r'#(include|define|ifdef|ifndef|endif|else|elif|pragma)\b', 'type': 'PREPROCESSOR'},
        {'regex': r'\b0x[0-9a-fA-F]+\b', 'type': 'HEX'},
        {'regex': r"'.'", 'type': 'CHAR'},
        {'regex': r'"([^"\\]|\\.)*"', 'type': 'STRING'},
        {'regex': r'\b(auto|break|case|char|const|continue|default|do|double|else|enum'
                  r'|extern|float|for|goto|if|int|long|register|return|short|signed'
                  r'|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile'
                  r'|while|_Bool|_Complex|_Imaginary)\b', 'type': 'KEYWORD'},
        {'regex': r'[a-zA-Z_][a-zA-Z0-9_]*', 'type': 'IDENTIFIER'},
        {'regex': r'[{}()\[\];,:.\'"]', 'type': 'PUNCTUATION'},  # AFTER NUMBER!
        {'regex': r'[+\-*/=<>!&|]', 'type': 'OPERATOR'},
    ]
    for t in token_types:
        if re.fullmatch(t['regex'], token):
            return t['type']
    return UNKNOWN


def lexer(code):
    token_types = [
        ('WHITESPACE', r'\s+'),
        ('COMMENT_BLOCK', r'/\*[\s\S]*?\*/'),
        ('COMMENT_LINE', r'//.*'),
        ('NUMBER', r'\d+\.\d+|\d+'),
        ('PREPROCESSOR', r'#(include|define|ifdef|ifndef|endif|else|elif|pragma)\b'),
        ('HEX', r'\b0x[0-9a-fA-F]+\b'),
        ('CHAR', r"'.'"),
        ('STRING', r'"([^"\\]|\\.)*"'),
        ('KEYWORD', r'\b(auto|break|case|char|const|continue|default|do|double|else|enum'
                    r'|extern|float|for|goto|if|int|long|register|return|short|signed'
                    r'|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile'
                    r'|while|_Bool|_Complex|_Imaginary)\b'),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('PUNCTUATION', r'[{}()\[\];,:.\'"]'),
        ('OPERATOR', r'[+\-*/=<>!&|]'),
    ]

    combined_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_types)
    token_regex = re.compile(combined_regex)

    tokens = []
    errors = []
    for lineno, text in enumerate(code.splitlines()):
        pos = 0
        while pos < len(text):
            match = token_regex.match(text, pos)
            if not match:
                errors.append({
                    'line': lineno,
                    'position': pos,
                    'type': 'LEXICAL_ERROR',
                    'message': f"Unrecognized character '{text[pos]}'"
                })
                pos += 1
                continue

            type_ = match.lastgroup
            value = match.group()
            if type_ != 'WHITESPACE':
                tokens.append({
                    'line': lineno,
                    'position': pos,
                    'type': type_,
                    'token': value
                })
            pos = match.end()
    return tokens, errors


class Token(TypedDict):
    line: int
    position: int
    type: str
    token: str


def parser(tokens: list[Token]):
    errors = []
    preproc_lines = {t['line'] for t in tokens if t['type'] == 'PREPROCESSOR'}
    filtered_tokens = [t for t in tokens if t['type'] not in {'COMMENT_LINE', 'COMMENT_BLOCK'} and t['line'] not in preproc_lines]

    pos = 0
    symbol_table = SymbolTable()

    def match(expected_type, expected_value=None) -> bool:
        nonlocal pos
        if pos < len(filtered_tokens):
            if filtered_tokens[pos]['type'] == expected_type and (expected_value is None or filtered_tokens[pos]['token'] == expected_value):
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
                        return False
                    if not match('PUNCTUATION', ',') and (pos >= len(filtered_tokens) or filtered_tokens[pos]['token'] != ')'):
                        errors.append({
                            'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                            'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                            'type': 'SYNTAX_ERROR',
                            'message': "Expected ',' or ')' in function call"
                        })
                        return False
                if not match('PUNCTUATION', ';'):
                    errors.append({
                        'line': filtered_tokens[pos]['line'] if pos < len(filtered_tokens) else -1,
                        'position': filtered_tokens[pos]['position'] if pos < len(filtered_tokens) else -1,
                        'type': 'SYNTAX_ERROR',
                        'message': "Expected ';' after function call"
                    })
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
                return False
            while pos < len(filtered_tokens) and not match('PUNCTUATION', '}'):
                if not statement() and not control_structure():
                    return False
            return True
        pos = start_pos
        return False

    while pos < len(filtered_tokens):
        if not (control_structure() or statement()):
            errors.append({
                'line': filtered_tokens[pos]['line'],
                'position': filtered_tokens[pos]['position'],
                'type': 'SYNTAX_ERROR',
                'message': f"Unexpected token '{filtered_tokens[pos]['token']}'"
            })
            return False, symbol_table, errors
    return True, symbol_table, errors


def semantic_analyzer(tokens: list[Token], symbol_table: SymbolTable):
    errors = []
    warnings = []
    has_error = False
    used_symbols = set()
    is_rhs = False

    for token in tokens:
        if token['type'] == 'OPERATOR' and token['token'] == '=':
            is_rhs = True
        elif token['type'] == 'PUNCTUATION' and token['token'] == ';':
            is_rhs = False
        elif is_rhs and token['type'] == 'IDENTIFIER':
            used_symbols.add(token['token'])
            symbol_table.mark_used(token['token'])

    for symbol in symbol_table.undeclared_variables(used_symbols):
        errors.append(f"Semantic Error: Variable '{symbol}' not declared.")
        has_error = True

    for symbol in symbol_table.unused_variables():
        warnings.append(f"Warning: Variable '{symbol}' declared but never used.")

    return not has_error, errors, warnings, symbol_table.dump()
