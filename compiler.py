import re
import xml.etree.ElementTree as ET

def orNop(func, arg):
    if func:
        func(arg)

def orNop0(func):
    if func:
        func()

negative_digits = ['8','9','A','B','C','D','E','F']

def wrap(s):
    return lambda l: s

def distanceTo(st, label, fromLine, printOut):
    def getDist(labels):
        distance = labels.distanceTo(label, fromLine + 1)
        if distance[0] in negative_digits:
            printOut(f'Warning: flow control using negative offset. This code may not work as intended. Label = {label}')
        return st.format(distance)
    yield getDist

def flowGoto(match, labels, printOut, abortAllCodes):
    return distanceTo("6600{0} 00000000", match.group(1), labels.line, printOut)

def flowReturn(match, labels, printOut, abortAllCodes):
    yield wrap("64000000 0000000{0}".format(match.group(1)))

def flowGosub(match, labels, printOut, abortAllCodes):
    return distanceTo("6800{0} 0000000" + match.group(1), match.group(2), labels.line, printOut)

def flowLabel(match, labels, printOut, abortAllCodes):
    labels.add(match.group(1))
    labels.incLine(-1)
    return []

def flowGecko(match, labels, printOut, abortAllCodes):
    yield wrap(match.group(1))

def flowAsm(match, labels, printOut, abortAllCodes):
    try:
        expandname = match.group(1)
        labels.incLine(-1)
        game = '.free' if labels.versionFree else labels.game
        with open(f'build-asm/{game}/{expandname}.gecko', 'r') as expandfile:
            for line in expandfile:
                yield wrap(line.lower())
                labels.incLine()
        printOut(f'Info: expanded file: {game}/{expandname}.asm')
    except FileNotFoundError:
        abortAllCodes(f'Error: expansion file not found: {expandname}.asm')

def flowAssignLiteralToGR(match, labels, printOut, abortAllCodes):
    register = match.group(1)
    value = int(match.group(2), 16)
    yield wrap("8000000{0} {1:0{2}X}".format(register, value, 8))

typeConvert = {
    'b': 0,
    'h': 1,
    'w': 2
}

def flowLoadMemToGR(match, labels, printOut, abortAllCodes):
    register = match.group(1)
    typeChar = match.group(2)
    address = match.group(3)
    yield wrap("82{0}0000{1} {2}".format(typeConvert[typeChar], register, address))

def flowWriteToMem(match, labels, printOut, abortAllCodes):
    match = match.groupdict()
    start = 16 if 'bapo' in match and match['bapo'] == 'po' else 0
    typeChar = typeConvert[match['type']]
    maxValue = 2**(2**(typeChar + 3))               # max (exclusive) value
    typeByte = typeChar * 2 + start                 # first byte of command
    value = match['value']
    valueInt = int(value, 16)
    if valueInt >= maxValue:
        matchType = match['type']
        orNop(abortAllCodes, f'Error: assigning value {value} is out of bounds for type {matchType}')
        return iter([])
    sourceAddress = int(match['offset'], 16) if 'offset' in match and match['offset'] else 0
    if sourceAddress > 0x01FFFFFF:
        orNop(abortAllCodes, 'Error: address offset greater than 0x01FFFFFF cannot be encoded.')
        return iter([])
    if sourceAddress > 0x00FFFFFF:
        typeByte += 1
        sourceAddress -= 0x01000000
    halfline1 = "{0:0{1}X}{2:0{3}X}".format(typeByte, 2, sourceAddress, 6)
    times = int(match['times'], 16) if 'times' in match and match['times'] else 1
    timeString = "{0:0{1}X}".format(times - 1, 4)
    if typeChar == 0:
        halfline2 = "{2}00{0:0{1}X}".format(valueInt, 2, timeString)
    elif typeChar == 1:
        halfline2 = "{2}{0:0{1}X}".format(valueInt, 4, timeString)
    else:
        if times > 1:
            orNop(abortAllCodes, 'Error: cannot specify repeated placement for word-sized values.')
            return iter([])
        halfline2 = "{0:0{1}X}".format(valueInt, 8)
    yield wrap(f'{halfline1} {halfline2}')

def flowMemcpy(match, betweenRegisters, offsetOnSource, abortAllCodes):
    times = match['times'] if 'times' in match and match['times'] else '1'
    sourceRegister = match['register']
    destRegister = match['destRegister'] if 'destRegister' in match and match['destRegister'] else '0'
    po = 'bapo' in match and match['bapo'] == 'po'
    offset = match['offset'] if 'offset' in match and match['offset'] else '0'

    firstByte = 0x8A
    lastByte = sourceRegister + 'F'
    if offsetOnSource:
        firstByte += 2
        lastByte = lastByte[::-1]
    if betweenRegisters:
        lastByte = sourceRegister + destRegister
    firstByte += (16 if po else 0)
    pointerOffset = int(offset, 16)
    if pointerOffset > 0x01FFFFFF:
        orNop(abortAllCodes, 'Error: address offset greater than 0x01FFFFFF cannot be encoded.')
        return iter([])
    if pointerOffset > 0x00FFFFFF:
        firstByte += 1
        pointerOffset -= 0x01000000
    yield wrap("{0:X}{1:0{2}X}{3} {4:0{5}X}".format(firstByte, int(times, 16), 4, lastByte, pointerOffset, 8))

def flowMemcpy1(match, labels, printOut, abortAllCodes):
    return flowMemcpy(match.groupdict(), False, False, abortAllCodes)

def flowMemcpy11(match, labels, printOut, abortAllCodes):
    return flowMemcpy(match.groupdict(), True, False, abortAllCodes)

def flowMemcpy2(match, labels, printOut, abortAllCodes):
    return flowMemcpy(match.groupdict(), False, True, abortAllCodes)

def flowMemcpy21(match, labels, printOut, abortAllCodes):
    return flowMemcpy(match.groupdict(), True, True, abortAllCodes)

def flowStoreGR(match, labels, printOut, abortAllCodes):
    match = match.groupdict()
    bapo = 'bapo' in match and match['bapo']
    po = 'bapo' in match and match['bapo'] and match['bapo'].startswith('po')
    offset = match['offset'] if 'offset' in match and match['offset'] else '0'
    if offset.upper() == 'BA' and not bapo:
        # Edge case: interpret BA as base address, not 0xBA
        bapo = True
        offset = '0'
    register = match['register']
    t = match['type']
    times = match['times'] if 'times' in match and match['times'] else '1'
    
    startByte = 0x84 + (16 if po else 0)
    typeDigit = typeConvert[t]
    baseDigit = 1 if bapo else 0
    timesValue = int(times,16) - 1
    yield wrap("{0:0{1}X}{2}{3}{4:0{5}X}{6} {7:0{8}X}".format(startByte, 2, typeDigit, baseDigit, timesValue, 3, register, int(offset, 16), 8))

validators = [
    [ re.compile(r'^([0-9a-f]{8}\s[0-9a-f]{8})$', re.IGNORECASE), flowGecko ],
    [ re.compile(r'^{([0-9a-z\-]+).asm}$', re.IGNORECASE), flowAsm ],
    [ re.compile(r'^gosub ([0-9a-f]) ([0-9a-z_]+)$', re.IGNORECASE), flowGosub ],
    [ re.compile(r'^goto ([0-9a-z_]+)$', re.IGNORECASE), flowGoto ],
    [ re.compile(r'^return ([0-9a-f])$', re.IGNORECASE), flowReturn ],
    [ re.compile(r'^gr([0-9a-f])\s*:=\s*([0-9a-f]{1,8})$', re.IGNORECASE), flowAssignLiteralToGR ],
    [ re.compile(r'^gr([0-9a-f])\s*:=\s*([bhw])\s*\[\s*([0-9a-f]{8})\s*\]$', re.IGNORECASE), flowLoadMemToGR ],
    [ re.compile(r'^\[\s*(?P<bapo>ba|po)\s*(?:\+\s*(?P<offset>[0-9a-f]{1,8}))?\s*\]\s*:=\s*(?P<type>[bhw])\s*(?P<value>[0-9a-f]{1,8})\s*(?:\*\*(?P<times>[0-9a-f]{1,4}))?$', re.IGNORECASE), flowWriteToMem ],
    [ re.compile(r'^\[\s*(?P<bapo>ba|po)\s*(?:\+\s*(?P<offset>[0-9a-f]{1,8}))?\s*\]\s*:=\s*\[\s*gr(?P<register>[0-9a-f])\s*\]\s*(?:\*\*(?P<times>[0-9a-f]+))?$', re.IGNORECASE), flowMemcpy1],
    [ re.compile(r'^\[\s*gr(?P<register>[0-9a-f])\s*\]\s*:=\s*\[\s*(?P<bapo>ba|po)(?:\s*\+\s*(?P<offset>[0-9a-f]{1,8}))?\s*\]\s*(?:\*\*(?P<times>[0-9a-f]+))?$', re.IGNORECASE), flowMemcpy2],
    [ re.compile(r'^\[\s*gr(?P<destRegister>[0-9a-f])\s*\]\s*:=\s*\[\s*gr(?P<register>[0-9a-f])\s*(?:\+\s*(?P<offset>[0-9a-f]{1,8}))?\s*\]\s*(?:\*\*(?P<times>[0-9a-f]+))?$', re.IGNORECASE), flowMemcpy21],
    [ re.compile(r'^\[\s*gr(?P<destRegister>[0-9a-f])\s*(?:\+\s*(?P<offset>[0-9a-f]{1,8}))?\s*\]\s*:=\s*\[\s*gr(?P<register>[0-9a-f])\s*\]\s*(?:\*\*(?P<times>[0-9a-f]+))?$', re.IGNORECASE), flowMemcpy11],
    [ re.compile(r'^\[\s*(?P<bapo>ba\s*|po\s*)?\s*\+?\s*(?:(?P<offset>[0-9a-f]{1,8}))?\s*\]\s*:=\s*(?P<type>[bhw])\s*gr(?P<register>[0-9a-f])\s*(?:\*\*(?P<times>[0-9a-f]+))?$', re.IGNORECASE), flowStoreGR],
    [ re.compile(r'^([0-9a-z_]+):$', re.IGNORECASE), flowLabel ]
]

class Labels:
    def __init__(self, game):
        self.data = {}
        self.line = 0
        self.game = game
        self.versionFree = False
    def add(self, label):
        self.data[label] = self.line
    def incLine(self, amount=1):
        self.line += amount
    def distanceTo(self, label, fromLine):
        targetLine = self.data[label]
        distance = targetLine - fromLine
        if distance < 0:
            distance += 0x10000
        return "{0:0{1}X}".format(distance,4)

geckoLineReplacer = re.compile(r'((?P<value>[0-9a-fA-F]{1,8})\+)?\((?P<alias>\w+)(?P<and>&)?(?:\+(?P<add>[0-9a-f]+))?\)', re.IGNORECASE)

class AliasList:
    def __init__(self):
        self._data = {}
        self.games = []
    def add(self, alias, game, ptr):
        aliasDict = None
        if alias in self._data:
            aliasDict = self._data[alias]
        else:
            aliasDict = {}
            self._data[alias] = aliasDict
        if game in aliasDict:
            print (f'Error: duplicate entry for alias {alias} with game {game}')
            exit()
        aliasDict[game] = int(ptr, 16)
    def get(self, alias, game):
        if alias in self._data:
            d = self._data[alias]
            if game in d:
                return d[game]
            elif '*' in d:
                return d['*']
        return None
    def getMacrosForGame(self, game):
        for k in self._data:
            if game in self._data[k]:
                yield '.set {0}, 0x{1:0{2}X}'.format(k, self._data[k][game], 8)
            elif '*' in self._data[k]:
                yield '.set {0}, 0x{1:0{2}X}'.format(k, self._data[k]['*'], 8)
    def getGameList(self, filter):
        return [game for game in self.games if filter in game]
    def replaceInGecko(self, geckoLine, game):
        def groupOrDefault(groupname, match, default):
            return match.group(groupname) if groupname in match.groupdict() and match.group(groupname) else default
        def gRepl(matchobj):
            value = groupOrDefault('value', matchobj, '0')
            prefix = ''
            if value.upper() == 'BA':
                # Leave ba+ as base address instead of 0xBA
                value = '0'
                prefix = 'ba+'
            value = int(value, 16)
            adder = int(groupOrDefault('add', matchobj, '0'), 16)
            alias = matchobj.group('alias')
            aliasResult = self.get(alias, game)
            andPresent = groupOrDefault('and', matchobj, '')
            if not aliasResult is None:
                if andPresent:
                    aliasResult &= 0x01FFFFFF
                return prefix + '{0:0{1}X}'.format(value + aliasResult + adder, 8)
            return matchobj.group(0)
        return re.sub(geckoLineReplacer, gRepl, geckoLine)

def getAliasList(xmlPath, errPrint):
    aliasList = AliasList()
    root = ET.parse(xmlPath).getroot()
    for node in root:
        if node.tag == 'Address':
            for ptr in node:
                aliasList.add(node.attrib['Alias'], ptr.attrib['Game'], ptr.text)
        elif node.tag == 'Game':
            aliasList.games.append(node.attrib['Id'])
        else:
            orNop(errPrint, f'Unknown node type in alias xml: {node.tag}')
    return aliasList

re_assert_game = re.compile(r'^!assertgame\s+(?P<game>(?:RVL-SOU[J|P|K|E]-0A-[0-2]\s*)+)$', re.IGNORECASE)
re_assert_versionfree = re.compile(r'^!assertgame\s+\*$', re.IGNORECASE)

class CheatCode:
    def __init__(self, name, game, aliasList):
        self.name = name
        self.labels = Labels(game)
        self.aliasList = aliasList
        self.tokens = []
        self.game = game
        self.aborted = False
        self.fullAborted = False
        self.versionFree = False
    def isEmpty(self):
        return len(self.tokens) == 0
    def lineLexer(self, line):
        def execute(doPrint, abortThisCode, abortAllCodes):
            def doAbortAll(err):
                self.aborted = True
                abortAllCodes(err)
            item = line.split('#')[0].strip()
            if self.aborted:
                orNop(abortThisCode, '')
            elif item:
                m = re_assert_game.match(line)
                if m:
                    if not (self.game in m.group('game').split()):
                        orNop(abortThisCode, f'Aborting code {self.name} for {self.game} because of assertgame directive.')
                else:
                    m = re_assert_versionfree.match(line)
                    if m:
                        self.versionFree = True
                        self.labels.versionFree = True
                    else:
                        item = self.aliasList.replaceInGecko(item, '*' if self.versionFree else self.game).lower()
                        for x in validators:
                            m = x[0].match(item)
                            if m:
                                self.labels.incLine()
                                self.tokens += list(x[1](m, self.labels, doPrint, doAbortAll))
                                if self.aborted:
                                    self.tokens = []
                                break
                        else:
                            orNop(abortAllCodes, f'Error: invalid syntax: "{item}" in {self.name}')
        return execute
    def lexer(self, file):
        def execute(abortAllCodes, printOut):
            if self.aborted:
                return
            self.currentErr = None
            def doAbortThisCode(err):
                self.aborted = True
                self.currentErr = err
            def doAbortAllCodes(err):
                self.fullAborted = True
                self.currentErr = err
            line = file.readline()
            while line:
                self.lineLexer(line)(printOut, doAbortThisCode, doAbortAllCodes)
                if self.aborted or self.fullAborted:
                    self.tokens = []
                if self.fullAborted:
                    self.aborted = True
                    if self.currentErr:
                        orNop(printOut, f'Fatal: {self.currentErr}')
                    orNop0(abortAllCodes)
                    return
                if self.aborted:
                    if self.currentErr:
                        orNop(printOut, f'Warning: skipping code {self.name}: {self.currentErr}')
                    return
                line = file.readline()
        return execute
    def getText(self):
        text = ''
        for item in self.tokens:
            text += item(self.labels).upper().strip() + '\n'
        return text