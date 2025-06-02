import re
from objects import Tag
    
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
      #{'regex': r'(?i)\b([a-z_][a-z0-9_]*)\s*\(', 'type': 'FUNCTION'},
      {'regex': r'[a-zA-Z_][a-zA-Z0-9_]*', 'type': 'IDENTIFIER'},
      {'regex': r'"([^"\\]|\\.)*"', 'type': 'STRING'},
      # {'regex': r"'([^'\\]|\\.)*'", 'type': 'STRING'},
      {'regex': r'''[{}()\[\];,:.'"]''', 'type': 'PUNCTUATION'},

      {'regex': r'[+\-*/=<>!&|]', 'type': 'OPERATOR'}]

  for token_type in token_types:
      if re.fullmatch(token_type['regex'], token):
          return token_type['type']
  return Tag.UNKNOWN


def try_n_catch (text):
    test = get_token_type(text) # tries the entire line in case of comments
    if test != Tag.UNKNOWN:
        return {'token': text, 'type': test}

    parts = re.findall(r'\w+|\S', text) # splits everything up
    # tests symbol+text combos like #define or malloc(
    if len(parts) > 1 and (not parts[0].isalnum() or not parts[1].isalnum()):
        part = parts[0] + parts[1]
        test = get_token_type(part)
        if test != Tag.UNKNOWN:
            return {'token': part, 'type': test}

    # tests decimals in a very roundabout way lol
    if len(parts) > 2 and (get_token_type(parts[0]) == Tag.NUMBER and
                           parts[1] == Tag.DOT and
                           get_token_type(parts[2]) == Tag.NUMBER):
        number = ''.join(parts[:3])
        if text.find(number) != -1: # in case the numbers are not written together
            next_char = text[text.find(number)+len(number)]
            if next_char in (Tag.SEMICOLON, Tag.CURLY_BRACKETS_CLOSED) or next_char.isspace():
                return {'token': number, 'type': Tag.DECIMAL}

    # last chance
    test = get_token_type(parts[0])
    return {'token': parts[0], 'type': test}


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

        # for multiline comment blocks
        if code[line][position:position+2] == Tag.MULTILINE_BEGIN:
            start_snippet = snippet = code[line][position:]  # captures the first comment line
            if snippet.find(Tag.MULTILINE_END) != -1:  # single line comment block
                snippet = snippet[:snippet.find(Tag.MULTILINE_END) + 2]
                tokens.append({"line": line, "position": position,
                               "type": Tag.MULTILINE, "token": snippet})
                position += len(snippet)
                continue

            # searching the end of the comment
            start_line = line
            start_pos = position
            end_found = False
            end_pos = 0
            line += 1
            while line < len(code):
                end_pos = code[line].find(Tag.MULTILINE_END)
                if end_pos != -1:
                    end_found = True
                    snippet += '\n' + code[line][:end_pos + 2] # to include the */ in the snippet

                    tokens.append({"line": start_line, "position": start_pos,
                                   "type": Tag.MULTILINE, "token": snippet})
                    break
                snippet += '\n' + code[line]
                line += 1
            if end_found:
                position = end_pos + len(Tag.MULTILINE_END)
                if position < len(code[line]):
                    continue
            else:
                position = 0
                line = start_line + 1
                tokens.append({"line": start_line, "position": start_pos,
                               "type": 'LEXICAL ERROR: MULTI-LINE COMMENT UNCLOSED',
                               "token": start_snippet})
            continue

        # strings
        if code[line][position] == Tag.QUOTATION_MARK:
            try: # just gets a full inline string if enclosed
                match = re.match(fr'^{re.escape(Tag.QUOTATION_MARK)}.*?{re.escape(Tag.QUOTATION_MARK)}',
                                 code[line][position:])
                match = match.group(0)
                test = get_token_type(match)
                if test != Tag.UNKNOWN:
                    tokens.append({"line": line, "position": position,
                                   "type": test, "token": match})
                    position += len(match)
                    continue
            except AttributeError:
                tokens.append({"line": line, "position": position,
                               "type": 'LEXICAL ERROR: UNCLOSED STRING', "token": '"'})
                position += 1
                continue

        # Last analysis
        snippet = try_n_catch(code[line][position:])
        if snippet['type'] != Tag.UNKNOWN:
            tokens.append({"line": line, "position": position,
               "type": snippet['type'], "token": snippet['token']})
        else:
            tokens.append({"line": line, "position": position,
            "type": 'LEXICAL ERROR: UNEXPECTED CHARACTER', "token": snippet['token']})
        position += len(snippet['token'])
        continue

    return tokens