from typing import Optional
from models.pr import Pr

class PrRepository:
    @staticmethod
    def get(id: int) -> Optional[Pr]:
        return Pr.query.filter_by(id=id).first_or_404('Pull Request not found.')