import unittest
import os
from compiler import CheatCode
from compiler_syntax import Context
from compiler_aliasing import getAliasList

class Flag:
    def __init__(self):
        self.isSet = False
        self.printLevel = 0
    def set(self, err):
        self.setNoErr()
        self.errNoSet(err)
    def setNoErr(self):
        self.isSet = True
    def errNoSet(self, err):
        if self.printLevel > 0:
            print (err)

class CompilerTestCases(unittest.TestCase):
    def setUp(self):
        self.aliases = getAliasList('src/aliases.xml', None)
    def newCode(self, game):
        ctx = Context(game, 'name', self.flag.errNoSet, self.flag.setNoErr)
        return CheatCode(ctx, self.aliases)
    def lineTest(self, text, expectedResult, opts = {}):
        self.flag = Flag()
        expectFail = opts['expectfail'] if 'expectfail' in opts else False
        expectFailAll = opts['expectfailall'] if 'expectfailall' in opts else False
        expectEmpty = opts['expectempty'] if 'expectempty' in opts else False
        game = opts['game'] if 'game' in opts else 'RVL-SOUJ-0A-0'
        code = self.newCode(game)
        code.lexLine(text)
        self.flag.errNoSet(f'Parsing {text} and ef = {expectFail} and efa = {expectFailAll} and aborted is {code.context.aborted}')
        self.assertEqual(expectFail or expectFailAll, code.context.aborted)
        self.assertEqual(expectFailAll, self.flag.isSet and code.context.allAborted)
        if not (expectFail or expectFailAll):
            actualText = code.getText()
            if expectEmpty:
                self.assertTrue(code.isEmpty())
            self.assertEqual(expectedResult, actualText.strip())
    def fileTest(self, text, expectedResult, opts = {}):
        self.flag = Flag()
        game = opts['game'] if 'game' in opts else 'RVL-SOUJ-0A-0'
        expectfailall = opts['expectfailall'] if 'expectfailall' in opts else False
        code = self.newCode(game)
        code.lexFile(map(lambda l: l.strip(), text.split('\n')))
        self.assertEqual(expectfailall, self.flag.isSet)
        self.assertEqual(code.getText().strip(), expectedResult)
    def lineTestAlias(self, text, expectedResult, game = 'RVL-SOUJ-0A-0'):
        self.lineTest(text, expectedResult, { 'game': game })
    def test_failed_gameassert(self):
        self.lineTest('!assertgame RVL-SOUE-0A-0', '', { 'expectfail': True })
    def test_versionfree_gameassert_fail(self):
        self.fileTest('''!assertgame *
82000000 (ReloaderPtr)''', '', { 'expectfailall': True })
    def test_versionfree_gameassert_pass(self):
        self.fileTest('''!assertgame *
82000000 (CurrentFiles)''', '82000000 8095545C')
    def test_invalid_syntax(self):
        self.lineTest('int main(int argc, char** argv) {', '', { 'expectfailall': True })
    def test_empty_line(self):
        self.lineTest('', '', { 'expectempty': True })
    def test_empty_file(self):
        self.fileTest('', '')
    def test_gecko(self):
        self.lineTest('0000159C 00010004', '0000159C 00010004')
    def test_gecko_with_comment(self):
        self.lineTest('  0000159C 00010004  # A comment of some sort', '0000159C 00010004')
    def test_asm(self):
        tmpfilename = 'tmp-test'
        gameFolder = 'build-asm/RVL-SOUJ-0A-0'
        geckopath = f'{gameFolder}/{tmpfilename}.gecko'
        if not os.path.exists(gameFolder): os.mkdir(gameFolder)
        with open(geckopath, 'w') as asmfile:
            asmfile.write('''C0000000 00000001
4E800020 00000000''')
        self.fileTest('''00001500 00000000
{0}
00001501 00000000'''.format('{' + tmpfilename + '.asm}'), '''00001500 00000000
C0000000 00000001
4E800020 00000000
00001501 00000000''')
        os.remove(geckopath)
    def test_gosub(self):
        input = '''gosub 5 a_label
        00001500 000000FF
        a_label:
        E0000000 80008000'''
        expected = '''68000001 00000005
00001500 000000FF
E0000000 80008000'''
        self.fileTest(input, expected)
    def test_gosub_negative_offset(self):
        input = '''a_label:
        00001400 000000FF
        00001500 000000FF
        gosub 6 a_label
        E0000000 80008000'''
        expected = '''00001400 000000FF
00001500 000000FF
6800FFFD 00000006
E0000000 80008000'''
        self.fileTest(input, expected)
    def test_goto(self):
        input = '''goto a_label
        00001500 000000FF
        a_label:
        E0000000 80008000'''
        expected = '''66000001 00000000
00001500 000000FF
E0000000 80008000'''
        self.fileTest(input, expected)
    def test_return(self):
        self.lineTest('return A', '64000000 0000000A')
    def test_assign_literal(self):
        self.lineTest(' grA := deadbeef', '8000000A DEADBEEF')
        self.lineTest('grA:=deadbeef', '8000000A DEADBEEF')
    def test_load_into_gr(self):
        self.lineTest('grB:=b[80001500]', '8200000B 80001500')
        self.lineTest('grB := b [ 80001500 ]', '8200000B 80001500')
        self.lineTest('grB:=h[80001500]', '8210000B 80001500')
        self.lineTest('grB := h [ 80001500 ]', '8210000B 80001500')
        self.lineTest('grB:=w[80001500]', '8220000B 80001500')
        self.lineTest('grB := w [ 80001500 ]', '8220000B 80001500')
    def test_tmp(self):
        self.lineTestAlias('[ba+(EmptyA&+00A0)] := w gr0', '84210000 000015A0')
    def test_aliases(self):
        self.lineTestAlias('28000000+(InputBuffer&) 40000001', '2859CF8C 40000001')
        self.lineTestAlias('28000000+(InputBuffer&) 40000001', '2859B48C 40000001', 'RVL-SOUP-0A-1')
        self.lineTestAlias('28000000+(InputBuffer&) 40000001', '2859B28C 40000001', 'RVL-SOUP-0A-0')

        self.lineTestAlias('[gr5] := [ba+(ReloaderPtr&)]', '8C0001F5 005789F4')
        self.lineTestAlias('[gr5] := [ba+(ReloaderPtr&)]', '8C0001F5 00576ED4', 'RVL-SOUP-0A-1')
        self.lineTestAlias('[gr5] := [ba+(ReloaderPtr&)]', '8C0001F5 00576D34', 'RVL-SOUP-0A-0')

        self.lineTestAlias('grB:=b[(LoadMeta)]', '8200000B 805B6B2E')
        self.lineTestAlias('grB:=b[(LoadMeta)]', '8200000B 805B5002', 'RVL-SOUP-0A-1')
        self.lineTestAlias('grB:=b[(LoadMeta)]', '8200000B 805B4E02', 'RVL-SOUP-0A-0')

        self.lineTestAlias('[gr5] := [ba+(ReloaderPtr&+A)]', '8C0001F5 005789FE')
        self.lineTestAlias('[gr5] := [ba+(ReloaderPtr&+A)]', '8C0001F5 00576EDE', 'RVL-SOUP-0A-1')
        self.lineTestAlias('[gr5] := [ba+(ReloaderPtr&+A)]', '8C0001F5 00576D3E', 'RVL-SOUP-0A-0')
    def test_write_mem(self):
        tests = [
            [ '[ba+1500]:=bCD', '00001500 000000CD' ],
            [ '[ ba + 1500 ] := b CD', '00001500 000000CD' ],
            [ '[ba+1500]:=bCD**1F', '00001500 001E00CD' ],
            [ '[ ba + 1500 ] := b CD **1F', '00001500 001E00CD' ],
            [ '[ba+1500]:=h1A1A', '02001500 00001A1A' ],
            [ '[ ba + 1500 ] := h 1A1A', '02001500 00001A1A' ],
            [ '[ba+1500]:=h1A1A**1F', '02001500 001E1A1A' ],
            [ '[ ba + 1500 ] := h 1A1A **1F', '02001500 001E1A1A' ],
            [ '[ba+1500]:=w2B2B3C3C', '04001500 2B2B3C3C' ],
            [ '[ ba + 1500 ] := w 2B2B3C3C', '04001500 2B2B3C3C' ]
        ]
        for case in tests:
            self.lineTest(case[0], case[1])
            self.lineTest(case[0].replace('ba', 'po', 1), '1' + case[1][1:])
            self.lineTest(case[0].replace('ba+1500', 'ba', 1).replace('ba + 1500', 'ba', 1), case[1].replace('1500', '0000'))
            self.lineTest(case[0].replace('ba+1500', 'po', 1).replace('ba + 1500', 'po', 1), '1' + case[1].replace('1500', '0000')[1:])
    def test_memcpy(self):
        tests = [
            [ '[gr5]:=[ba+1500]', '8C0001F5 00001500' ],
            [ ' [ gr5 ] := [ ba + 1500 ] ', '8C0001F5 00001500' ],
            [ '[gr5]:=[ba+1500]**4', '8C0004F5 00001500' ],
            [ ' [ gr5 ] := [ ba + 1500 ] **4', '8C0004F5 00001500' ],
            [ '[ba+1500]:=[gr3]', '8A00013F 00001500'],
            [ ' [ ba + 1500 ] := [ gr3 ] ', '8A00013F 00001500'],
            [ '[ba+1500]:=[gr3]**A', '8A000A3F 00001500'],
            [ ' [ ba + 1500 ] := [ gr3 ] **A', '8A000A3F 00001500']
        ]
        for case in tests:
            self.lineTest(case[0], case[1])
            self.lineTest(case[0].replace('ba', 'po', 1), '9' + case[1][1:])
            self.lineTest(case[0].replace('ba+1500', 'ba', 1).replace('ba + 1500', 'ba', 1), case[1].replace('1500', '0000'))
            self.lineTest(case[0].replace('ba+1500', 'po', 1).replace('ba + 1500', 'po', 1), '9' + case[1].replace('1500', '0000')[1:])
    def test_memcpy_between_registers(self):
        self.lineTest('[gr4]:=[gr7]', '8C000174 00000000')
        self.lineTest(' [ gr4 ] := [ gr7 ] ', '8C000174 00000000')
        self.lineTest('[gr4]:=[gr7]**BB', '8C00BB74 00000000')
        self.lineTest(' [ gr4 ] := [ gr7 ] **BB', '8C00BB74 00000000')

        self.lineTest('[gr6+3C]:=[gr9]', '8A000196 0000003C')
        self.lineTest('[ gr6 + 3C ] := [ gr9 ]', '8A000196 0000003C')
        self.lineTest('[gr6+3C]:=[gr9]**F6', '8A00F696 0000003C')
        self.lineTest('[ gr6 + 3C ] := [ gr9 ] **F6', '8A00F696 0000003C')
        
        self.lineTest('[gr6]:=[gr9+3C]', '8C000196 0000003C')
        self.lineTest(' [ gr6 ] := [ gr9 + 3C ]', '8C000196 0000003C')
        self.lineTest('[gr6]:=[gr9+3C]**F6', '8C00F696 0000003C')
        self.lineTest(' [ gr6 ] := [ gr9 + 3C ] **F6', '8C00F696 0000003C')
    def test_store_gr_edge_case(self):
        # These cases are to make sure that a simple [ba] is interpreted as [base address] and not as [0xBA] but that [0ba] is interpreted as [0xBA]
        self.lineTest('[ba]:=bgrA', '8401000A 00000000')
        self.lineTest('[ ba ] := b grA', '8401000A 00000000')
        self.lineTest('[ba]:=bgrA**3C', '840103BA 00000000')
        self.lineTest('[ ba ] := b grA **3C', '840103BA 00000000')

        self.lineTest('[0ba]:=bgrA', '8400000A 000000BA')
        self.lineTest('[ 0ba ] := b grA', '8400000A 000000BA')
        self.lineTest('[0ba]:=bgrA**3C', '840003BA 000000BA')
        self.lineTest('[ 0ba ] := b grA **3C', '840003BA 000000BA')
    def test_temp(self):
        self.lineTest('[po]:=bgrA', '9401000A 00000000')
    def test_store_gr(self):
        tests = [
            [ '[ba+001500]:=bgrA', '8401000A 00001500' ],
            [ '[ ba + 001500 ] := b grA', '8401000A 00001500' ],
            [ '[ba+001500]:=bgrA**1C', '840101BA 00001500' ],
            [ '[ ba + 001500 ] := b grA **1C', '840101BA 00001500' ],
            [ '[ba+001500]:=hgrA', '8411000A 00001500' ],
            [ '[ ba + 001500 ] := h grA', '8411000A 00001500' ],
            [ '[ba+001500]:=hgrA**1C', '841101BA 00001500' ],
            [ '[ ba + 001500 ] := h grA **1C', '841101BA 00001500' ],
            [ '[ba+001500]:=wgrA', '8421000A 00001500' ],
            [ '[ ba + 001500 ] := w grA', '8421000A 00001500' ],
            [ '[ba+001500]:=wgrA**1C', '842101BA 00001500' ],
            [ '[ ba + 001500 ] := w grA **1C', '842101BA 00001500' ]
        ]
        for case in tests:
            self.lineTest(case[0], case[1])
            self.lineTest(case[0].replace('ba', 'po', 1), '9' + case[1][1:])
            self.lineTest(case[0].replace('ba+001500', 'ba', 1).replace('ba + 001500', 'ba', 1), case[1].replace('1500', '0000'))
            self.lineTest(case[0].replace('ba+001500', 'po', 1).replace('ba + 001500', 'po', 1), '9' + case[1].replace('1500', '0000')[1:])
            self.lineTest(case[0].replace('ba+', '', 1).replace('ba + ', '', 1), case[1][:3] + '0' + case[1][4:])

if __name__ == '__main__':
    unittest.main()