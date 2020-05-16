import unittest
import os
import compiler

class CompilerTestCases(unittest.TestCase):
    def lineTest(self, text, expectedResult, expectFail=False, expectEmpty=False):
        code = compiler.CheatCode('name')
        passed = code.lexLine(text)
        if expectFail:
            self.assertFalse(passed)
        else:
            actualText = code.getText()
            if expectEmpty:
                self.assertTrue(code.isEmpty())
            self.assertEqual(expectedResult, actualText.strip())
    def fileTest(self, text, expectedResult):
        code = compiler.CheatCode('name')
        class FileMock:
            def __init__(self, text):
                self.text = text.split('\n')
                self.line = 0
            def readline(self):
                if self.line < len(self.text):
                    line = self.text[self.line]
                    self.line += 1
                    return line + '\n'
                return None
        file = FileMock(text)
        self.assertTrue(code.lex(file))
        self.assertEqual(code.getText().strip(), expectedResult)
    def test_invalid_syntax(self):
        self.lineTest('int main(int argc, char** argv) {', '', True)
    def test_empty_line(self):
        self.lineTest('', '', False, True)
    def test_empty_file(self):
        self.fileTest('', '')
    def test_gecko(self):
        self.lineTest('0000159C 00010004', '0000159C 00010004')
    def test_gecko_with_comment(self):
        self.lineTest('  0000159C 00010004  # A comment of some sort', '0000159C 00010004')
    def test_asm(self):
        tmpfilename = 'tmp-test'
        with open('build-asm/{0}.gecko'.format(tmpfilename), 'w') as asmfile:
            asmfile.write('''C0000000 00000001
4E800020 00000000''')
        self.fileTest('''00001500 00000000
{0}
00001501 00000000'''.format('{' + tmpfilename + '.asm}'), '''00001500 00000000
C0000000 00000001
4E800020 00000000
00001501 00000000''')
        os.remove('build-asm/{0}.gecko'.format(tmpfilename))
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