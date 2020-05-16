import re

negative_digits = ['8','9','A','B','C','D','E','F']

def wrap(s):
    return lambda l: s

def distanceTo(st, label, fromLine):
    def getDist(labels):
        distance = labels.distanceTo(label, fromLine + 1)
        if distance[0] in negative_digits:
            print('Warning: flow control using negative offset. This code may not work as intended. Label = {0}'.format(label))
        return st.format(distance)
    yield getDist

def flowGoto(match, labels):
    return distanceTo("6600{0} 00000000", match.group(1), labels.line)

def flowReturn(match, labels):
    yield wrap("64000000 0000000{0}".format(match.group(1)))

def flowGosub(match, labels):
    return distanceTo("6800{0} 0000000" + match.group(1), match.group(2), labels.line)

def flowLabel(match, labels):
    labels.add(match.group(1))
    labels.incLine(-1)
    return []

def flowGecko(match, labels):
    yield wrap(match.group(1))

def flowAsm(match, labels):
    try:
        expandname = match.group(1)
        labels.incLine(-1)
        with open(f'build-asm/{expandname}.gecko', 'r') as expandfile:
            for line in expandfile:
                yield wrap(line.lower())
                labels.incLine()
        print(f'Info: expanded file: {expandname}.asm')
    except FileNotFoundError:
        print(f'Error: expansion file not found: {expandname}.asm')
        exit()

def flowAssignLiteralToGR(match, labels):
    register = match.group(1)
    value = int(match.group(2), 16)
    yield wrap("8000000{0} {1:0{2}X}".format(register, value, 8))

typeConvert = {
    'b': 0,
    'h': 1,
    'w': 2
}

def flowLoadMemToGR(match, labels):
    register = match.group(1)
    typeChar = match.group(2)
    address = match.group(3)
    yield wrap("82{0}0000{1} {2}".format(typeConvert[typeChar], register, address))

def flowWriteToMem(match, labels):
    match = match.groupdict()
    start = 16 if 'bapo' in match and match['bapo'] == 'po' else 0
    typeChar = typeConvert[match['type']]
    maxValue = 2**(2**(typeChar + 3))               # max (exclusive) value
    typeByte = typeChar * 2 + start                 # first byte of command
    value = match['value']
    valueInt = int(value, 16)
    if valueInt >= maxValue:
        print('Error: assigning value {0} is out of bounds for type {1}'.format(value, match['type']))
        exit()
    sourceAddress = int(match['offset'], 16) if 'offset' in match and match['offset'] else 0
    if sourceAddress > 0x01FFFFFF:
        print('Error: address offset greater than 0x01FFFFFF cannot be encoded.')
        exit()
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
            print('Error: cannot specify repeated placement for word-sized values.')
            exit()
        halfline2 = "{0:0{1}X}".format(valueInt, 8)
    yield wrap("{0} {1}".format(halfline1, halfline2))

def flowMemcpy(match, betweenRegisters, offsetOnSource):
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
        lastByte = "{0}{1}".format(sourceRegister, destRegister)
    firstByte += (16 if po else 0)
    pointerOffset = int(offset, 16)
    if pointerOffset > 0x01FFFFFF:
        print('Error: address offset greater than 0x01FFFFFF cannot be encoded.')
        exit()
    if pointerOffset > 0x00FFFFFF:
        firstByte += 1
        pointerOffset -= 0x01000000
    yield wrap("{0:X}{1:0{2}X}{3} {4:0{5}X}".format(firstByte, int(times, 16), 4, lastByte, pointerOffset, 8))

def flowMemcpy1(match, labels):
    return flowMemcpy(match.groupdict(), False, False)

def flowMemcpy11(match, labels):
    return flowMemcpy(match.groupdict(), True, False)

def flowMemcpy2(match, labels):
    return flowMemcpy(match.groupdict(), False, True)

def flowMemcpy21(match, labels):
    return flowMemcpy(match.groupdict(), True, True)

def flowStoreGR(match, labels):
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
    def __init__(self):
        self.data = {}
        self.line = 0
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

class CheatCode:
    def __init__(self, name):
        self.name = name
        self.labels = Labels()
        self.tokens = []
    def isEmpty(self):
        return len(self.tokens) == 0
    def lexLine(self, line):
        item = line.split('#')[0].strip().lower()
        if item:
            for x in validators:
                m = x[0].match(item)
                if m:
                    self.labels.incLine()
                    self.tokens += list(x[1](m, self.labels))
                    break
            else:
                print(f'Error: invalid syntax: "{item}" in {self.name}')
                return False
        return True
    def lex(self, file):
        line = file.readline()
        while line:
            if not self.lexLine(line):
                return False
            line = file.readline()
        return True
    def getText(self):
        text = ''
        for item in self.tokens:
            text += item(self.labels).upper().strip() + '\n'
        return text