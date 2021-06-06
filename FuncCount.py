import os

root = r'C:\Users\aviro\Desktop\game_engine'
pattern = ".py"

py_files = []
for path, subdirs, files in os.walk(root):
    for name in files:
        if name.endswith(pattern):
            f = os.path.join(path, name)
            if 'venv' not in f:
                py_files.append(f)
  
methods = 0  # 670
classes = 0  # 215
for file in py_files:
    try:
        content = open(file, 'rb').read().decode()
        methods += content.count('def')
        classes += content.count('class')
    except Exception as e:
        print('\nError In:\n', file)
        raise e
print(methods)
print(classes)

