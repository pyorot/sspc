import sys
import os
import re

g = sys.argv and 'g' in sys.argv[-1]    # Encodes everything into one GCT file
d = sys.argv and 'd' in sys.argv[-1]    # Encodes everything into a Dolphin ini
if not g and not d:
    print('Error: Specify g (gct) and/or d (dolphin ini) in last argument')
    exit()

if not os.path.exists('build'): os.mkdir('build')
validator = re.compile(r'^[0-9a-f]{8}\s[0-9a-f]{8}$')   # regex to validate gecko syntax

names = []
outputs = []
for filename in os.listdir('src'):
    if filename.endswith(".gecko"):
        text = ''
        with open('src/' + filename, 'r') as srcfile:
            while True:
                line = srcfile.readline()
                if line:
                    item = line.split('#')[0].strip()
                    if item:
                        if validator.match(item):
                            text += item + '\n'
                        else:
                            print(f'Error: invalid syntax: "{item}" in {filename}')
                            exit()
                else:
                    break
            if text:
                outputs.append(text)
                names.append(filename[:-6])
                print(f'Info: will encode: {filename}')
            else:
                print(f'Warning: ignoring empty file: {filename}')

if outputs:
    if g:
        with open('build/sspc.gct', 'wb') as gfile:
            gfile.write(bytes.fromhex('00d0c0de00d0c0de'))
            for code in outputs:
                gfile.write(bytes.fromhex(''.join(code.split())))
            gfile.write(bytes.fromhex('f000000000000000'))
        print('Info: encoded GCT')
    if d:
        with open('build/sspc.ini', 'w') as dfile:
            dfile.write('[Gecko]\n')
            for i in range(len(outputs)):
                dfile.write('\n$' + names[i] + '\n' + outputs[i])
        print('Info: encoded Dolphin INI')
else:
    print('Error: nothing to encode.')
