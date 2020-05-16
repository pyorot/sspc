import sys
import os
import compiler

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

outputs = []
for filename in os.listdir('src'):
    if filename.endswith(".gecko"):
        code = compiler.CheatCode(filename[:-6])
        with open('src/' + filename, 'r') as srcfile:
            if not code.lex(srcfile):
                exit()
            if code.isEmpty():
                print(f'Warning: ignoring empty file: {filename}')
            else:
                print(f'Info: will encode: {filename}')
                outputs.append(code)

if outputs:
    if g:
        with open('build/sspc.gct', 'wb') as gfile:
            gfile.write(bytes.fromhex('00d0c0de00d0c0de'))
            for code in outputs:
                gfile.write(bytes.fromhex(''.join(code.getText().split())))
            gfile.write(bytes.fromhex('f000000000000000'))
        print('Info: encoded GCT')
    if d:
        with open('build/sspc.ini', 'w') as dfile:
            dfile.write('[Gecko]\n')
            for code in outputs:
                dfile.write('$sspc | ' + code.name + '\n' + code.getText())
        print('Info: encoded Dolphin INI')
else:
    print('Error: nothing to encode.')
