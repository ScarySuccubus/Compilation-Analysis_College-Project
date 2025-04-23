from flask import Flask, request, jsonify
from function import add_word, check_word #, clean_string

app = Flask('V1')
 

@app.route("/analise-lexica/verifica-token/<string:token>", methods=['GET'])
def do_lexical_analysis(token):
  try:
    # Lógica para obter o item com o ID fornecido
    success = check_word(token)
    message = 'Token encontrado com sucesso!' if success else 'Erro ao encontrar token.'
    print(message)
    return jsonify({'is_success': success, 'message': message}), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': e}), 500
    

@app.route("/analise-lexica/adiciona-token", methods=['POST'])
def add_to_lexicon():
  try:
    token = request.get_json().get('token')
    success = add_word(token)
    message = 'Token adicionado com sucesso!' if success else 'Erro ao adicionar o token.'
    print(message)
    return jsonify({'is_success': success, 'message': message}), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': e}), 500


@app.route("/analise-lexica/divide-token", methods=['POST'])
def divide_into_tokens():
  try:
    snippet = request.get_json().get('snippet')
    # snippet = clean_string(snippet)  
    response = snippet.split()
    message = 'Tokens divididos com sucesso!' if response else 'Erro ao dividir os tokens.'
    success = bool(response)
    print(message)
    return jsonify({'is_success': success, 'message': message, 'response': response}), 200
  except BaseException as e:
    print(str(e))
    return jsonify({'is_success': False, 'message': e}), 500


if __name__ == "__main__":
  app.run(debug=True)