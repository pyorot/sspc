import re

class Context:
    def __init__(self, game, name, printFunc, abortAllFunc):
        self.labels = {}
        self.line = 0
        self.game = game
        self.name = name
        self.versionFree = False
        self.printFunc = printFunc
        self.abortAllFunc = abortAllFunc
        self.allAborted = False
        self.aborted = False
    def abortAll(self, err):
        self.allAborted = True
        self.aborted = True
        self.printOut(err)
        if self.abortAllFunc:
            self.abortAllFunc()
    def abortThis(self, err):
        self.aborted = True
    def printOut(self, err):
        if self.printFunc:
            self.printFunc(err)
    def addLabel(self, label):
        self.labels[label] = self.line
    def incLine(self, amount=1):
        self.line += amount
    def formatWithDistance(self, fmtStr, label):
        fromLine = self.line + 1
        def getDist():
            targetLine = self.labels[label]
            distance = targetLine - fromLine
            if distance < 0:
                distance += 0x10000
                self.printOut(f'Warning: flow control using negative offset. This code may not work as intended. Label = {label}')
            distance = "{0:0{1}X}".format(distance, 4)
            return fmtStr.format(distance)
        return [getDist]

def flowGoto(match, context):
    return context.formatWithDistance("6600{0} 00000000", match.group(1))

def flowReturn(match, context):
    yield "64000000 0000000{0}".format(match.group(1))

def flowGosub(match, context):
    return context.formatWithDistance("6800{0} 0000000" + match.group(1), match.group(2))

def flowLabel(match, context):
    context.addLabel(match.group(1))
    context.incLine(-1)
    return []

def flowGecko(match, context):
    yield match.group(1)

def flowAsm(match, context):
    try:
        expandname = match.group(1)
        context.incLine(-1)
        game = '.free' if context.versionFree else context.game
        with open(f'build-asm/{game}/{expandname}.gecko', 'r') as expandfile:
            for line in expandfile:
                yield line.lower()
                context.incLine()
        context.printOut(f'Info: expanded file: {game}/{expandname}.asm')
    except FileNotFoundError:
        context.abortAll(f'Error: expansion file not found: {expandname}.asm')

def flowAssignLiteralToGR(match, context):
    register = match.group(1)
    value = int(match.group(2), 16)
    yield "8000000{0} {1:0{2}X}".format(register, value, 8)

typeConvert = {
    'b': 0,
    'h': 1,
    'w': 2
}

def flowLoadMemToGR(match, context):
    register = match.group(1)
    typeChar = match.group(2)
    address = match.group(3)
    yield "82{0}0000{1} {2}".format(typeConvert[typeChar], register, address)

def flowWriteToMem(match, context):
    match = match.groupdict()
    start = 16 if 'bapo' in match and match['bapo'] == 'po' else 0
    typeChar = typeConvert[match['type']]
    maxValue = 2**(2**(typeChar + 3))               # max (exclusive) value
    typeByte = typeChar * 2 + start                 # first byte of command
    value = match['value']
    valueInt = int(value, 16)
    if valueInt >= maxValue:
        matchType = match['type']
        context.abortAll(f'Error: assigning value {value} is out of bounds for type {matchType}')
        return iter([])
    sourceAddress = int(match['offset'], 16) if 'offset' in match and match['offset'] else 0
    if sourceAddress > 0x01FFFFFF:
        context.abortAll('Error: address offset greater than 0x01FFFFFF cannot be encoded.')
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
            context.abortAll('Error: cannot specify repeated placement for word-sized values.')
            return iter([])
        halfline2 = "{0:0{1}X}".format(valueInt, 8)
    yield f'{halfline1} {halfline2}'

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
        abortAllCodes('Error: address offset greater than 0x01FFFFFF cannot be encoded.')
        return iter([])
    if pointerOffset > 0x00FFFFFF:
        firstByte += 1
        pointerOffset -= 0x01000000
    yield "{0:X}{1:0{2}X}{3} {4:0{5}X}".format(firstByte, int(times, 16), 4, lastByte, pointerOffset, 8)

def flowMemcpy1(match, context):
    return flowMemcpy(match.groupdict(), False, False, context.abortAll)

def flowMemcpy11(match, context):
    return flowMemcpy(match.groupdict(), True, False, context.abortAll)

def flowMemcpy2(match, context):
    return flowMemcpy(match.groupdict(), False, True, context.abortAll)

def flowMemcpy21(match, context):
    return flowMemcpy(match.groupdict(), True, True, context.abortAll)

def flowStoreGR(match, context):
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
    
    startByte = "{0:0{1}X}".format(0x84 + (16 if po else 0), 2)
    typeDigit = typeConvert[t]
    baseDigit = 1 if bapo else 0
    timesValue = "{0:0{1}X}".format(int(times,16) - 1, 3)
    offset = "{0:0{1}X}".format(int(offset, 16), 8)
    yield f"{startByte}{typeDigit}{baseDigit}{timesValue}{register} {offset}"

validators = [
    [ re.compile(r'^([0-9a-f]{8}\s[0-9a-f]{8})$', re.IGNORECASE), flowGecko ],
    [ re.compile(r'^{([0-9a-z\-]+).asm}$', re.IGNORECASE), flowAsm ],
    [ re.compile(r'^gosub\s+([0-9a-f])\s+([0-9a-z_]+)$', re.IGNORECASE), flowGosub ],
    [ re.compile(r'^goto\s+([0-9a-z_]+)$', re.IGNORECASE), flowGoto ],
    [ re.compile(r'^return\s+([0-9a-f])$', re.IGNORECASE), flowReturn ],
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