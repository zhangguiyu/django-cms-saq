from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from cms.admin.placeholderadmin import PlaceholderAdmin

from cms_saq.models import *
from cms_saq.forms import QuestionForm, AnswerForm

from django.utils.translation import ugettext as _

from hvad.admin import TranslatableAdmin

#from parler.admin import TranslatableAdmin


class QuestionnaireTextAdmin(admin.ModelAdmin):
#    date_hierarchy = 'pub_date'
#    list_display = ('__unicode__', 'depends_on_answer', 'all_translations')    
    list_display = ('__unicode__', 'depends_on_answer')    

        
#class QuestionAdmin(TranslatableAdmin, PlaceholderAdmin):
class QuestionAdmin(TranslatableAdmin):
    form = QuestionForm
    list_display = ('slug', '__unicode__', 'question_type', 'get_tags', 'optional', 'depends_on_question', 'depends_on_answer')
    def get_tags(self, obj):
        return obj.tags.names()
        get_tags.short_description = _('Tags')

#class QAAdmin(admin.ModelAdmin, PlaceholderAdmin):
class QAAdmin(admin.ModelAdmin):
    class Meta:
        model = QA
#    list_display = ('question')

class AnswerAdmin(TranslatableAdmin):
    model = Answer
    extra = 0
#    prepopulated_fields = {'slug': ('title',)} # fails for hvad 0.3
    list_display = ('slug', '__unicode__', 'all_translations', 'score', 'order', 'is_default', 'answerset')

    form = AnswerForm

    # hack because you cannot use the following
    # prepopulated_fields = {'slug': ('title',)}
    # see https://github.com/KristianOellegaard/django-hvad/issues/10
    def __init__(self, *args, **kwargs):
        super(AnswerAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'slug': ('title',)}


    # translatable fields cannot be in list_display unless you define your own
    # as follows. See http://martinbrochhaus.com/hvad.html
#    def get_title(self, obj):
#        return obj.title
#        get_title.short_description = _('Title')
    def get_group(self, obj):
        return obj.group
        get_group.short_description = _('Group')
    def get_helptext(self, obj):
        return obj.help_text
        get_helptext.short_description = _('Help Text')

class AnswerSetAdmin(TranslatableAdmin):
    model = AnswerSet
    extra = 0
    list_display = ('slug', '__unicode__', 'all_translations', 'get_helptext')

    # hack because you cannot use the following
    # prepopulated_fields = {'slug': ('title',)}
    # see https://github.com/KristianOellegaard/django-hvad/issues/10
    def __init__(self, *args, **kwargs):
        super(AnswerSetAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'slug': ('title',)}
    def get_helptext(self, obj):
        return obj.help_text
        get_helptext.short_description = _('Help Text')


class GroupedAnswerAdmin(TranslatableAdmin):
    list_display = ('slug', 'title', 'help_text', 'score', 'order', 'is_default', 'answerset', 'group')

class SubmissionSetAdmin(admin.ModelAdmin):
    list_display = ('user', 'slug', 'get_submissions')
    def get_submissions(self, obj):
        qlist = []
        for s in obj.submissions.all():
            qlist.append(s.question) 
        return qlist

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'score', 'user', 'submission_set')

class FormNavAdmin(admin.ModelAdmin):
    list_display = ('version', 'prev_page', 'prev_page_label', 'next_page', 'next_page_label', 'end_page', 'end_page_label', 'end_page_condition_question', 'end_submission_set', 'submission_set_tag')
    def version(self, obj):
        return get_version(obj.page)

class SectionedScoringAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'scores_for_user')

class ScoreSectionAdmin(admin.ModelAdmin):
    list_display = ('group', 'label', 'tag', 'order')

class ProgressBarAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'count_optional')

class BulkAnswerAdmin(admin.ModelAdmin):
    list_display = ('label', 'answer_value')

admin.site.register(QuestionnaireText, QuestionnaireTextAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QA, QAAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(AnswerSet, AnswerSetAdmin)
admin.site.register(GroupedAnswer, GroupedAnswerAdmin)
admin.site.register(SubmissionSet, SubmissionSetAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(FormNav, FormNavAdmin)
admin.site.register(SectionedScoring, SectionedScoringAdmin)
admin.site.register(ScoreSection, ScoreSectionAdmin)
admin.site.register(ProgressBar, ProgressBarAdmin)
admin.site.register(BulkAnswer, BulkAnswerAdmin)

"""
class NewsAdmin(TranslatableAdmin, PlaceholderAdmin):

    date_hierarchy = 'pub_date'
    list_display = ('slug', '__unicode__', 'category','is_published', 'pub_date', 'all_translations', )
    list_filter = ('is_published', 'category', )
    search_fields = ['excerpt', ]
    #form = NewsForm
    
    actions = ['make_published', 'make_unpublished']
    
    save_as = True
    save_on_top = True

    def queryset(self, request):
        return News.objects.all()
       
    def make_published(self, request, queryset):
        rows_updated = queryset.update(is_published=True)
        self.message_user(request, ungettext('%(count)d newsitem was published', 
                                             '%(count)d newsitems where published', 
                                             rows_updated) % {'count': rows_updated})
    make_published.short_description = _('Publish selected news')

    def make_unpublished(self, request, queryset):
        rows_updated =queryset.update(is_published=False)
        self.message_user(request, ungettext('%(count)d newsitem was unpublished', 
                                             '%(count)d newsitems where unpublished', 
                                             rows_updated) % {'count': rows_updated})
    make_unpublished.short_description = _('Unpublish selected news')
"""

