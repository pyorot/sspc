import sys
import os
import re

g,d,a = True,True,False
if len(sys.argv) >=2:
    g = sys.argv and 'g' in sys.argv[-1]    # encodes everything into one GCT file
    d = sys.argv and 'd' in sys.argv[-1]    # encodes everything into a Dolphin ini
    a = sys.argv and 'a' in sys.argv[-1]    # runs assemble.sh
commandsText = ''
if g: commandsText += 'g'
if d: commandsText += 'd'
if a: commandsText += 'a'
if not commandsText:
    print('Error: no valid command supplied (among g,d,a)')
    exit()
print(f'== encode.py {commandsText} ==')

if a:
    os.system('sh assemble.sh')
    print('Info: assemble finished')

if not os.path.exists('build'): os.mkdir('build')
validator = re.compile(r'^[0-9a-f]{8}\s[0-9a-f]{8}$')       # regex to validate gecko syntax
validator_expansion = re.compile(r'^{([0-9a-z\-]+).asm}$')  # regex to validate expansion syntax

names = []
outputs = []
for filename in os.listdir('src'):
    if filename.endswith(".gecko"):
        text = ''
        with open('src/' + filename, 'r') as srcfile:
            while True:
                line = srcfile.readline()
                if line:
                    item = line.split('#')[0].strip().lower()
                    if item:
                        if validator.match(item):               # line of gecko
                            text += item + '\n'
                        elif validator_expansion.match(item):   # expansion command
                            try:
                                expandname = validator_expansion.match(item).group(1)
                                with open(f'build-asm/{expandname}.gecko', 'r') as expandfile:
                                    text += expandfile.read().lower()
                                print(f'Info: expanded file: {expandname}.asm in {filename}')
                            except FileNotFoundError:
                                print(f'Error: expansion file not found: {expandname}.asm')
                                exit()
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
