from ..models import ResultRange


class ResultRangeService:
    def get_result_for_score(self, test, score):
        return (
            ResultRange.objects
            .filter(test=test, min_score__lte=score, max_score__gte=score)
            .order_by("min_score")
            .first()
        )