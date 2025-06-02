import unittest
from lexical_analysis import lexer  # Lexical analysis module
from syntactic_analysis import parser  # Syntactic analysis module
from semantic_analysis import semantic_analyzer  # Semantic analysis module

class TestCompiler(unittest.TestCase):

    # --- ✅ Lexical Assert Helpers ---
    def assertLexSuccess(self, tokens, lex_errors):
        """Ensure no lexical errors in token stream."""
        self.assertEqual(len(lex_errors), 0, f"Lexical errors found: {lex_errors}")
        for token in tokens:
            self.assertNotEqual(token["type"], "LEXICAL_ERROR", f"Lexical error on token: {token}")

    # --- ✅ Syntactic Assert Helpers ---
    def assertParseSuccess(self, tokens):
        """Ensure parsing succeeds."""
        valid, _, parse_errors = parser(tokens)
        self.assertTrue(valid, f"Parsing failed. Errors: {parse_errors}")

    def assertParseFailure(self, tokens):
        """Ensure parsing fails for invalid syntax."""
        valid, _, parse_errors = parser(tokens)
        self.assertFalse(valid, f"Expected parsing failure. Errors: {parse_errors}")

    # --- ✅ Semantic Assert Helpers ---
    def assertSemanticSuccess(self, tokens, symbol_table):
        """Ensure semantic analysis succeeds."""
        success, sem_errors, warnings, _ = semantic_analyzer(tokens, symbol_table)
        self.assertTrue(success, f"Semantic analysis failed. Errors: {sem_errors}")

    def assertSemanticFailure(self, tokens, symbol_table):
        """Ensure semantic analysis fails as expected."""
        success, sem_errors, warnings, _ = semantic_analyzer(tokens, symbol_table)
        self.assertFalse(success, f"Expected semantic failure but got success. Warnings: {warnings}")

    # --- ✅ Compiler Pipeline (Lexing → Parsing) ---
    def run_pipeline(self, code):
        """Runs code through lexer and parser, returns tokens and symbol table."""
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, symbol_table, parse_errors = parser(tokens)
        self.assertTrue(valid, f"Parsing failed. Errors: {parse_errors}")
        return tokens, symbol_table

    # --- ✅ TEST CASES ---

    # ✅ Valid end-to-end test (lex + parse + semantic)
    def test_valid_declaration_and_expression(self):
        code = "int a = 5;\nfloat b = a + 3.14;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ❌ Syntactic error: Missing semicolon
    def test_missing_semicolon(self):
        code = "int a = 5\nfloat b = 2.0;"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        self.assertParseFailure(tokens)

    # ❌ Lexical error: Invalid character
    def test_invalid_character(self):
        code = "int a = 5$;"
        tokens, lex_errors = lexer(code)
        self.assertGreater(len(lex_errors), 0, "Expected a lexical error for invalid character.")

    # ❌ Semantic error: Use of undeclared variable
    def test_undeclared_variable_use(self):
        code = "int x = y + 1;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticFailure(tokens, sym_table)

    # ⚠️ Semantic warning: Variable declared but not used
    def test_declared_but_unused(self):
        code = "int a = 5;\nint b = 10;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ✅ Semantic: Correct use after declaration
    def test_use_after_declaration(self):
        code = "int a = 2;\nint b = a + 3;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ❌ Semantic error: Chain assignments with undeclared vars
    def test_chained_assignments_with_undeclared(self):
        code = "int a = b + c;\nint d = a + 1;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticFailure(tokens, sym_table)

    # ❌ Semantic error: Complex expression with undeclared var
    def test_complex_expression_with_undeclared(self):
        code = "int a, b, d = 0;\nint x = (a + b) * (c - d);"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticFailure(tokens, sym_table)

    # ✅ Semantic: All variables declared and used correctly
    def test_all_variables_declared(self):
        code = "int a = 1;\nint b = 2;\nint c = a + b;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ✅ Semantic: Return with expression
    def test_return_statement(self):
        code = "int a = 5;\nint b = 2;\nreturn a + b;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ✅ Syntactic: Nested expression valid
    def test_nested_expression(self):
        code = "int a = (2 + 3) * 4;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ✅ Lexical: Comment should be ignored
    def test_comment_handling(self):
        code = "// this is a comment\nint a = 10;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ✅ Lexical: Preprocessor directive ignored
    def test_preprocessor_ignored(self):
        code = "#include <stdio.h>\nint a = 5;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    # ❌ Syntactic: Extra unmatched closing brace
    def test_unexpected_closing_brace(self):
        code = "int a = 5; }"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        self.assertParseFailure(tokens)

    # ❌ Syntactic: Missing closing parenthesis
    def test_missing_closing_parenthesis(self):
        code = "int a = (2 + 3;"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        self.assertParseFailure(tokens)

    # ❌ Syntactic: Unmatched opening bracket
    def test_unmatched_opening_bracket(self):
        code = "int a = (5 + 3;"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, _, errors = parser(tokens)
        self.assertFalse(valid)
        self.assertTrue(any("Unmatched opening bracket" in e['message'] for e in errors))

    # ❌ Syntactic: Unmatched closing bracket
    def test_unmatched_closing_bracket(self):
        code = "int a = 5 + 3);"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, _, errors = parser(tokens)
        self.assertFalse(valid)
        self.assertTrue(any("Unmatched closing bracket" in e['message'] for e in errors))

    # ❌ Syntactic: Missing semicolon after function call
    def test_missing_semicolon_after_function_call(self):
        # Valid case
        code = "foo();"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, _, errors = parser(tokens)
        self.assertTrue(valid)

        # Invalid case: Missing semicolon
        code_missing_semicolon = "foo()"
        tokens2, lex_errors2 = lexer(code_missing_semicolon)
        self.assertLexSuccess(tokens2, lex_errors2)
        valid2, _, errors2 = parser(tokens2)
        self.assertFalse(valid2)
        self.assertTrue(any("Expected ';' after function call" in e['message'] for e in errors2))

    # ❌ Syntactic: Return statement with no expression
    def test_invalid_return_statement(self):
        code = "return;"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, _, errors = parser(tokens)
        self.assertFalse(valid)
        self.assertTrue(any("Invalid return statement syntax" in e['message'] for e in errors))

    # ❌ Syntactic: Control structures without braces
    def test_if_while_without_braces(self):
        code = "if (a < 5) a = 3;"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, _, errors = parser(tokens)
        self.assertFalse(valid)
        self.assertTrue(any("Invalid control structure syntax" in e['message'] for e in errors))


# Run tests
if __name__ == '__main__':
    unittest.main()
