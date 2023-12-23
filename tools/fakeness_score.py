import re

fakeness_scoring_rules = [
    {
        'code': 'asm(',
        'score': 5,
        'description': 'Direct asm() call'
    },
    {
        'code': 'FORCE_REGISTER',
        'score': 5,
        'description': 'FORCE_REGISTER to force register allocation'
    },
    {
        'code': 'MEMORY_BARRIER',
        'score': 3,
        'description': 'MEMORY_BARRIER to change register allocation'
    },
    {
        'code': 'NON_MATCHING',
        'score': 2,
        'description': 'Check for NON_MATCHING define'
    },
    {
        'code': 'goto',
        'score': 1,
        'description': 'goto'
    }
]

first_chars = {}

for rule in fakeness_scoring_rules:
    first_chars[rule['code'][0]] = rule

def calculate_fakeness_score(code: str):
    scorer = FakenessScorer(code)
    return scorer.calculate_fakeness_score()

class FakenessScorer:
    code: str
    cursor: int
    fakeness_score: int
    
    def __init__(self, code: str):
        self.code = code
        self.cursor = 0
        self.fakeness_score = 0

    def calculate_fakeness_score(self) -> int:
        self.parse_code()
        return self.fakeness_score

    def parse_code(self):
        while self.cursor < len(self.code):
            char = self.code[self.cursor]

            if char == '/':
                if self.code[self.cursor+1] == '*':
                    self.cursor += 2
                    self.parse_block_comment()
                elif self.code[self.cursor+1] == '/':
                    self.cursor += 2
                    self.parse_line_comment()
                else:
                    self.cursor += 1
            else:
                if char in first_chars:
                    rule = first_chars[char]
                    if self.code[self.cursor:self.cursor + len(rule['code'])] == rule['code']:
                        self.fakeness_score += rule['score']
                        self.cursor += len(rule['code'])
                    else:
                        self.cursor +=1
                else:
                    self.cursor +=1

    def parse_block_comment(self):
        while self.cursor < len(self.code):
            if self.code[self.cursor] == '*' and self.code[self.cursor+1] == '/':
                self.cursor += 2
                return

            self.cursor += 1
        #raise Exception('Did not find end of block comment')

    def parse_line_comment(self):
        while self.cursor < len(self.code):
            if self.code[self.cursor] == '\n':
                self.cursor += 1
                return
            self.cursor += 1