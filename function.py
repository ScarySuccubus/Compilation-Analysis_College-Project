UNKNOWN = 'UNKNOWN'

import re

def clean_string(text):
  new_string = ''.join(char for char in text if char.isalnum() or char == ' ')
  return new_string


def split_token(text):
  tokens = re.findall(r'\w+|\S', text)
  response = []
  for token in tokens:
    response.append({'token': token, 'type': get_token_type(token)})
  return response


def try_n_catch (text):
    test = get_token_type(text) # tries the entire line in case of comments
    if test != UNKNOWN:
        return {'token': text, 'type': test}
    if text[0] in ["'", '"']: # to get full strings
        quote_char = text[0]
        match = re.match(fr'^{re.escape(quote_char)}.*?{re.escape(quote_char)}', text)
        match = match.group(0)
        test = get_token_type(match)
        if test != UNKNOWN:
            return {'token': match, 'type': test}
    parts = re.findall(r'\w+|\S', text)
    # tests symbol+text combos like #define or malloc(
    if len(parts) > 1 and (not parts[0].isalnum() or not parts[1].isalnum()):
        part = parts[0] + parts[1]
        test = get_token_type(part)
        if test != UNKNOWN:
            return {'token': part, 'type': test}
    # last chance
    test = get_token_type(parts[0])
    return {'token': parts[0], 'type': test}

def get_token_type(token):
  token_types = [
      {'regex': r'\s+', 'type': 'WHITESPACE'},
      {'regex': r'/\*[\s\S]*?\*/', 'type': 'COMMENT BLOCK'},
      {'regex': r'\b\d+(\.\d+)?\b', 'type': 'NUMBER'},
      # SPECIFICS FOR PYTHON
      # {'regex': r'#.*', 'type': 'COMMENT LINE'},
      # {'regex': r'\b(?:else|try|finally)\b', 'type': 'CONTROLLER'},
      # {'regex': r'\b(?:print|len|type|input|int|float|str|bool|abs|sum|min|max|round|list'
      #           r'|tuple|dict|set|range|enumerate|zip|sorted|\.split|\.join|\.replace|\.find'
      #           r'|\.lower|\.upper|\.strip|open|\.read|\.write|\.close|map|filter|\.append'
      #           r'|\.pop|\.remove|\.sort|\.index|\.get)\b', 'type': 'FUNCTION'},
      # {'regex':r'\b(?:auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while|_Bool|_Complex|_Imaginary)\b',
      #  'type': 'KEYWORD'},
      # {'regex': r'\b(?:break|continue|pass|return)\b', 'type': 'STATEMENT'},
      #
      # SPECIFICS FOR C
      {'regex': r'//.*', 'type': 'COMMENT LINE'},
      {'regex': r'\b(auto|break|case|char|const|continue|default|do|double|else|enum'
                r'|extern|float|for|goto|if|int|long|register|return|short|signed'
                r'|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile'
                r'|while|_Bool|_Complex|_Imaginary)\b', 'type': 'KEYWORD'},
      {'regex': r'^\s*#\s*(include|define|ifdef|ifndef|endif|else|elif|pragma)\b',
       'type': 'PREPROCESSOR'},
      {'regex': r'\b0x[0-9a-fA-F]+\b', 'type': 'HEX'},
      {'regex': r"'.'", 'type': 'CHAR'},
      {'regex': r'[a-zA-Z_][a-zA-Z0-9_]*', 'type': 'IDENTIFIER'},
      {'regex': r'"([^"\\]|\\.)*"', 'type': 'STRING'},
      # {'regex': r"'([^'\\]|\\.)*'", 'type': 'STRING'},
      {'regex': r'''[{}()\[\];,:.'"]''', 'type': 'PUNCTUATION'},
      {'regex': r'[+\-*/=<>!&|]', 'type': 'OPERATOR'}
  ]

  for token_type in token_types:
      if re.fullmatch(token_type['regex'], token):
          return token_type['type']
  return UNKNOWN


def lexer(code):
    code = code.split('\n')
    tokens = []
    position = 0
    line = 0

    while line < len(code):
        if position >= len(code[line]):
            line += 1
            position = 0
            continue

        if code[line][position].isspace():
            position += 1
            continue

        else:
            snippet = try_n_catch(code[line][position:])
            #snippet = snippet[0]
            if snippet['type'] != UNKNOWN:
                tokens.append({"line": line, "position": position,
                   "type": snippet['type'], "token": snippet['token']})
            else:
                tokens.append({"line": line, "position": position,
                "type": 'ERROR: UNEXPECTED CHARACTER', "token": snippet['token']})
                print(f"Lexical Error: Invalid character '{snippet['token']}'"
                f" at line {line}, position {position}.")
            position += len(snippet['token'])
            continue

    return tokens

from typing import TypedDict

# TypedDict for tokens used in parsing and semantic analysis
class Token(TypedDict):
    line: int
    position: int
    type: str
    token: str


# --- Syntactic Analysis ---
def parser(tokens: list[Token]):
    """
    Parses tokens to check syntax correctness.
    Filters out comments and preprocessor directives before parsing.
    Returns (True, symbols) if successful, else (False, symbols).
    """
    # Remove comments and tokens on preprocessor directive lines
    preproc_lines = {t['line'] for t in tokens if t['type'] == 'PREPROCESSOR'}
    tokens = [
        t for t in tokens
        if t['type'] not in {'COMMENT LINE', 'COMMENT BLOCK'} and t['line'] not in preproc_lines
    ]
    
    pos = 0
    symbols = set()  # Declared variable names

    # Match and consume a token with optional specific value
    def match(expected_type, expected_value=None) -> bool:
        nonlocal pos
        if pos < len(tokens):
            token_type, token_value = tokens[pos]['type'], tokens[pos]['token']
            if token_type == expected_type and (expected_value is None or token_value == expected_value):
                pos += 1
                return True
        return False

    # Expression parsing (handles comparisons, additive, term, primary)
    def expression() -> bool:
        nonlocal pos

        def primary() -> bool:
            nonlocal pos
            if match('IDENTIFIER') or match('NUMBER'):
                return True
            elif match('PUNCTUATION', '('):
                if not expression():
                    return False
                return match('PUNCTUATION', ')')
            return False

        def term() -> bool:
            nonlocal pos
            if not primary():
                return False
            while pos < len(tokens) and tokens[pos]['type'] == 'OPERATOR' and tokens[pos]['token'] in '*/':
                pos += 1
                if not primary():
                    return False
            return True

        def additive() -> bool:
            nonlocal pos
            if not term():
                return False
            while pos < len(tokens) and tokens[pos]['type'] == 'OPERATOR' and tokens[pos]['token'] in '+-':
                pos += 1
                if not term():
                    return False
            return True

        def comparison() -> bool:
            nonlocal pos
            if not additive():
                return False
            # Support multiple comparison operators
            while pos < len(tokens) and tokens[pos]['type'] == 'OPERATOR' and tokens[pos]['token'] in ['<', '<=', '>', '>=', '==', '!=']:
                pos += 1
                if not additive():
                    return False
            return True

        return comparison()

    # Parse statements: variable declarations, return, assignments, function calls
    def statement() -> bool:
        nonlocal pos
        start_pos = pos

        # Return statement
        if match('KEYWORD', 'return'):
            if not expression():
                print(f"Syntax Error: Invalid expression after return at token {tokens[pos]}")
                return False
            if not match('PUNCTUATION', ';'):
                print(f"Syntax Error: Expected ';' after return statement at token {tokens[pos]}")
                return False
            return True
        
        # Variable declaration e.g. int x = 5, y;
        if match('KEYWORD'):
            while True:
                if not match('IDENTIFIER'):
                    return False
                var_name = tokens[pos - 1]['token']
                symbols.add(var_name)
                if match('OPERATOR', '='):
                    if not expression():
                        return False
                if not match('PUNCTUATION', ','):
                    break
            if match('PUNCTUATION', ';'):
                return True

        # Assignment or function call
        if match('IDENTIFIER'):
            var_name = tokens[pos - 1]['token']

            # Assignment: x = expr;
            if match('OPERATOR', '='):
                if expression() and match('PUNCTUATION', ';'):
                    symbols.add(var_name)
                    return True

            # Function call: f(...);
            elif match('PUNCTUATION', '('):
                while not match('PUNCTUATION', ')'):
                    if not expression():
                        return False
                    # Optional commas between arguments
                    if not match('PUNCTUATION', ',') and tokens[pos]['token'] != ')':
                        return False
                if match('PUNCTUATION', ';'):
                    return True

        # Reset position on failure to parse statement
        pos = start_pos
        return False

    # Parse control structures (while, if) with blocks
    def control_structure() -> bool:
        nonlocal pos
        start_pos = pos

        if match('KEYWORD', 'while') or match('KEYWORD', 'if'):
            if not match('PUNCTUATION', '('):
                print(f"Syntax Error: Expected '(' after control keyword at token {tokens[pos]}")
                return False
            if not expression():
                print(f"Syntax Error: Invalid expression in control condition at token {tokens[pos]}")
                return False
            if not match('PUNCTUATION', ')'):
                print(f"Syntax Error: Expected ')' after condition at token {tokens[pos]}")
                return False
            if not match('PUNCTUATION', '{'):
                print(f"Syntax Error: Expected '{{' to start block at token {tokens[pos]}")
                return False

            # Parse statements or nested control structures inside block
            while pos < len(tokens) and not match('PUNCTUATION', '}'):
                if not statement() and not control_structure():
                    return False
            return True

        # Backtrack if not a control structure
        pos = start_pos
        return False

    # Main parsing loop
    while pos < len(tokens):
        if not (control_structure() or statement()):
            print(f"Syntax Error: Unexpected token: {tokens[pos]} at line {tokens[pos]['line']}, position {tokens[pos]['position']}.")
            return False, symbols

    return True, symbols