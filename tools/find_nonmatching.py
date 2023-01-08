import os
import re
import sys
from typing import List, Optional, Tuple

import requests

from models.function import Function
from models import db
from models.submission import Submission
from repositories.submission import SubmissionRepository
from sqlalchemy import desc

from tools.symbols import SymbolList, load_symbols_from_elf
from tools.symbols_from_map import load_symbols_from_map
import difflib
from flask import current_app


def collect_non_matching_funcs():
    result = []
    src_folder = os.path.join(current_app.config['TMC_REPO'], "src")
    for root, dirs, files in os.walk(src_folder):
        for file in files:
            if file.endswith(".c"):
                with open(os.path.join(root, file), "r") as f:
                    data = f.read()
                    # Find all NONMATCH macros
                    for match in re.findall(
                        r'NONMATCH\(".*",(?: static)?\W*\w*\W*(\w*).*\)', data
                    ):
                        result.append(
                            (
                                os.path.relpath(os.path.join(root, file), src_folder),
                                match,
                            )
                        )
    return result


def collect_asm_funcs():
    result = []
    src_folder = os.path.join(current_app.config['TMC_REPO'], "src")
    for root, dirs, files in os.walk(src_folder):
        for file in files:
            if file.endswith(".c"):
                with open(os.path.join(root, file), "r") as f:
                    data = f.read()
                    # Find all ASM_FUNC macros
                    for match in re.findall(
                        r'ASM_FUNC\(".*",(?: static)?\W*\w*\W*(\w*).*\)', data
                    ):
                        result.append(
                            (
                                os.path.relpath(os.path.join(root, file), src_folder),
                                match,
                            )
                        )
    return result


def find_inc_file(name: str) -> Optional[str]:
    filename = name + ".inc"
    search_path = os.path.join(current_app.config['TMC_REPO'], "asm", "non_matching")
    for root, dirs, files in os.walk(search_path):
        if filename in files:
            return os.path.join(root, filename)
    return None


def find_source_file(name: str, symbols: SymbolList) -> Optional[str]:
    # # Get the source file from tmc.map
    # with open(os.path.join(current_app.config['TMC_REPO'], "tmc.map"), "r") as f:
    #     current_file = None
    #     for line in f:
    #         if line.startswith(" .text"):
    #             current_file = line.split()[3]
    #         elif line.strip().endswith(" " + name):
    #             return current_file[0:-2] + ".c"
    #     return None
    symbol = symbols.find_symbol_by_name(name)
    if symbol is None:
        return None
    else:
        if symbol.file.endswith('.o'):
            return symbol.file[0:-2] + '.c'
        else:
            return symbol.file


def read_file_split_headers(src_file: str) -> Tuple[List[str], List[str]]:
    with open(src_file, "r") as f:
        data = []
        headers = []

        in_headers = True
        # match headers
        for line in f:
            if in_headers:
                if (
                    "{" in line
                    and not "struct" in line
                    and not "union" in line
                    and not "enum" in line
                ):
                    in_headers = False
                    data.append(line)
                elif "NONMATCH" in line or "ASM_FUNC" in line:
                    in_headers = False
                    data.append(line)
                else:
                    headers.append(line)
            else:
                data.append(line)
    return (headers, data)


def extract_nonmatching_section(
    inc_path: str, src_file: str, include_function: bool
) -> Tuple[Optional[str], str]:
    (headers, data) = read_file_split_headers(src_file)

    # match nonmatching section
    match = re.search(
        r"NONMATCH\(\"" + inc_path + r"\", ?(.*?)\) ?{(.*?)END_NONMATCH",
        "".join(data),
        re.MULTILINE | re.DOTALL,
    )
    if match:
        return (
            "".join(headers)
            + "// end of existing headers\n\n"
            + ((match.group(1) + " {" + match.group(2)) if include_function else ""),
            match.group(1),
        )

    match = re.search(
        r"ASM_FUNC\(\"" + inc_path + r"\", ?(.*?)\)",
        "".join(data),
        re.MULTILINE | re.DOTALL,
    )
    if match:
        return (
            "".join(headers)
            + "// end of existing headers\n\n"
            + ((match.group(1) + ") {\n\n}") if include_function else ""),
            match.group(1) + ")",
        )
    return (None, None)


def prepare_asm(inc_file: str, name: str) -> str:
    lines = []
    with open(inc_file, "r") as f:
        for line in f:
            l = line.strip()
            if l == "" and len(lines) == 0:  # ignore empty lines at the beginning
                continue
            if l != ".text" and l != ".syntax unified" and l != ".syntax divided":
                lines.append(line)
    return "thumb_func_start " + name + "\n" + name + ":\n" + ("".join(lines))


def get_code(name: str, include_function: bool, symbols: SymbolList) -> Tuple[bool, str, str, str]:
    # Find the .inc file for the non matching function
    inc_file = find_inc_file(name)
    if inc_file is None:
        return (True, f"No {name}.inc found in asm/non_matching folder.", "", "")

    src_file = find_source_file(name, symbols)
    if src_file is None:
        return (True, f"Source file for {name} not found in tmc.map.", "", "")
    src_file = os.path.join(current_app.config['TMC_REPO'], src_file)

    if not os.path.isfile(src_file):
        return (True, f"{src_file} is not a file.", "", "")

    inc_path = inc_file.replace("\\", "/")
    inc_path = inc_path.replace(current_app.config['TMC_REPO'] + "/", "")
    (src, signature) = extract_nonmatching_section(inc_path, src_file, include_function)
    if src is None:
        return (
            True,
            f"No NONMATCH or ASM_FUNC section found for {inc_path} in {src_file}.",
            "",
            "",
        )

    asm = prepare_asm(inc_file, name)

    return (False, asm, src, signature)


def calculate_score(a: str, b: str) -> int:
    if False:
        with open("a.txt", "w") as file:
            file.write(a)
        with open("b.txt", "w") as file:
            file.write(b)
    plus = 0
    minus = 0
    for line in difflib.unified_diff(a.split("\n"), b.split("\n")):
        plus += 1 if line.startswith("+") else 0
        minus += 1 if line.startswith("-") else 0

    # -1 as there is a --- +++ at the beginning of the diff
    return max(0, max(minus, plus) - 1)


ignored_functions = [
    "sub_080A2FD0",  # DEMO_USA
    "sub_080A30AC",  # DEMO_USA
]


def get_symbols() -> SymbolList:
    symbols = load_symbols_from_elf()
    map_symbols = load_symbols_from_map(os.path.join(current_app.config['TMC_REPO'], "tmc.map"))

    # elf currently only reads the functions from c files from the DWARF information
    # read asm files and variables from the .map
    for symbol in map_symbols.symbols:
        pub_symbol = symbols.get_symbol_at(symbol.address)
        if pub_symbol.address != symbol.address:
            pub_symbol = None
        if pub_symbol is None:
            # So far unknown symbol
            symbols.symbols.add(symbol)
        else:
            # Symbol is known, maybe the size can be more precise
            if pub_symbol.length > symbol.length:
                pub_symbol.length = symbol.length
    return symbols

def update_nonmatching_functions():
    symbols = get_symbols()

    nonmatch = collect_non_matching_funcs()
    asm_funcs = collect_asm_funcs()

    # Merge both lists
    repo_functions = []
    for (file, func) in nonmatch:
        repo_functions.append((False, file, func))
    for (file, func) in asm_funcs:
        repo_functions.append((True, file, func))

    # Query all existing functions in the database
    functions = Function.query.filter_by(deleted=False).all()
    funcs = {}
    addrs = {}
    for func in functions:
        funcs[func.name] = func
        addrs[func.addr] = func.name

    for (is_asm_func, file, func) in repo_functions:
        if func in ignored_functions:
            continue

        (err, asm, src, signature) = get_code(func, True, symbols)
        if err:
            print(asm, file=sys.stderr)
            sys.exit(1)
            continue

        create_function = True
        modified = False

        symbol = symbols.find_symbol_by_name(func)
        if symbol is None:
            print(f"No symbol found for {func}, maybe static?")
            sys.exit(1)
            continue

        if symbol.address in addrs and addrs[symbol.address] != func:
            print(f'Renaming {addrs[symbol.address]} to {func}...')
            funcs[func] = funcs[addrs[symbol.address]]
            del funcs[addrs[symbol.address]]
            funcs[func].name = func
            modified = True

        # Is the function already in the file
        if func in funcs:
            # TODO check whether the NONMATCH code changed, then update
            # -> look at the latest submission from the repo user (or the only one if we update it?)

            if funcs[func].is_asm_func != is_asm_func:
                print(f'Change asm state for {func} to {is_asm_func}')
                funcs[func].is_asm_func = is_asm_func
                modified = True

            submission = (
                Submission.query.filter_by(function=funcs[func].id, owner=current_app.config['REPO_USER'])
                .order_by(desc(Submission.time_created))
                .limit(1)
                .first()
            )
            if submission is not None and submission.code == src:

                # TODO remove
                # Update function size
                funcs[func].size = symbol.length
                funcs[func].addr = symbol.address
                db.session.commit()
                # END TODO



                # print(f'{func} code did not change, ignoring')
                continue
            create_function = False
            print(f"{func} code did change")
            # Only update the submission

        # Calculate the size from the symbol
        addr = symbol.address
        size = symbol.length

        # Compile, so that we can calculate the score
        res = requests.post(
            current_app.config['CEXPLORE_URL'],
            headers={
                "accept": "application/json, text/javascript, */*; q=0.01",
                "content-type": "application/json",
            },
            json={
                "source": src,
                "compiler": "agbcc",
                "options": {
                    "userArguments": "-O2",  # TODO allow the user to specify this?
                    "compilerOptions": {"produceGccDump": {}, "produceCfg": False},
                    "filters": {
                        "labels": True,
                        "binary": False,
                        "commentOnly": True,
                        "demangle": True,
                        "directives": True,
                        "execute": False,
                        "intel": True,
                        "libraryCode": False,
                        "trim": False,
                    },
                    "tools": [],
                    "libraries": [
                        {
                            "id": "tmc",
                            "version": "master"
                        }
                    ],
                },
                "lang": "c",
                "allowStoreCodeDebug": True,
            },
        )
        # also save the
        compiled = res.text
        # print(res.json())
        compiled_asm = ""
        separator = ""
        for line in res.json()["asm"]:
            compiled_asm += separator + line["text"]
            separator = "\n"

        if not res.ok:
            print("Failed to compile")
            print(compiled)
            sys.exit(1)


        asm = extract_USA_asm(asm)

        function_id = 0
        if create_function:
            print(f"Creating {func}")
            # Run pycat.py on the asm code
            res = requests.post(current_app.config['PYCAT_URL'], asm)
            asm = res.text.rstrip()
            if asm.startswith('#'):
                # Remove Compiler Explorer comment
                asm = asm.split('\n', 1)[1]

            # TODO the calculated score here differs from the score computed by monaco diff. Maybe update it when the first person views it?
            score = calculate_score(asm, compiled_asm)

            # TODO move to FunctionRepository
            function = Function(
                name=func,
                file=file,
                addr=addr,
                size=size,
                asm=asm,
                best_score=score,
                is_asm_func=is_asm_func,
                has_code_try=not is_asm_func
            )
            db.session.add(function)
            db.session.commit()
            function_id = function.id
        else:
            function_id = funcs[func].id
            # Run pycat.py on the asm code
            res = requests.post(current_app.config['PYCAT_URL'], asm)
            asm = res.text.rstrip()
            if asm.startswith('#'):
                # Remove Compiler Explorer comment
                asm = asm.split('\n', 1)[1]
            funcs[func].asm = asm

            # TODO the calculated score here differs from the score computed by monaco diff. Maybe update it when the first person views it?
            score = calculate_score(asm, compiled_asm)

            # Change the best_score of the function if this one is better
            if score < funcs[func].best_score:
                funcs[func].best_score = score

            funcs[func].size = size
            db.session.commit()

        SubmissionRepository.create(
            function=function_id,
            owner=current_app.config['REPO_USER'],
            code=src,
            score=score,
            is_equivalent=False,
            parent=None,
            compiled=compiled,
            comments=''
        )

    # TODO Does anything need to be done for functions that switch from ASM_FUNC to NONMATCH? or the other way around?

    funcs_in_repo = list(map(lambda x: x[2], repo_functions))

    for func in funcs:
        if not func in funcs_in_repo:
            print(f"{func} is no longer NONMATCH, removing...")
            funcs[func].deleted = True
            db.session.commit()


def store_code(
    name: str, includes: str, header: str, src: str, matching: bool
) -> Tuple[bool, str]:


    symbols = get_symbols()

    # Find the .inc file for the non matching function
    inc_file = find_inc_file(name)
    if inc_file is None:
        return (True, f"No {name}.inc found in asm/non_matching folder.")

    src_file = find_source_file(name, symbols)
    if src_file is None:
        return (True, f"Source file for {name} not found in tmc.map.")
    src_file = os.path.join(current_app.config['TMC_REPO'], src_file)

    if not os.path.isfile(src_file):
        return (True, f"{src_file} is not a file.")

    inc_path = inc_file.replace(current_app.config['TMC_REPO'] + "/", "")

    (headers, data) = read_file_split_headers(src_file)

    # https://stackoverflow.com/a/23146126
    def find_last_containing(lst, sought_elt):
        for r_idx, elt in enumerate(reversed(lst)):
            if sought_elt in elt:
                return len(lst) - 1 - r_idx

    # Insert includes at the correct place
    if includes.strip() != "":
        last_include_index = find_last_containing(headers, "#include")
        headers.insert(last_include_index + 1, includes.strip() + "\n")

    # Append headers
    if header.strip() != "":
        headers.append(header.strip() + "\n\n")

    # Add NONMATCH macro to replacement string when not matching
    if not matching:
        src = (
            re.sub(r"(.*?)\s*{", r'NONMATCH("' + inc_path + r'", \1) {', src, 1)
            + "\nEND_NONMATCH"
        )

    match = re.search(
        r"NONMATCH\(\"" + re.escape(inc_path) + r"\", ?(.*?)\) ?{(.*?)END_NONMATCH",
        "".join(data),
        re.MULTILINE | re.DOTALL,
    )
    if match:
        data = re.sub(
            r"NONMATCH\(\"" + re.escape(inc_path) + r"\", ?(.*?)\) ?{(.*?)END_NONMATCH",
            src,
            "".join(data),
            flags=re.MULTILINE | re.DOTALL,
        )
    else:
        match = re.search(
            r"ASM_FUNC\(\"" + re.escape(inc_path) + r"\", ?(.*?)\);?$",
            "".join(data),
            re.MULTILINE | re.DOTALL,
        )
        if match:
            data = re.sub(
                r"ASM_FUNC\(\"" + re.escape(inc_path) + r"\", ?(.*?)\);?$",
                src,
                "".join(data),
                flags=re.MULTILINE | re.DOTALL,
            )
        else:
            return (
                True,
                f"No NONMATCH or ASM_FUNC section found for {inc_path} in {src_file}.",
            )

    with open(src_file, "w") as f:
        f.write("".join(headers))
        f.write(data)

    if matching:
        # Remove the .inc file as its no longer neede
        os.remove(inc_file)

    return (False, "")


def split_code(code: str) -> Tuple[str, str, str]:
    if "// end of existing headers" in code:
        code = code.split("// end of existing headers")[1].strip()

    includes = []
    headers = []
    data = []
    lines = code.split("\n")
    in_includes = True
    in_headers = True
    for line in lines:
        if in_headers:
            if (
                "{" in line
                and not "struct" in line
                and not "union" in line
                and not "enum" in line
            ):
                in_headers = False
                data.append(line)
            elif "NONMATCH" in line or "ASM_FUNC" in line:
                in_headers = False
                data.append(line)
            else:
                if in_includes:
                    if line.strip() == "" or "#include" in line:
                        includes.append(line)
                    else:
                        in_includes = False
                        headers.append(line)
                else:
                    headers.append(line)
        else:
            data.append(line)
    return (
        "\n".join(includes).strip(),
        "\n".join(headers).strip(),
        "\n".join(data).strip(),
    )



# Only extract the code for the USA version from the asm code
def extract_USA_asm(asm: str) -> str:
    script_lines = asm.split('\n')
    output_lines = []
    ifdef_stack = [True]

    for line in script_lines:
        stripped = line.strip()

        if '.ifdef' in stripped:
            if not ifdef_stack[-1]:
                ifdef_stack.append(False)
                #output_lines.append(line)
                continue
            # TODO check variant
            is_usa = stripped.split(' ')[1] == 'USA'
            ifdef_stack.append(is_usa)
            #output_lines.append(line)
            continue
        if '.ifndef' in stripped:
            if not ifdef_stack[-1]:
                ifdef_stack.append(False)
                output_lines.append(line)
                continue
            is_usa = stripped.split(' ')[1] == 'USA'
            ifdef_stack.append(not is_usa)
            #output_lines.append(line)
            continue
        if '.else' in stripped:
            if ifdef_stack[-2]:
                # If the outermost ifdef is not true, this else does not change the validiness of this ifdef
                ifdef_stack[-1] = not ifdef_stack[-1]
            #output_lines.append(line)
            continue
        if '.endif' in stripped:
            ifdef_stack.pop()
            #output_lines.append(line)
            continue

        if not ifdef_stack[-1]:
            # Not defined for this variant
            #output_lines.append(line)
            continue

        output_lines.append(line)
    return '\n'.join(output_lines)

def get_headers_code(function_name: str) -> str:
    # symbols = get_symbols()
    # Only use map symbols because faster
    symbols = load_symbols_from_map(os.path.join(current_app.config['TMC_REPO'], "tmc.map"))

    src_file = find_source_file(function_name, symbols)
    if src_file is None:
        raise Exception(f"Source file for {function_name} not found in tmc.map.")
    src_file = os.path.join(current_app.config['TMC_REPO'], src_file)

    if not os.path.isfile(src_file):
        raise Exception(f"{src_file} is not a file.")

    (headers, data) = read_file_split_headers(src_file)
    return "".join(headers) + "// end of existing headers\n\n// Type your C code here..."
