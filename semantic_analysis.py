from objects import Token, SymbolTable

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