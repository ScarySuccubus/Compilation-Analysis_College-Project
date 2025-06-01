from typing import TypedDict

# --- Token Type Definition ---

class Token(TypedDict):
    """
    Represents a lexical token with location and type information.
    Fields:
        - line: Line number in the source code
        - position: Column/character position in the line
        - type: Type of token (e.g., IDENTIFIER, NUMBER, OPERATOR, etc.)
        - token: Actual token string
    """
    line: int
    position: int
    type: str
    token: str


# --- Symbol Table ---

class SymbolTable:
    """
    Manages declared variables and their attributes for semantic analysis.

    Each symbol entry contains:
        - type: The declared type of the variable (e.g., int, float)
        - used: Whether the variable was ever used
        - initialized: Whether the variable was initialized before use
        - const: Whether the variable is constant (immutable)
    """

    def __init__(self):
        self.table = {}

    def insert(self, name, attributes: dict, errors: list):
        """
        Insert a new variable into the symbol table.

        Parameters:
            - name: Variable name
            - attributes: Dictionary containing type info and const flag
            - errors: List to append semantic error messages if redeclared
        """
        if name in self.table:
            errors.append(f"Semantic Error: Redeclaration of variable '{name}'.")
        else:
            self.table[name] = {
                'type': attributes.get('type'),
                'used': False,
                'initialized': attributes.get('initialized', False),
                'const': attributes.get('const', False)
            }

    def lookup(self, name):
        """
        Return the symbol attributes if declared, else None.
        """
        return self.table.get(name)

    def mark_used(self, name):
        """
        Mark a variable as used.
        """
        if name in self.table:
            self.table[name]['used'] = True

    def mark_initialized(self, name):
        """
        Mark a variable as initialized.
        """
        if name in self.table:
            self.table[name]['initialized'] = True

    def is_initialized(self, name):
        """
        Check if a variable is initialized.
        """
        return self.table.get(name, {}).get('initialized', False)

    def is_const(self, name):
        """
        Check if a variable is declared as constant.
        """
        return self.table.get(name, {}).get('const', False)

    def undeclared_variables(self, used_symbols):
        """
        Return a list of symbols used but not declared.
        """
        return [symbol for symbol in used_symbols if symbol not in self.table]

    def unused_variables(self):
        """
        Return a list of declared but unused variables.
        """
        return [name for name, attr in self.table.items() if not attr.get('used', False)]

    def dump(self):
        """
        Return a copy of the current symbol table state (for diagnostics or reporting).
        """
        return {name: info.copy() for name, info in self.table.items()}
