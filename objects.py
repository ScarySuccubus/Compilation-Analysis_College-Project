from typing import TypedDict

class Tag:
    # Words
    UNKNOWN = 'UNKNOWN'
    NUMBER = 'NUMBER'
    PUNCTUATION = 'PUNCTUATION'
    DECIMAL = 'DECIMAL'
    MULTILINE = 'MULTILINE COMMENT'
    # Punctuation
    DOT = '.'
    SEMICOLON = ';'
    CURLY_BRACKETS_CLOSED = '}'
    MULTILINE_BEGIN = '/*'
    MULTILINE_END = '*/'
    QUOTATION_MARK = '"'


class Token(TypedDict):
    line: int
    position: int
    type: str
    token: str

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