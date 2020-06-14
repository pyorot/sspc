import os
import subprocess
from lib.functional import FuncList, xmap, xfilter

def assembleasm(filename, aliases, versionfilter, buildfolder, srcfolder):
    def ensuredir(path):
        if not os.path.exists(path): os.mkdir(path)
    ensuredir(srcfolder)
    ensuredir(buildfolder)
    for game in aliases.getGameList(versionfilter):
        ensuredir(buildfolder + '/' + game)
    ensuredir(f'{buildfolder}/.free')
    os.chdir('pyiiasmh')
    def outputsinglecode(game, filter):
        with open(f'../{buildfolder}/tmp.asm', 'w') as tmpfile:
            contents = list(aliases.getMacrosForGame(filter))
            with open(f'../{srcfolder}/_macros.asm', 'r') as f:
                contents.append(f.read())
            with open(f'../{srcfolder}/{filename}.asm', 'r') as f:
                contents.append(f.read())
            tmpfile.write('\n'.join(contents) + '\n')
        output = subprocess.Popen(f'py -2 pyiiasmh_cli.py -a -codetype C0 ../{buildfolder}/tmp.asm'.split(), stdout=subprocess.PIPE).communicate()
        with open(f'../{buildfolder}/{game}/{filename}.gecko', 'w') as outfile:
            for line in output[0].decode('utf-8').strip().split('\n'):
                outfile.write(line.strip() + '\n')
        print (f'- Assembled {game}/{filename}.asm')
    for game in aliases.getGameList(versionfilter):
        outputsinglecode(game, game)
    outputsinglecode('.free', '*')
    os.chdir('..')

def assemble(aliases, versionfilter):
    FuncList(os.listdir('src-asm')).pipe(
        xfilter(lambda x: x.endswith('.asm') and x != '_macros.asm'),
        xmap(lambda x: x[:-4])
    ).foreach(lambda x: assembleasm(x, aliases, versionfilter, 'build-asm', 'src-asm'))