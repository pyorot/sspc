import re
from compiler_syntax import validators
from compiler_syntax import Context

class CheatCode:
    def __init__(self, context, aliasList):
        self.aliasList = aliasList
        self.context = context
        self.tokens = []
        self.re_assert_game = re.compile(r'^!assertgame\s+(?P<game>(?:RVL-SOU[J|P|K|E]-0A-[0-2]\s*)+)$', re.IGNORECASE)
        self.re_assert_versionfree = re.compile(r'^!assertgame\s+\*$', re.IGNORECASE)
        self.codetext = ''
    def isEmpty(self):
        return len(self.tokens) == 0
    def lexLine(self, line):
        item = line.split('#')[0].strip()
        if self.context.aborted:
            self.context.abortThis('')
        elif item:
            m = self.re_assert_game.match(item)
            if m:
                if not (self.context.game in m.group('game').split()):
                    self.context.abortThis(f'Aborting code {self.context.name} for {self.context.game} because of assertgame directive.')
            else:
                m = self.re_assert_versionfree.match(line)
                if m:
                    self.context.versionFree = True
                    if not self.isEmpty():
                        self.context.abortAll(f'Error: assertgame directive found after compiled code in {self.context.name}')
                else:
                    item = self.aliasList.replaceInGecko(item, '*' if self.context.versionFree else self.context.game).lower()
                    for x in validators:
                        m = x[0].match(item)
                        if m:
                            self.context.incLine()
                            self.tokens += list(x[1](m, self.context))
                            if self.context.aborted:
                                self.tokens = []
                            break
                    else:
                        self.context.abortAll(f'Error: invalid syntax: "{item}" in {self.context.name}')
    def lexFile(self, file):
        if not self.context.aborted:
            for line in file:
                self.lexLine(line)
                if self.context.allAborted:
                    self.tokens = []
                    return
                if self.context.aborted:
                    self.tokens = []
                    self.context.printOut(f'Warning: skipping code {self.context.name} for {self.context.game}.')
                    return
    def getText(self):
        if self.codetext:
            return self.codetext
        text = ''
        for item in self.tokens:
            if callable(item):
                item = item()
            text += str(item).upper().strip() + '\n'
        self.codetext = text
        return text