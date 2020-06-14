import re
import yaml
from functools import wraps
from yaml.nodes import ScalarNode,SequenceNode,MappingNode
from collections.abc import Iterable

def defaultctor(basector, node):
    if isinstance(node, ScalarNode):
        return basector.construct_scalar(node)
    elif isinstance(node, SequenceNode):
        return basector.construct_sequence(node)
    elif isinstance(node, MappingNode):
        return basector.construct_mapping(node)
    return None

class AliasData:
    def __init__(self, alias):
        self.alias = alias
        self.data = {}
        self.universal = None
    def setvalue(self, version, scalar):
        if isinstance(scalar, int):
            scalar = str(scalar)
        if version == '*':
            self.universal = scalar
        else:
            self.data[version] = scalar
    def getvalue(self, version):
        toconvert = self.universal if version == '*' or not version in self.data else self.data[version]
        return int(toconvert, 16) if isinstance(toconvert, str) else toconvert
    def getmacro(self, version):
        value = self.getvalue(version)
        return f'.set {self.alias}, 0x{value:08X}' if value else ''

class AliasList:
    def __init__(self, games, aliases):
        self.games = games
        self.aliases = aliases
        self.geckoLineReplacer = re.compile(r'((?P<source>[0-9a-f]{1,8})\s*(?P<or>\|))?\<(?P<alias>\w+)(?:\+(?P<add>[0-9a-f]+))?\>', re.IGNORECASE)
    def get(self, alias, game):
        return self.aliases[alias].getvalue(game) if alias in self.aliases else None
    def replace(self, text, version):
        def groupOrDefault(groupname, match, default):
            return match.group(groupname) if groupname in match.groupdict() and match.group(groupname) else default
        def gRepl(matchobj):
            value = groupOrDefault('source', matchobj, '0')
            prefix = ''
            if value.upper() == 'BA':
                # Leave ba+ as base address instead of 0xBA
                value = '0'
                prefix = 'ba|'
            value = int(value, 16)
            aliasResult = self.get(matchobj.group('alias'), version)
            andPresent = groupOrDefault('or', matchobj, '')
            if not aliasResult is None:
                if andPresent:
                    aliasResult %= 0x02000000
                return prefix + f'{value + aliasResult + int(groupOrDefault("add", matchobj, "0"), 16):08X}'
            return matchobj.group(0)
        return re.sub(self.geckoLineReplacer, gRepl, text)
    def getMacrosForGame(self, game):
        for k in self.aliases:
            m = self.aliases[k].getmacro(game)
            if m:
                yield m
    def getGameList(self, filter):
        return [game for game in self.games if filter in game]

def filector(basector, node):
    if len(node.value) > 1 and len(node.value[1]) and node.value[1][0].value == 'addresses':
        games = defaultctor(basector, SequenceNode(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, [node.value[0][1]]))
        d = dict()
        for value in MappingNode(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, node.value[1][1].value).value:
            result = AliasData(defaultctor(basector, value[0]))
            nextnode = value[1]
            if isinstance(nextnode, ScalarNode):
                result.setvalue('*', nextnode.value)
            else:
                for v in nextnode.value:
                    result.setvalue(defaultctor(basector, v[0]), defaultctor(basector, v[1]))
            d[result.alias] = result
        return AliasList(games[0], d)
    return defaultctor(basector, node)

def read_aliases(file):
    yaml.SafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, filector)
    with open(file) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)