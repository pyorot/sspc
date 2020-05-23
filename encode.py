import sys
import os
import compiler

def doPrint(arg):
    print (arg)

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
    doPrint('Error: no valid command supplied (among g,d,a)')
    exit()
gameFilter = ''
codeFilter = ''
for arg in sys.argv[1:-1]:
    if arg.startswith('--game='):
        if gameFilter:
            doPrint('Error: duplicate --game argument specified.')
            exit()
        gameFilter = arg[len('--game='):]
    elif arg.startswith('--code='):
        if codeFilter:
            doPrint('Error: duplicate --code argument specified.')
            exit()
        codeFilter = arg[len('--game='):]
    else:
        doPrint(f'Error: unrecognized argument: {arg}')
        exit()

doPrint(f'== encode.py {commandsText} ==')

aliasList = compiler.getAliasList('src/aliases.xml', doPrint)
gameList = aliasList.getGameList(gameFilter)

def ensuredir(path):
    if not os.path.exists(path): os.mkdir(path)

ensuredir('build')
ensuredir('build-asm')

def compileAsm(gamePath, gameMacro):
    ensuredir('build-asm/' + gamePath)
    with open(f'build-asm/{gamePath}/aliases.asm', 'w') as aliasOut:
        for macro in aliasList.getMacrosForGame(gameMacro):
            aliasOut.write(macro + '\n')
    os.system(f'sh assemble.sh {gamePath}')

if a:
    for game in gameList:
        compileAsm(game, game)
    compileAsm('.free', '*')
    doPrint('Info: assemble finished')

outputs = {}
for filename in os.listdir('src'):
    if codeFilter in filename:
        for game in gameList:
            if filename.endswith(".gecko"):
                code = compiler.CheatCode(filename[:-6], game, aliasList)
                with open('src/' + filename, 'r') as srcfile:
                    code.lexer(srcfile)(exit, doPrint)
                    if not code.aborted:
                        if code.isEmpty() and not code.aborted:
                            doPrint(f'Warning: ignoring empty file: {filename}')
                        elif not code.aborted:
                            doPrint(f'Info: will encode: {filename} for {game}')
                            if game in outputs:
                                outputs[game].append(code)
                            else:
                                outputs[game] = [code]

if outputs:
    for game in gameList:
        iniPath = f'build/{game}.ini'
        gctPath = f'build/{game}.gct'
        def noCodes():
            doPrint(f'No codes found for {game} - not encoding those files')
            if os.path.exists(iniPath): os.remove(iniPath)
            if os.path.exists(gctPath): os.remove(gctPath)
        encode = False
        if game in outputs:
            codes = outputs[game]
            if codes:
                encode = True
                doPrint(f'Encoding {game}...')
                if g:
                    with open(gctPath, 'wb') as gfile:
                        gfile.write(bytes.fromhex('00d0c0de00d0c0de'))
                        for code in codes:
                            doPrint(f'    Encoding {code.name} into gct...')
                            gfile.write(bytes.fromhex(''.join(code.getText().split())))
                        gfile.write(bytes.fromhex('f000000000000000'))
                if d:
                    with open(iniPath, 'w') as dfile:
                        dfile.write('[Gecko]\n')
                        for code in codes:
                            doPrint(f'    Encoding {code.name} into ini...')
                            dfile.write('$sspc | ' + code.name + '\n' + code.getText())
        if not encode:
            noCodes()
else:
    doPrint('No codes found.')