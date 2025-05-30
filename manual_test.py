from function import lexer, parser, semantic_analyzer

def test_analyzer():
    test_cases = {
        "Valid declaration and expression": """
            int a = 5;
            float b = a + 3.14;
        """,

        "Missing semicolon": """
            int a = 5
            float b = a + 2.1;
        """,

        "Invalid character": """
            int a = 5$;
        """,

        "Valid nested expression": """
            int a = (2 + 3) * 4;
        """,

        "Function call": """
            printf("Hello, world!", "Hello, world!", "Hello, world!");
        """,

        "Unclosed string": """
            printf("Hello);
        """,

        "Preprocessor directive": """
            #include <stdio.h>
        """,

        "Comment test": """
            // This is a comment
            int a = 10;
        """,

        "Multiple Declarations": "int a = 1, b = 2, c;",

        "Return Statement": "return a + b;",

        "If Statement": """
            if (a > b) {
                a = b;
            }
        """,

        "While Loop": """
            while (a < 10) {
                a = a + 1;
            }
        """,

        "Undeclared variable used": """
            int x = y + 1;
        """,

        "Declared but unused variable": """
            int a = 5;
            int b = 10;
        """,

        "Use after declaration": """
            int a = 2;
            int b = a + 3;
        """,

        "Chained assignments with undeclared": """
            int a = b + c;
            int d = a + 1;
        """,

        "Complex expression with one undeclared": """
            int a, b, d = 0;
            int x = (a + b) * (c - d);
        """,

        "Nested scopes not handled": """
            int a = 5;
            if (a > 0) {
                b = a + 1;
            }
        """,

        "All variables declared properly": """
            int a = 1;
            int b = 2;
            int c = a + b;
        """
    }

    for name, code in test_cases.items():
        print(f"\n=== Test Case: {name} ===")
        print(f"Code:\n{code.strip()}\n")

        print("Lexical Analysis:")
        try:
            tokens, lex_errors = lexer(code)
            if lex_errors:
                print(f"Lexical Errors ❌:\n{lex_errors}")
                continue
            for t in tokens:
                print(t)
        except Exception as e:
            print(f"Lexer Error: {e}")
            continue

        print("\nSyntactic Analysis:")
        try:
            valid, symbol_table, parse_errors = parser(tokens)
            if valid:
                print("Syntax OK ✅")
            else:
                print(f"Syntax Errors ❌:\n{parse_errors}")
                continue
        except Exception as e:
            print(f"Parser Error: {e}")
            continue

        print("\nSemantic Analysis:")
        try:
            success, sem_errors, warnings, _ = semantic_analyzer(tokens, symbol_table)
            if success:
                print("Semantics OK ✅")
            else:
                print(f"Semantic Errors ❌:\n{sem_errors}")
            if warnings:
                print(f"Warnings ⚠️ :\n{warnings}")
        except Exception as e:
            print(f"Semantic Error: {e}")

# Run the test
if __name__ == "__main__":
    test_analyzer()
