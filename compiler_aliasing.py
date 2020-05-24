import re
import xml.etree.ElementTree as ET

class AliasList:
    def __init__(self):
        self._data = {}
        self.games = []
        self.geckoLineReplacer = re.compile(r'((?P<value>[0-9a-fA-F]{1,8})\+)?\((?P<alias>\w+)(?P<and>&)?(?:\+(?P<add>[0-9a-f]+))?\)', re.IGNORECASE)
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
        return re.sub(self.geckoLineReplacer, gRepl, geckoLine)

def getAliasListFromXml(xmlPath, errPrint):
    aliasList = AliasList()
    root = ET.parse(xmlPath).getroot()
    for node in root:
        if node.tag == 'Address':
            for ptr in node:
                aliasList.add(node.attrib['Alias'], ptr.attrib['Game'], ptr.text)
        elif node.tag == 'Game':
            aliasList.games.append(node.attrib['Id'])
        elif errPrint:
            errPrint(f'Unknown node type in alias xml: {node.tag}')
    return aliasList

aliasparsers = {
    'xml': getAliasListFromXml
}

def getAliasList(path, errPrint):
    extension = path[path.rindex('.') + 1:]
    parser = aliasparsers[extension] if extension in aliasparsers else None
    if parser:
        return parser(path, errPrint)
    errPrint(f'Unknown file type for alias list: .{extension}')