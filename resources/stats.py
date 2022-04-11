from flask_restful import Resource

from repositories.function import FunctionRepository


class StatsResource(Resource):
    def get(self):

        functions = FunctionRepository.get_all_internal()

        total_functions = 0
        total_size = 0
        open_functions = 0
        open_size = 0
        open_score = 0
        asm_functions = 0
        asm_size = 0
        asm_score = 0
        nonmatch_functions = 0
        nonmatch_size = 0
        nonmatch_score = 0
        unsubmitted_size = 0

        for function in functions:
            total_functions += 1
            total_size += function.size

            if function.is_matched and not function.is_submitted:
                unsubmitted_size += function.size

            if function.deleted or function.is_matched or function.is_submitted:
                continue

            open_functions += 1
            open_size += function.size
            open_score += function.best_score

            if function.is_asm_func:
                asm_functions += 1
                asm_size += function.size
                asm_score += function.best_score
            else:
                nonmatch_functions += 1
                nonmatch_size += function.size
                nonmatch_score += function.best_score

        return {
            'total_functions': total_functions,
            'total_size': total_size,
            'open_functions': open_functions,
            'open_size': open_size,
            'open_score': open_score,
            'asm_functions': asm_functions,
            'asm_size': asm_size,
            'asm_score': asm_score,
            'nonmatch_functions': nonmatch_functions,
            'nonmatch_size': nonmatch_size,
            'nonmatch_score': nonmatch_score,
            'unsubmitted_size': unsubmitted_size
        }, 200