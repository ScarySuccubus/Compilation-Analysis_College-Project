wordlist_python = ['print', 'input', 'if', 'elif', 'else', 'range', 'for', 'while', 'pass', 'return', 'str', 'int', 'def', 'in', 'True', 'False', 'try', 'except', 'type']


def add_word(word):
  if word in wordlist_python :
    return True
    
  wordlist_python.append(word)
  return True


def check_word(word):
  return word in wordlist_python
  

def clean_string(text):
  new_string = ''.join(char for char in text if char.isalnum() or char == ' ')
  return new_string