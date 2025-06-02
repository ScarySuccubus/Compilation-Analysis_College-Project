from objects import Token, SymbolTable

def can_assign(to_type, from_type):
    """
    Determine if a value of `from_type` can be assigned to a variable of `to_type`.
    - Allows exact matches (e.g., int → int)
    - Allows promotion from int to float
    - All other combinations are considered invalid
    """
    if to_type == from_type:
        return True
    if to_type == 'float' and from_type == 'int':
        return True  # Allow promotion
    return False  # Disallow all other combinations

def semantic_analyzer(tokens: list[Token], symbol_table: SymbolTable):
    """
    Perform semantic analysis on a stream of tokens using a given symbol table.
    Checks for:
    - Assignment to `const` variables
    - Type compatibility in assignments
    - Use-before-initialization
    - Use of undeclared variables
    - Declared but unused variables (as warnings)

    Returns:
        (is_valid: bool, errors: list[str], warnings: list[str], symbol_table_snapshot: dict)
    """
    errors = []
    warnings = []
    has_error = False

    used_symbols = set()          # Track all used identifiers
    is_rhs = False                # Flag: inside the right-hand side of an assignment
    assignment_target = None      # Current left-hand-side variable being assigned to

    for i, token in enumerate(tokens):

        # Detect assignment operator
        if token['type'] == 'OPERATOR' and token['token'] == '=':
            is_rhs = True
            # Check for identifier immediately before '=' to determine assignment target
            if i > 0 and tokens[i - 1]['type'] == 'IDENTIFIER':
                assignment_target = tokens[i - 1]['token']

                # Error: assignment to const variable
                if symbol_table.is_const(assignment_target):
                    errors.append(f"Semantic Error: Assignment to constant variable '{assignment_target}'.")
                    has_error = True

        # Handle literals (numbers) in RHS
        elif token['type'] == 'NUMBER' and is_rhs and assignment_target:
            rhs_type = 'float' if '.' in token['token'] else 'int'
            declared_entry = symbol_table.lookup(assignment_target)

            if declared_entry:
                lhs_type = declared_entry.get('type')
                if not can_assign(lhs_type, rhs_type):
                    errors.append(f"Semantic Error: Cannot assign {rhs_type} to {lhs_type} variable '{assignment_target}'.")
                    has_error = True

        # Statement end; finalize assignment
        elif token['type'] == 'PUNCTUATION' and token['token'] == ';':
            if assignment_target:
                if symbol_table.is_const(assignment_target):
                    errors.append(f"Semantic Error: Cannot assign to constant variable '{assignment_target}'.")
                    has_error = True
                else:
                    symbol_table.mark_initialized(assignment_target)
            is_rhs = False
            assignment_target = None

        # Handle identifiers in RHS (e.g., x = y)
        elif is_rhs and token['type'] == 'IDENTIFIER':
            used_symbols.add(token['token'])
            symbol_table.mark_used(token['token'])

            # Error: use-before-initialization
            if not symbol_table.is_initialized(token['token']):
                errors.append(f"Semantic Error: Variable '{token['token']}' used before initialization.")
                has_error = True

            # Check type compatibility between identifiers
            if assignment_target:
                lhs = symbol_table.lookup(assignment_target)
                rhs = symbol_table.lookup(token['token'])

                if lhs and rhs:
                    lhs_type = lhs.get('type')
                    rhs_type = rhs.get('type')
                    if not can_assign(lhs_type, rhs_type):
                        errors.append(
                            f"Semantic Error: Type mismatch — cannot assign variable '{token['token']}' "
                            f"of type '{rhs_type}' to '{assignment_target}' of type '{lhs_type}'."
                        )
                        has_error = True

        # Handle literals like string, char in RHS
        elif is_rhs and token['type'] in {'NUMBER', 'STRING', 'CHAR'}:
            if assignment_target:
                lhs = symbol_table.lookup(assignment_target)
                if lhs:
                    lhs_type = lhs.get('type')

                    # Determine literal type
                    if token['type'] == 'NUMBER':
                        rhs_type = 'float' if '.' in token['token'] else 'int'
                    elif token['type'] == 'STRING':
                        rhs_type = 'string'
                    elif token['type'] == 'CHAR':
                        rhs_type = 'char'
                    else:
                        rhs_type = 'unknown'

                    if not can_assign(lhs_type, rhs_type):
                        errors.append(
                            f"Semantic Error: Type mismatch — cannot assign {rhs_type} literal to '{assignment_target}' of type '{lhs_type}'."
                        )
                        has_error = True

    # Final checks

    # Undeclared variable use
    for symbol in symbol_table.undeclared_variables(used_symbols):
        errors.append(f"Semantic Error: Variable '{symbol}' not declared.")
        has_error = True

    # Unused variable warnings
    for symbol in symbol_table.unused_variables():
        warnings.append(f"Warning: Variable '{symbol}' declared but never used.")

    # Return analysis result
    return not has_error, errors, warnings, symbol_table.dump()
