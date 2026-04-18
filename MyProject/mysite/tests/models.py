from django.db import models


class Test(models.Model):
    """
    Тест: "Дальтонизм", "Аутизм", и т.д.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    # порядок вывода на главной/в списках
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey("Test", on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("test", "order")

    def __str__(self):
        return f"{self.test.title} — Q{self.order + 1}"


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    score = models.IntegerField(default=0)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("question", "order")

    def __str__(self):
        return f"Option({self.question.id}): {self.text[:40]}"


class Submission(models.Model):
    """
    Прохождение теста (попытка). Пока без авторизации — просто session_key.
    Потом можно добавить FK на User.
    """
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="submissions")
    session_key = models.CharField(max_length=40, blank=True, db_index=True)  # request.session.session_key
    total_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission #{self.id} — {self.test.title}"


class SubmissionAnswer(models.Model):
    """
    Ответы пользователя: какой вариант выбрал для каждого вопроса.
    unique_together гарантирует 1 ответ на 1 вопрос в рамках попытки.
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.ForeignKey(AnswerOption, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["submission", "question"], name="uniq_submission_question")
        ]

    def __str__(self):
        return f"SubmissionAnswer(sub={self.submission_id}, q={self.question_id})"


class ResultRange(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="result_ranges")
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "min_score", "id"]

    def __str__(self):
        return f"{self.test.title}: {self.min_score}-{self.max_score} — {self.title}"


