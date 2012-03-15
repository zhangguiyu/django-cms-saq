import itertools, operator

from django.contrib import admin

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from cms_saq.models import Question, Answer, GroupedAnswer, Submission, \
        FormNav, SectionedScoring, ScoreSection

class AnswerAdmin(admin.StackedInline):
    model = Answer
    extra = 0
    verbose_name = "answer"
    prepopulated_fields = {"slug": ("title",)}

class NoHelpTextAnswerAdmin(AnswerAdmin):
    exclude = ('help_text',)

class NoHelpTextGroupedAnswerAdmin(NoHelpTextAnswerAdmin):
    model = GroupedAnswer

class QuestionPlugin(CMSPluginBase):
    model = Question
    module = "SAQ"
    inlines = [AnswerAdmin]
    exclude = ('question_type',)

    def render(self, context, instance, placeholder):
        user = context['request'].user
        extra = {
            'question': instance,
            'answers': instance.answers.all()
        }
        if user.is_authenticated():
            try:
                extra['submission'] = Submission.objects.get(user=user, question=instance.slug)
            except Submission.DoesNotExist:
                pass
        context.update(extra)
        return context

    def save_model(self, request, obj, form, change):
        obj.question_type = self.question_type
        super(QuestionPlugin, self).save_model(request, obj, form, change)

class SingleChoiceQuestionPlugin(QuestionPlugin):
    name = "Single Choice Question"
    render_template = "cms_saq/single_choice_question.html"
    question_type = "S"
    exclude = ('question_type', 'label', 'help_text')

class MultiChoiceQuestionPlugin(QuestionPlugin):
    name = "Multi Choice Question"
    render_template = "cms_saq/multi_choice_question.html"
    question_type = "M"
    exclude = ('question_type', 'label', 'help_text')

class DropDownQuestionPlugin(QuestionPlugin):
    name = "Drop-down Question"
    render_template = "cms_saq/drop_down_question.html"
    inlines = [NoHelpTextAnswerAdmin]
    question_type = "S"

class GroupedDropDownQuestionPlugin(QuestionPlugin):
    name = "Grouped Drop-down Question"
    render_template = "cms_saq/drop_down_question.html"
    inlines = [NoHelpTextGroupedAnswerAdmin]
    question_type = "S"

    def render(self, context, instance, placeholder):
        new_ctx = super(GroupedDropDownQuestionPlugin, self).render(context, instance, placeholder)
        answers = list(GroupedAnswer.objects.filter(question=instance))
        grouped_answers = itertools.groupby(answers, operator.attrgetter('group'))
        grouped_answers = [[key, list(group)] for key, group in grouped_answers]
        new_ctx.update({'grouped_answers': grouped_answers})
        return new_ctx

class FreeTextQuestionPlugin(QuestionPlugin):
    name = "Free Text Question"
    render_template = "cms_saq/free_text_question.html"
    inlines = []
    question_type = "F"

class FormNavPlugin(CMSPluginBase):
    model = FormNav
    name = "Back / Next Buttons"
    module = "SAQ"
    render_template = "cms_saq/form_nav.html"

    def render(self, context, instance, placeholder):
        context.update({'instance': instance})
        return context

class ScoreSectionAdmin(admin.TabularInline):
    model = ScoreSection
    extra = 0
    verbose_name = "section"

class SectionedScoringPlugin(CMSPluginBase):
    model = SectionedScoring
    name = "Sectioned Scoring"
    module = "SAQ"
    render_template = "cms_saq/sectioned_scoring.html"
    inlines = [ScoreSectionAdmin]

    def render(self, context, instance, placeholder):
        scores, overall = instance.scores_for_user(context['request'].user)
        context.update({
            'scores': scores,
            'overall': overall
        })
        return context

plugin_pool.register_plugin(SingleChoiceQuestionPlugin)
plugin_pool.register_plugin(MultiChoiceQuestionPlugin)
plugin_pool.register_plugin(DropDownQuestionPlugin)
plugin_pool.register_plugin(GroupedDropDownQuestionPlugin)
plugin_pool.register_plugin(FreeTextQuestionPlugin)
plugin_pool.register_plugin(FormNavPlugin)
plugin_pool.register_plugin(SectionedScoringPlugin)

