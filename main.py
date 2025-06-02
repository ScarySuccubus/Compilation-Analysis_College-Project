from flask import Flask, request, jsonify
from flask_cors import CORS
from lexical_analysis import lexer, get_token_type
from utils import separate_errors, print_clean
from semantic_analysis import semantic_analyzer
from syntactic_analysis import parser

app = Flask('V1')
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


@app.route("/analise-lexica", methods=['POST'])
def lexical_analysis():
    try:
        snippet = request.get_json().get('snippet')
        response = lexer(snippet)
        success = bool(response)
        message = 'Analise lexica realizada com sucesso!' if success else 'Erro na realização da analise lexica.'
        print(message)
        return jsonify({'is_success': success, 'message': message, 'response': response}), 200
    except BaseException as e:
        print(str(e))
        return jsonify({'is_success': False, 'message': str(e)}), 500


@app.route("/analise-completa", methods=['POST'])
def full_analysis():
    try:
        snippet = request.get_json().get('snippet')
        print(f"Code:\n{snippet.strip()}\n")

        response = "Lexical Analysis:\n"
        is_success = True
        try:
            tokens = lexer(snippet)
            lex_errors = separate_errors(tokens)
            if lex_errors:
                response += f"Lexical Errors ❌:\n{print_clean(lex_errors)}\n"
            response += "Lexicon OK ✅\n"
        except Exception as e:
            response += f"Lexer Error: {e}\n"
            is_success = False

        response += "\nSyntactic Analysis:\n"
        try:
            valid, symbol_table, parse_errors = parser(tokens)
            if valid:
                response += "Syntax OK ✅\n"
            else:
                response += f"Syntax Errors ❌:\n{print_clean(parse_errors)}\n"
        except Exception as e:
            response += f"Parser Error: {e}\n"
            is_success = False

        response += "\nSemantic Analysis:\n"
        try:
            success, sem_errors, warnings, _ = semantic_analyzer(tokens, symbol_table)
            if success:
                response += "Semantics OK ✅\n"
            else:
                response += f"Semantic Errors ❌:\n{print_clean(sem_errors)}\n"
            if warnings:
                response += f"Warnings ⚠️ :\n{('\n'.join(warnings))}\n"
        except Exception as e:
            response += f"Semantic Error: {e}\n"
            is_success = False

        print(response)
        return jsonify({'is_success': is_success, 'response': response, 'message': 'Analisado com sucesso.'}), 200
    except BaseException as e:
        print(str(e))
        return jsonify({'is_success': False, 'message': f'Erro na analise: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # Critical fix
