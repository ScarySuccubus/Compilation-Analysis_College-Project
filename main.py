from flask import Flask, request, jsonify
from flask_cors import CORS
from function import lexer, get_token_type

app = Flask('V1')
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


@app.route("/analise-lexica", methods=['POST'])
def divide_into_tokens():
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

if __name__ == '__main__':
  app.run(debug=True, use_reloader=False)  # Critical fix