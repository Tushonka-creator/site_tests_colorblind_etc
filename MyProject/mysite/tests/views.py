from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from .models import Test, Question, AnswerOption, Submission, SubmissionAnswer


def test_list(request):
    tests = Test.objects.filter(is_published=True).order_by("order", "id")
    return render(request, "tests/test_list.html", {"tests": tests})


def test_detail(request, slug):
    test = get_object_or_404(Test, slug=slug, is_published=True)
    questions = test.questions.prefetch_related("options").all()

    if request.method == "POST":
        # гарантируем session_key
        if not request.session.session_key:
            request.session.save()

        chosen = {}  # question_id -> option_id
        errors = []

        for q in questions:
            key = f"q_{q.id}"
            opt_id = request.POST.get(key)

            if q.is_required and not opt_id:
                errors.append(q.id)
                continue

            if opt_id:
                chosen[q.id] = opt_id

        if errors:
            return render(
                request,
                "tests/test_detail.html",
                {"test": test, "questions": questions, "errors": set(errors)},
            )

        with transaction.atomic():
            submission = Submission.objects.create(
                test=test,
                session_key=request.session.session_key or "",
                total_score=0,
            )

            total = 0
            # проверяем, что выбранные option действительно принадлежат нужному question
            options_map = {
                o.id: o for o in AnswerOption.objects.filter(id__in=chosen.values()).select_related("question")
            }

            answers_to_create = []
            for q in questions:
                opt_id = chosen.get(q.id)
                if not opt_id:
                    continue
                opt_id = int(opt_id)
                opt = options_map.get(opt_id)
                if not opt or opt.question_id != q.id:
                    continue  # защита от подмены POST

                total += opt.score
                answers_to_create.append(
                    SubmissionAnswer(submission=submission, question=q, option=opt)
                )

            SubmissionAnswer.objects.bulk_create(answers_to_create)
            submission.total_score = total
            submission.save(update_fields=["total_score"])

        return redirect("tests:result", slug=test.slug, submission_id=submission.id)

    return render(request, "tests/test_detail.html", {"test": test, "questions": questions, "errors": set()})


def test_result(request, slug, submission_id):
    test = get_object_or_404(Test, slug=slug, is_published=True)
    submission = get_object_or_404(Submission, id=submission_id, test=test)

    answers = (
        submission.answers
        .select_related("question", "option")
        .order_by("question__order", "question__id")
    )

    return render(
        request,
        "tests/test_result.html",
        {"test": test, "submission": submission, "answers": answers},
    )