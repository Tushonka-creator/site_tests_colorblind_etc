from django.template.context_processors import request

from .selectors.tests import (
    get_published_tests,
    get_published_test_by_slug,
    get_test_questions_with_options,
)
from .services.result_range import ResultRangeService
from .services.submission import SubmissionService
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from .forms import TestSubmissionForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Test, Submission, SubmissionAnswer, AnswerOption
from .services.scoring import ScoreCalculator


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


@login_required
def take_test(request, slug):
    test = get_object_or_404(Test, slug=slug, is_published=True)
    questions = test.questions.prefetch_related("answeroption_set").all()

    if request.method == "POST":
        form = TestSubmissionForm(request.POST, questions=questions)

        if form.is_valid():
            with transaction.atomic():
                submission = Submission.objects.create(
                    user=request.user,
                    test=test,
                )

                selected_options = []

                for question in questions:
                    option_id = form.cleaned_data.get(f"question_{question.id}")
                    if not option_id:
                        continue

                    option = AnswerOption.objects.get(
                        id=option_id,
                        question=question
                    )

                    SubmissionAnswer.objects.create(
                        submission=submission,
                        question=question,
                        selected_option=option,
                    )
                    selected_options.append(option)

                submission.total_score = calculate_submission_score(selected_options)
                submission.save(update_fields=["total_score"])

            return redirect("submission_detail", pk=submission.pk)
    else:
        form = TestSubmissionForm(questions=questions)

    return render(request, "tests/take_test.html", {
        "test": test,
        "form": form,
    })


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission,
        pk=pk,
        user=request.user,
    )
    return render(request, "tests/submission_detail.html", {"submission": submission})

@login_required
def my_results(request):
    submissions = Submission.objects.filter(user=request.user).select_related("test")
    return render(request, "tests/my_results.html", {"submissions": submissions})


def test_list(request):
    tests = get_published_tests()
    return render(request, "tests/test_list.html", {"tests": tests})


def test_detail(request, slug):
    test = get_published_test_by_slug(slug)
    questions = get_test_questions_with_options(test)

    if request.method == "POST":
        if not request.session.session_key:
            request.session.save()

        submission_service = SubmissionService()
        validation_result = submission_service.parse_answers(questions, request.POST)

        if validation_result.errors:
            return render(
                request,
                "tests/test_detail.html",
                {
                    "test": test,
                    "questions": questions,
                    "errors": validation_result.errors,
                },
            )

        submission = submission_service.create_submission(
            test=test,
            session_key=request.session.session_key or "",
            questions=questions,
            chosen_answers=validation_result.chosen,
        )

        return redirect("tests:result", slug=test.slug, submission_id=submission.id)

    return render(
        request,
        "tests/test_detail.html",
        {
            "test": test,
            "questions": questions,
            "errors": set(),
        },
    )


def test_result(request, slug, submission_id):
    test = get_published_test_by_slug(slug)
    submission = get_object_or_404(Submission, id=submission_id, test=test)

    answers = (
        submission.answers
        .select_related("question", "option")
        .order_by("question__order", "question__id")
    )

    result_service = ResultRangeService()
    result_range = result_service.get_result_for_score(test, submission.total_score)

    return render(
        request,
        "tests/test_result.html",
        {
            "test": test,
            "submission": submission,
            "answers": answers,
            "result_range": result_range,
        },
    )