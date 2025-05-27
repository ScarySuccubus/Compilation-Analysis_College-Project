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
      {'regex': r'(?i)\b([a-z_][a-z0-9_]*)\s*\(', 'type': 'FUNCTION'},
      {'regex': r'[a-zA-Z_$][a-zA-Z0-9_$]*', 'type': 'IDENTIFIER'},
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