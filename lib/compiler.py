import operator
import re
from collections.abc import Iterable
from inspect import signature
from functools import wraps
from lib.functional import xmap, xflatten, xfilter, xreduce, xfirst, xstopifany, xreduceout, FuncList
from lib.compiler_syntax import validators

class Context:
    def __init__(self, game, name, aliases):
        self.game = game
        self.name = name
        self.aliases = aliases
        self.versionfree = False
        self.games = []

class ParsedGecko:
    def __init__(self, codelines, logs, errlevel, context):
        self.codelines = codelines
        self.logs = logs
        self.errlevel = errlevel
        self.context = context
    def codetext(self):
        return '\n'.join(map(lambda line: line.strip(), self.codelines))

class Token:
    def __init__(self, other=None):
        useother = not other is None
        self.raw = other.raw if useother else None
        self.geckoline = other.geckoline if useother else None
        self.rawline = other.rawline if useother else None
        self.stripped = other.stripped if useother else None
        self.parsed = other.parsed if useother else None
        self.fatal = other.fatal if useother else []
        self.lookup = other.lookup if useother else None
        self.label = other.label if useother else None
        self.info = other.info if useother else []
        self.warnings = other.warnings if useother else []
        self.context = other.context if useother else None
        self.errors = other.errors if useother else []
        self.versionfree = other.versionfree if useother else False
        self.isassertgame = other.isassertgame if useother else False
    def __len__(self):
        if isinstance(self.parsed, str):
            return 1 if self.parsed else 0
        elif isinstance(self.parsed, Iterable):
            return len(list(self.parsed))
        return 0 if hasattr(self.parsed, 'label') else 1
    def _addItem(self, collection, item):
        return collection + [item] if collection else [item]
    def addwarning(self, warn):
        self.warnings = self._addItem(self.warnings, warn)
    def addfatal(self, err):
        self.fatal = self._addItem(self.fatal, err)
    def addinfo(self, info):
        self.info = self._addItem(self.info, info)
    def adderror(self, err):
        self.errors = self._addItem(self.errors, err)

def compile(srccontents, context):
    def withRawLineNumbers(sofar, line):
        result = Token()
        result.raw = line
        result.rawline = sofar[-1].rawline + 1 if sofar else 1
        return sofar + [result]
    def stripCommentsAndTrivia(token):
        clone = Token(token)
        clone.stripped = token.raw.split('#')[0].strip()
        return clone
    def withVersionAssert(sofar, nexttoken):
        clone = Token(nexttoken)
        clone.context = context
        mgame = re.compile(r'^!assertgame\s+(?P<game>(?:RVL-SOU(?:[J|K]-0A-0|[E|P]-0A-[0-2])\s*)+)$', re.IGNORECASE).match(clone.stripped)
        mfree = re.compile(r'^!assertgame\s+\*$', re.IGNORECASE).match(clone.stripped)
        if len(sofar) == 0:
            if mgame:
                if not (context.game in mgame.group('game').split()):
                    clone.adderror(f'Aborting code {context.name} for {context.game} because of assertgame directive.')
                if not context.games:
                    context.games = mgame.group('game').split()
                clone.isassertgame = True
            elif mfree:
                clone.versionfree = True
                context.versionfree = True
                clone.isassertgame = True
        elif mgame or mfree:
            clone.addfatal(f'assertgame directive found after compiled code in {context.name}')
        return sofar + [clone]
    def handleAliases(token):
        clone = Token(token)
        clone.stripped = context.aliases.replace(clone.stripped, '*' if context.versionfree else context.game)
        return clone
    def parse(token):
        clone = Token(token)
        if not clone.isassertgame:
            for x in validators:
                m = x[0].match(clone.stripped)
                if m:
                    clone.parsed = [
                        lambda: x[1](),
                        lambda: x[1](m),
                        lambda: x[1](m, clone)
                    ][len(signature(x[1]).parameters)]()
                    if isinstance(clone.parsed, Iterable) and not isinstance(clone.parsed, str):
                        clone.parsed = list(clone.parsed)
                    break
            else:
                clone.addfatal(f'Error: invalid syntax: "{clone.stripped}"')
        return clone
    def withGeckoLineNumbers(sofar, nexttoken):
        clone = Token(nexttoken)
        clone.geckoline = sofar[-1].geckoline + len(sofar[-1]) if sofar else 0
        clone.lookup = sofar[-1].lookup if sofar else dict()
        clone.lookup[clone.label] = clone.geckoline
        return sofar + [clone]
    def toGecko(token):
        clone = Token(token)
        def convert_value(arg):
            if callable(arg):
                return arg(token).strip()
            elif isinstance(arg, str):
                return arg.strip()
            elif isinstance(arg, Iterable):
                return map(convert_value, arg)
            elif arg is None or not hasattr(arg, 'label'):
                token.addfatal(f'Unknown type output by parser')
            return None
        clone.parsed = convert_value(clone.parsed)
        return clone
    result = FuncList(srccontents.split('\n')).pipe(
        xreduce(withRawLineNumbers, []),                # Add raw line numbers.
        xmap(stripCommentsAndTrivia),                   # Remove comments and whitespace
        xfilter(lambda x: x.stripped),                  # Filter out empty lines
        xreduce(withVersionAssert, []),                 # Find any game version asserts
        xstopifany(lambda x: x.fatal or x.errors),      # Stop here if already any errors (so that a game assert can block a syntax error)
        xmap(handleAliases),                            # Replace aliases
        xmap(parse),                                    # Parse the tokens
        xreduce(withGeckoLineNumbers, []),              # Add gecko line number to tokens
        xmap(toGecko),                                  # Convert to gecko lines
        xflatten())                                     # Flatten any tokens that returned multiple gecko lines
    def aggregator(sofar, token):
        def mapper(level):
            class DisplayItem:
                severities = [ 'Info', 'Warning', 'Error', 'Fatal' ]
                def __init__(self, text):
                    self.text = text
                    self.rawline = token.rawline
                    self.errlevel = level
                def __str__(self):
                    return f'{DisplayItem.severities[level]}: (Code {context.name} game {context.game} line {token.rawline}) - {self.text}'
            return lambda text: DisplayItem(text)
        loglist = [token.info, token.warnings, token.errors, token.fatal]
        return sofar + [log for x in range(4) for log in map(mapper(x), loglist[x])]
    items = result.pipe(xreduce(aggregator, []))
    errlevel = items.maxBy(lambda x, y: x.errlevel - y.errlevel, None)
    textLines = result.pipe(
        xfilter(lambda x: not x.isassertgame and x.parsed),
        xmap(lambda x: (x.parsed if isinstance(x.parsed, str) else '\n'.join(x.parsed)) + '\n'),
        xreduceout(operator.add, '')
    ).strip().split('\n')
    return ParsedGecko(textLines, items.sortedBy(lambda x, y: x.rawline - y.rawline), errlevel.errlevel if errlevel else 0, context)