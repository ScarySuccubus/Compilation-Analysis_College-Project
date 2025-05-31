import re
from typing import TypedDict

UNKNOWN = 'UNKNOWN'

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
