from dataclasses import dataclass
from typing import Optional
from sortedcontainers import SortedKeyList
from sortedcontainers.sortedlist import SortedList
from subprocess import check_output
import os

ROM_OFFSET=0x08000000
@dataclass
class Symbol:
    address: int = 0
    name: str = None
    file: str = None
    length: int = 0

class SymbolList:
    symbols: SortedKeyList[Symbol]

    def __init__(self, symbols: SortedKeyList[Symbol]) -> None:
        self.symbols = symbols

    def get_symbol_at(self, local_address: int) -> Optional[Symbol]:
        if len(self.symbols) == 0:
            return None
        index = self.symbols.bisect_key_right(local_address)
        return self.symbols[index-1]

    def get_symbol_after(self, local_address: int) -> Optional[Symbol]:
        if len(self.symbols) == 0:
            return None
        index = self.symbols.bisect_key_right(local_address)
        return self.symbols[index]

    def find_symbol_by_name(self, name: str) -> Optional[Symbol]:
        for symbol in self.symbols:
            if symbol.name == name:
                return symbol
        return None


def load_symbols_from_elf() -> SymbolList:
    symbols = SortedKeyList([], key=lambda x:x.address)

    output = check_output(['readelf', '--debug-dump=info', os.path.join(os.getenv('TMC_REPO'),'tmc.elf')], universal_newlines=True)

    IGNORE = 0
    SUBPROGRAM = 1
    COMPILE_UNIT = 2
    VARIABLE = 3
    tag = IGNORE
    current_file = 'UNKNOWN'
    current_name = ''
    prev_symbol = None

    for line in output.split('\n'):
        if 'Abbrev Number' in line:
            if 'DW_TAG_subprogram' in line:
                tag = SUBPROGRAM
            elif 'DW_TAG_compile_unit' in line:
                tag = COMPILE_UNIT
            # TODO is the address of the variables stored in the dwarf info?
            # elif 'DW_TAG_variable' in line:
            #     tag = VARIABLE
            else:
                tag = IGNORE
        if tag == IGNORE:
            continue
        elif tag == SUBPROGRAM:
            if 'DW_AT_name' in line:
                current_name = line.split(':')[1].strip()
            elif 'DW_AT_low_pc' in line:
                addr = int(line.split(':')[1].strip(),16)-ROM_OFFSET
                if prev_symbol is not None:
                    prev_symbol.length = addr-prev_symbol.address
                symbol = Symbol(addr, current_name, current_file)
                symbols.add(symbol)
                prev_symbol = symbol
        elif tag == COMPILE_UNIT:
            if 'DW_AT_name' in line:
                current_file = line.split(':')[1].strip()

    return SymbolList(symbols)