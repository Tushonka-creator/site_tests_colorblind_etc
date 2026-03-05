from django.contrib import admin
from .models import Test, Question, AnswerOption, Submission, SubmissionAnswer, ResultRange



class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2
    fields = ("order", "text", "score")
    ordering = ("order",)


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ("order", "text", "is_required")
    ordering = ("order",)
    show_change_link = True


class ResultRangeInline(admin.TabularInline):
    model = ResultRange
    extra = 1
    fields = ("order", "min_score", "max_score", "title")
    ordering = ("order", "min_score")


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "order", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("order", "id")
    inlines = (QuestionInline, ResultRangeInline)



@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("test", "order", "short_text", "is_required")
    list_filter = ("test", "is_required")
    search_fields = ("text",)
    ordering = ("test", "order", "id")
    inlines = (AnswerOptionInline,)

    def short_text(self, obj):
        t = obj.text.strip().replace("\n", " ")
        return (t[:80] + "…") if len(t) > 80 else t
    short_text.short_description = "text"


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "text", "score")
    list_filter = ("question__test",)
    search_fields = ("text",)
    ordering = ("question", "order", "id")


class SubmissionAnswerInline(admin.TabularInline):
    model = SubmissionAnswer
    extra = 0
    fields = ("question", "option")
    autocomplete_fields = ("question", "option")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "test", "total_score", "session_key", "created_at")
    list_filter = ("test", "created_at")
    date_hierarchy = "created_at"
    inlines = (SubmissionAnswerInline,)
    readonly_fields = ("created_at",)
    search_fields = ("id", "session_key", "test__title")


@admin.register(SubmissionAnswer)
class SubmissionAnswerAdmin(admin.ModelAdmin):
    list_display = ("submission", "question", "option")
    list_filter = ("submission__test",)
    autocomplete_fields = ("submission", "question", "option")


