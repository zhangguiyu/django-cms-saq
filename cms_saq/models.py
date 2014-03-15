from django.db import models
from django.db.models import Max, Sum

from cms.models import CMSPlugin, Page, Placeholder
from cms.models.fields import PageField
from taggit.managers import TaggableManager

from cms.plugins.text.models import AbstractText

# kuiyu multi-lingual
from hvad.models import TranslatableModel, TranslatedFields
#from parler.models import TranslatableModel, TranslatedFields

from django.utils.translation import ugettext_lazy as _

class QuestionnaireText(AbstractText):
    """ Text plugin which, when rendered is translated
        using django translations.  Also provides
        means of making text dependent on SAQ answers.
    """
    depends_on_answer = models.ForeignKey(
        'cms_saq.Answer', null=True, blank=True, related_name='trigger_text')

class AnswerSet(TranslatableModel):
    slug = models.SlugField(_("Slug"))
    translations = TranslatedFields(
        title = models.CharField(_("Title"), null=True, max_length=255),
        help_text = models.TextField(_("Help Text"), blank=True, null=True),
    )
    class Meta:
        verbose_name = _("AnswerSet")
        verbose_name_plural = _("AnswerSets")
#        ordering = ('question', 'order', 'slug')
#        unique_together = (('question', 'slug'),)
    def __unicode__(self):
        return self.lazy_translation_getter('title', '%s: %s' % (self.slug, self.title))
#        return u"%s: %s" % (self.question.slug, self.title)



# todo: add img, scale options
class Answer(TranslatableModel):
    slug = models.SlugField(_("Slug"))
    score = models.IntegerField(_("Score"), default=0)
    order = models.IntegerField(_("Order"), default=0)
#    question = models.ForeignKey('cms_saq.Question', related_name="answers",)
    answerset = models.ForeignKey(AnswerSet, related_name="answers",)

    is_default = models.BooleanField(_("Is Default"), default=False)

    translations = TranslatedFields(
        title = models.CharField(_("Title"), null=True, max_length=255),
        help_text = models.TextField(_("Help Text"), blank=True, null=True),
        group = models.CharField(_("Group"), max_length=255, blank=True, null=True)
    )
    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ('answerset', 'order', 'slug')
        unique_together = (('answerset', 'slug'),)

    def __unicode__(self):
        return self.lazy_translation_getter('title', '%s: %s' % (self.answerset.slug, self.title))
#        return u"%s: %s" % (self.question.slug, self.title)

    def save(self, *args, **kwargs):
        # check that answerset is saved or exist in DB, if not, save it first
        if self.answerset.pk is None:
            self.answerset.save()
        # kuiyu: TranslatableStackedInline bug  needs to set explicitly
        self.answerset_id = self.answerset.id
        print "---------------------------self.answerset_id = %d" % self.answerset_id
        super(Answer, self).save(*args, **kwargs) # Call the "real" save() method.

class GroupedAnswer(Answer):
#    group = models.CharField(max_length=255)
    class Meta:
        ordering = ('translations__group', 'order', 'slug')
        proxy = True        # kuiyu: needed to bypass master accessor problem

# todo: add image, scale
class Question(TranslatableModel):
    QUESTION_TYPES = [
        ('S', 'Single-choice question'),
        ('M', 'Multi-choice question'),
        ('F', 'Free-text question'),
    ]

    slug = models.SlugField(
        help_text=_("A slug for identifying answers to this specific question. Use the same slug for different translations of the same question if you want to tally results across different languages of the same question"))
    translations = TranslatedFields(
        label = models.CharField(_("Label"), max_length=512, blank=True),
        help_text = models.TextField(_("Help Text"), blank=True, null=True)
    )
    question_type = models.CharField(max_length=1, choices=QUESTION_TYPES)
    tags = TaggableManager(blank=True)
    answerset = models.ForeignKey(AnswerSet, blank=True, null=True, related_name='answerset',
    help_text=_("Pick a common answerset for this Question. Leave blank for Free-text question."),
    )



    optional = models.BooleanField(
        default=False,
        blank=True,
        max_length=512,
        help_text=_("Only applies to free text questions."),
    )

    # todo: replace with AnswerSet.answers
    depends_on_answer = models.ForeignKey(
        Answer, null=True, blank=True, related_name='trigger_questions')

    # kuiyu 2014.03.04 When a question is published along with container page,
    # CMSPlugin creates a published copy of the question:
    # one draft, one published
    # The draft question have associated answers, but the published one 
    # does not, so we copy over the answers associated to the draft over
    # to the published question.
    # 
    # The original design of cms_saq Question = CMSplugin
    # which means there will be 2 copies of the question.
    #
    # In this new design, the Question plugin points to a question, 
    # and the question points to a set of answers, AnswerSet.
    # That way we don't need to have 2 versions (1 draft, 1 published)
    # of every question/answers
    '''
    def copy_answer_translations(self, newid, oldtrans):
        for t in oldtrans:
            t.pk = None
#            t.id = None
            t.master_id = newid
            t.save()


    def copy_relations(self, oldinstance):
        self.depends_on_answer = oldinstance.depends_on_answer
        for answer in oldinstance.answers.all():
            oldtrans = answer.translations.all()   # old answer's translations
            oldpk = answer.pk
            newid = answer.id               # initialize newid to answer.id
            try:
                # 1a) copy the groupedanswer
                ga = GroupedAnswer.objects.get(pk=oldpk)
                gp = ga.group 
                # to copy inherited objects, must set both pk *AND* id to None 
                ga.pk = None
                ga.id = None
                ga.question = self
                ga.save()
                newid = ga.id
            except:
                # 1b) copy the answer
                answer.pk = None
                answer.question = self  # set new answers to new question
                answer.save()
                newid = answer.id

            # copy over the translations
            self.copy_answer_translations(newid, oldtrans)
    '''

    def score(self, answers):
        if self.question_type == 'F':
            return 0
        elif self.question_type == 'S':
            return self.answerset.answers.get(slug=answers).score
        elif self.question_type == 'M':
            answers_list = answers.split(',')
            return sum([self.answerset.answers.get(slug=a).score for a in answers_list])

    @property
    def max_score(self):
        if not hasattr(self, '_max_score'):
            if self.question_type == "S":
                self._max_score = self.answers.aggregate(
                    Max('score'))['score__max']
            elif self.question_type == "M":
                self._max_score = self.answers.aggregate(
                    Sum('score'))['score__sum']
            else:
                self._max_score = None  # don't score free-text answers
        return self._max_score

    def percent_score_for_user(self, user):
        if self.max_score:
            try:
                score = Submission.objects.get(
                    question=self.slug,
                    user=user,
                ).score
            except Submission.DoesNotExist:
                return 0
            return 100.0 * score / self.max_score
        else:
            return None

    def __unicode__(self):
#        return self.slug
        return self.lazy_translation_getter('label', '%s: %s' % (self.slug, self.label))

class QA(CMSPlugin):
    question = models.ForeignKey(Question, null=False, blank=True, related_name="plugin")
    @staticmethod
    def all_in_tree(page):
        root = page.get_root()
        # Remember that there might be questions on the root page as well!
        tree = root.get_descendants() | Page.objects.filter(id=root.id)
        placeholders = Placeholder.objects.filter(page__in=tree)
        return QA.objects.filter(placeholder__in=placeholders)

    @staticmethod
    def all_in_page(page):
        placeholders = Placeholder.objects.filter(page=page)
        return QA.objects.filter(placeholder__in=placeholders)



class SubmissionSet(models.Model):
    """ A set of submissions stored and associated with a particular user to
        provide a mechanism through which a single user can provide repeated
        sets of answers to the same questionnaire.
    """
    slug = models.SlugField(blank=True)
    user = models.ForeignKey('auth.User', related_name='saq_submissions_sets')


class Submission(models.Model):
    # todo: add date
    question = models.SlugField()
    answer = models.TextField(blank=True)
    score = models.IntegerField()
    user = models.ForeignKey('auth.User', related_name='saq_submissions')

    submission_set = models.ForeignKey(
        SubmissionSet, related_name='submissions', null=True)

    class Meta:
        ordering = ('submission_set', 'user', 'question')
        unique_together = ('question', 'user', 'submission_set')

    def answer_list(self):
        return self.answer.split(",")

    def __unicode__(self):
        return u"%s answer to %s (%s)" % (
            self.user, self.question, self.submission_set.slug
            if self.submission_set else "default")


class FormNav(CMSPlugin):
    next_page = PageField(blank=True, null=True, related_name="formnav_nexts",
    help_text=_("Shown only if link is non-empty"))
    next_page_label = models.CharField(max_length=255, blank=True, null=True,
    help_text=_("Optional Label, defaults to 'Next'"))

    prev_page = PageField(blank=True, null=True, related_name="formnav_prevs",
    help_text=_("Shown only if link is non-empty"))
    prev_page_label = models.CharField(max_length=255, blank=True, null=True,
    help_text=_("Optional Label, defaults to 'Prev'"))

    end_page = PageField(blank=True, null=True, related_name="formnav_ends",
    help_text=_("Shown only if link is non-empty and end page condition question set below *and* subsequently answered by user."))
    end_page_label = models.CharField(max_length=255, blank=True, null=True,
    help_text=_("Optional Label, defaults to 'End/Analysis'. End link is shown only if the end page condition question is set and answer submitted"))

    end_page_condition_question = models.ForeignKey(
        Question, null=True, blank=True,
        help_text=_("If set, End link will be shown if this question is answered."))

    end_submission_set = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("On submit, create a submission set from all submissions with the submision set tag name.  All sets created will be unique, if the given set name already exists, a numeric suffix will be appended to the tag name.")
        )

    submission_set_tag = models.CharField(
        max_length=255, blank=True, null=True)

    # not needed correctly copied automatically by django-cms
#    def copy_relations(self, oldinstance):
#        self.end_page_condition_question = oldinstance.end_page_condition_question



class SectionedScoring(CMSPlugin):
    def scores_for_user(self, user):
        scores = [
            [s.label, s.score_for_user(user)] for s in self.sections.all()]
        overall = sum([s[1] for s in scores]) / max(1,len(scores))
        return [scores, overall]

    def copy_relations(self, oldinstance):
        self.sections = oldinstance.sections.all()


class ScoreSection(models.Model):
    group = models.ForeignKey(
        'cms_saq.SectionedScoring', related_name='sections')
    label = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    order = models.IntegerField()

    class Meta:
        ordering = ('order', 'label')

    def score_for_user(self, user):
        return aggregate_score_for_user_by_tags(user, [self.tag])


class ProgressBar(CMSPlugin):
    count_optional = models.BooleanField(default=False)

    def progress_for_user(self, user):
        subs = Submission.objects.filter(
            user=user.id).values_list('question', flat=True)
        qas = QA.all_in_tree(self.page)

        if not self.count_optional:
            qas = QA.filter(optional=False)

        answered = 0
        for qa in qas:
            if qa.question.slug in subs:
                answered = answered + 1
#        answered = qas.question.all().filter(slug__in=subs)
        return (answered, qas.count())


class BulkAnswer(CMSPlugin):
    """Answer all questions on the current page with a given value."""
    answer_value = models.CharField(max_length=255)
    label = models.CharField(
        max_length=255, help_text="e.g.: 'mark all as not applicable'",
    )


def aggregate_score_for_user_by_questions(user, questions):
    scores = []
    for question in questions:
        score = question.percent_score_for_user(user)
        if score is not None:
            scores.append(score)
    if len(scores):
        return sum(scores) / len(scores)
    else:
        return 0


def aggregate_score_for_user_by_tags(user, tags):
    questions = Question.objects.filter(tags__name__in=tags).distinct()
    scores = []
    for question in questions:
        score = question.percent_score_for_user(user)
        if score is not None:
            scores.append(score)
    if len(scores):
        return sum(scores) / len(scores)
    else:
        return 0
