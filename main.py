from flask import Flask, request, jsonify
from flask_cors import CORS
from lexical_analysis import lexer, get_token_type
from syntactic_analysis import parser
from semantic_analysis import semantic_analyzer
from objects import SymbolTable

app = Flask('V1')
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


@app.route("/analise-lexica", methods=['POST'])
def divide_into_tokens():
  try:
    snippet = request.get_json().get('snippet')
    # snippet = clean_string(snippet)  # for removing special chars
    response = lexer(snippet)
    message = 'Analise lexica realizada com sucesso!' if response else 'Erro na realização da analise lexica.'
    success = bool(response)
    print(message)
    return jsonify({'is_success': success, 'message': message, 'response': response}), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': str(e)}), 500


@app.route("/analise-lexica/analisa-token/<string:token>", methods=['GET'])
def do_lexical_analysis(token):
  try:
    # Lógica para obter o item com o ID fornecido
    result = get_token_type(token)
    success = bool(result)
    message = 'Token encontrado com sucesso!' if success else 'Token não encontrado.'
    print(message)
    return jsonify({'is_success': success, 'message': message, 'response': result}), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': str(e)}), 500
  
@app.route("/analise-sintatica", methods=['POST'])
def call_parser():
  try:
    code = request.get_json().get('code')
    # snippet = clean_string(snippet)  # for removing special chars
    success, symbol_table, errors = parser(code)
    message = 'Analise sintatica realizada com sucesso!' if success else 'Erro na realização da analise sintatica.'
    print(message)
    return jsonify({'is_success': success, 'message': message, 'response': (symbol_table.dump(), errors)}), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': str(e)}), 500
  
@app.route("/analise-semantica", methods=['POST'])
def call_semantic():
  try:
    code, symbol_table_json = (request.get_json().get('code'), request.get_json().get('symbol_table'))
    symbol_table = SymbolTable.from_dict(symbol_table_json)
    # snippet = clean_string(snippet)  # for removing special chars
    success, errors, warnings, symbol_table_sem = semantic_analyzer(code, symbol_table)
    message = 'Analise semantica realizada com sucesso!' if success else 'Erro na realização da analise semantica.'
    print(message)
    return jsonify({
        'is_success': success,
        'message': message,
        'response': {
            'symbol_table': symbol_table_sem,
            'errors': errors,
            'warnings': warnings
        }
    }), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': str(e)}), 500

if __name__ == '__main__':
  app.run(debug=True, use_reloader=False)  # Critical fix