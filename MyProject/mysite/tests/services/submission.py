from dataclasses import dataclass
from typing import Dict, List

from django.db import transaction

from ..models import AnswerOption, Submission, SubmissionAnswer
from ..services.scoring import ScoreCalculator


@dataclass
class SubmissionValidationResult:
    chosen: Dict[int, str]
    errors: set[int]


class SubmissionService:
    def __init__(self, score_calculator=None):
        self.score_calculator = score_calculator or ScoreCalculator()

    def parse_answers(self, questions, post_data) -> SubmissionValidationResult:
        chosen: Dict[int, str] = {}
        errors: set[int] = set()

        for question in questions:
            key = f"q_{question.id}"
            option_id = post_data.get(key)

            if question.is_required and not option_id:
                errors.add(question.id)
                continue

            if option_id:
                chosen[question.id] = option_id

        return SubmissionValidationResult(chosen=chosen, errors=errors)

    @transaction.atomic
    def create_submission(self, test, session_key: str, questions, chosen_answers: Dict[int, str]):
        submission = Submission.objects.create(
            test=test,
            session_key=session_key,
            total_score=0,
        )

        options_map = {
            option.id: option
            for option in AnswerOption.objects.filter(
                id__in=chosen_answers.values()
            ).select_related("question")
        }

        selected_options: List[AnswerOption] = []
        answers_to_create: List[SubmissionAnswer] = []

        for question in questions:
            option_id = chosen_answers.get(question.id)
            if not option_id:
                continue

            option = options_map.get(int(option_id))
            if not option:
                continue

            if option.question_id != question.id:
                continue

            selected_options.append(option)
            answers_to_create.append(
                SubmissionAnswer(
                    submission=submission,
                    question=question,
                    option=option,
                )
            )

        total_score = self.score_calculator.calculate(selected_options)

        SubmissionAnswer.objects.bulk_create(answers_to_create)

        submission.total_score = total_score
        submission.save(update_fields=["total_score"])

        return submission