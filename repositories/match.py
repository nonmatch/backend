from repositories.function import FunctionRepository
from repositories.submission import SubmissionRepository


class MatchRepository:
    @staticmethod
    def get_all():
        matches = []
        functions = FunctionRepository.get_all_matched()

        for function in functions:
            submissions = SubmissionRepository.get_matched_for_function(
                function.id)
            for submission in submissions:
                matches.append({
                    'name': function.name,
                    'function': function.id,
                    'owner': submission.owner,
                    'submission': submission.id,
                    'time_created': submission.time_created,
                    'size': function.size,
                    'file': function.file
                })

        return matches
