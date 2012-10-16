from django.db import models
from django.db.models import Max, Sum

from cms.models import CMSPlugin, Page, Placeholder
from cms.models.fields import PageField
from taggit.managers import TaggableManager

class Answer(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    help_text = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    question = models.ForeignKey('cms_saq.Question', related_name="answers")

    class Meta:
        ordering = ('order', 'slug')
        unique_together = ('question', 'slug')

    def __unicode__(self):
        return u"%s" % self.title

class GroupedAnswer(Answer):
    group = models.CharField(max_length=255)

    class Meta:
        ordering = ('group', 'order', 'slug')

class Question(CMSPlugin):
    QUESTION_TYPES = [
        ('S', 'Single-choice question'),
        ('M', 'Multi-choice question'),
        ('F', 'Free-text question'),
    ]

    slug = models.SlugField(unique=True,
            help_text="A unique slug for identifying answers to this specific question")
    tags = TaggableManager(blank=True)
    label = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=255, blank=True)
    question_type = models.CharField(max_length=1, choices=QUESTION_TYPES)
    optional = models.BooleanField(
        default=False,
        help_text="Only applies to free text questions",
    )

    @staticmethod
    def all_in_tree(page):
        root = page.get_root()
        # Remember that there might be questions on the root page as well!
        tree = root.get_descendants() | Page.objects.filter(id=root.id)
        placeholders = Placeholder.objects.filter(page__in=tree)
        return Question.objects.filter(placeholder__in=placeholders)

    @staticmethod
    def all_in_page(page):
        placeholders = Placeholder.objects.filter(page=page)
        return Question.objects.filter(placeholder__in=placeholders)

    def score(self, answers):
        if self.question_type == 'F':
            return 0
        elif self.question_type == 'S':
            return self.answers.get(slug=answers).score
        elif self.question_type == 'M':
            answers_list = answers.split(',')
            return sum([self.answers.get(slug=a).score for a in answers_list])

    @property
    def max_score(self):
        if not hasattr(self, '_max_score'):
            if self.question_type == "S":
                self._max_score = self.answers.aggregate(Max('score'))['score__max']
            elif self.question_type == "M":
                self._max_score = self.answers.aggregate(Sum('score'))['score__sum']
            else:
                self._max_score = None # don't score free-text answers
        return self._max_score

    def percent_score_for_user(self, user):
        if self.max_score:
            try:
                score = Submission.objects.get(question=self.slug, user=user).score
            except Submission.DoesNotExist:
                return 0
            return 100.0 * score / self.max_score
        else:
            return None

    def __unicode__(self):
        return self.slug

class Submission(models.Model):
    question = models.SlugField()
    answer = models.TextField(blank=True)
    score = models.IntegerField()
    user = models.ForeignKey('auth.User', related_name='saq_submissions')

    class Meta:
        ordering = ('user', 'question')
        unique_together = ('question', 'user')

    def answer_list(self):
        return self.answer.split(",")

    def __unicode__(self):
        return u"%s answer to %s" % (self.user, self.question)

class FormNav(CMSPlugin):
    next_page = PageField(blank=True, null=True, related_name="formnav_nexts")
    next_page_label = models.CharField(max_length=255, blank=True, null=True)
    prev_page = PageField(blank=True, null=True, related_name="formnav_prevs")
    prev_page_label = models.CharField(max_length=255, blank=True, null=True)
    end_page = PageField(blank=True, null=True, related_name="formnav_ends")
    end_page_label = models.CharField(max_length=255, blank=True, null=True)
    end_page_condition_question = models.ForeignKey(Question, null=True, blank=True)


class SectionedScoring(CMSPlugin):
    def scores_for_user(self, user):
        scores = [[s.label, s.score_for_user(user)] for s in self.sections.all()]
        overall = sum([s[1] for s in scores]) / len(scores)
        return [scores, overall]

class ScoreSection(models.Model):
    group = models.ForeignKey('cms_saq.SectionedScoring', related_name='sections')
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
        subs = Submission.objects.filter(user=user).values_list('question', flat=True)
        questions = Question.all_in_tree(self.page)

        if not self.count_optional:
            questions = questions.filter(optional=False)

        answered = questions.filter(slug__in=subs)

        return (answered.count(), questions.count())


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

