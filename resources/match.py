from flask_restful import Resource
from repositories.match import MatchRepository

from schemas.match import MatchSchema

matches_schema = MatchSchema(many=True)

class MatchResource(Resource):
    def get(self):
        '''Returns all matching submissions'''
        return matches_schema.dump(MatchRepository.get_all())