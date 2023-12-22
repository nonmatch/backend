import re

fakeness_scoring_rules = [
    {
        'regex': 'asm\(',
        'score': 5,
        'description': 'Direct asm() call'
    },
    {
        'regex': 'FORCE_REGISTER',
        'score': 5,
        'description': 'ORCE_REGISTER to force register allocation'
    },
    {
        'regex': 'MEMORY_BARRIER',
        'score': 3,
        'description': 'MEMORY_BARRIER to change register allocation'
    },
    {
        'regex': 'NON_MATCHING',
        'score': 3,
        'description': 'Check for NON_MATCHING define'
    },
    {
        'regex': 'goto',
        'score': 1,
        'description': 'goto'
    }
]

def calculate_fakeness_score(code: str):
    fakeness_score = 0
    for rule in fakeness_scoring_rules:
        for match in re.findall(rule['regex'], code):
            fakeness_score += rule['score']
    return fakeness_score