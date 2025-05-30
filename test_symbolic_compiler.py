import unittest
from function import lexer, parser, semantic_analyzer

class TestSymbolicCompiler(unittest.TestCase):
    def assertLexSuccess(self, tokens, lex_errors):
        self.assertEqual(len(lex_errors), 0, f"Lexical errors found: {lex_errors}")
        for token in tokens:
            self.assertNotEqual(token["type"], "LEXICAL_ERROR", f"Lexical error on token: {token}")

    def assertParseSuccess(self, tokens):
        valid, _, parse_errors = parser(tokens)
        self.assertTrue(valid, f"Parsing failed. Errors: {parse_errors}")

    def assertSemanticSuccess(self, tokens, symbol_table):
        success, sem_errors, warnings, _ = semantic_analyzer(tokens, symbol_table)
        self.assertTrue(success, f"Semantic analysis failed. Errors: {sem_errors}")

    def assertSemanticFailure(self, tokens, symbol_table):
        success, sem_errors, warnings, _ = semantic_analyzer(tokens, symbol_table)
        self.assertFalse(success, f"Expected semantic error but passed. Warnings: {warnings}")

    def run_pipeline(self, code):
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, symbol_table, parse_errors = parser(tokens)
        self.assertTrue(valid, f"Parsing failed. Errors: {parse_errors}")
        return tokens, symbol_table

    def test_valid_declaration_and_expression(self):
        code = "int a = 5;\nfloat b = a + 3.14;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_missing_semicolon(self):
        code = "int a = 5\nfloat b = 2.0;"
        tokens, lex_errors = lexer(code)
        self.assertLexSuccess(tokens, lex_errors)
        valid, _, parse_errors = parser(tokens)
        self.assertFalse(valid, f"Expected parse failure but passed. Errors: {parse_errors}")

    def test_invalid_character(self):
        code = "int a = 5$;"
        tokens, lex_errors = lexer(code)
        self.assertTrue(len(lex_errors) > 0, "Expected invalid character error.")

    def test_undeclared_variable_use(self):
        code = "int x = y + 1;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticFailure(tokens, sym_table)

    def test_declared_but_unused(self):
        code = "int a = 5;\nint b = 10;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_use_after_declaration(self):
        code = "int a = 2;\nint b = a + 3;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_chained_assignments_with_undeclared(self):
        code = "int a = b + c;\nint d = a + 1;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticFailure(tokens, sym_table)

    def test_complex_expression_with_undeclared(self):
        code = "int a, b, d = 0;\nint x = (a + b) * (c - d);"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticFailure(tokens, sym_table)

    def test_all_variables_declared(self):
        code = "int a = 1;\nint b = 2;\nint c = a + b;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_return_statement(self):
        code = "int a = 5;\nint b = 2;\nreturn a + b;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_nested_expression(self):
        code = "int a = (2 + 3) * 4;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_comment_handling(self):
        code = "// this is a comment\nint a = 10;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)

    def test_preprocessor_ignored(self):
        code = "#include <stdio.h>\nint a = 5;"
        tokens, sym_table = self.run_pipeline(code)
        self.assertSemanticSuccess(tokens, sym_table)


if __name__ == '__main__':
    unittest.main()
