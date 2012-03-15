from django.db import models
from django.db.models import Max, Sum

from cms.models import CMSPlugin
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

    def score(self, answers):
        if self.question_type == 'F':
            return 0
        elif self.question_type == 'S':
            return self.answers.get(slug=answers).score
        elif self.question_type == 'M':
            answers_list = answers.split(',')
            return sum([self.answers.get(slug=a).score for a in answers_list])

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
        questions = Question.objects.filter(tags__name__in=[self.tag])
        scores = []
        for question in questions:
            if question.question_type == "S":
                max_score = question.answers.aggregate(Max('score'))['score__max']
            elif question.question_type == "M":
                max_score = question.answers.aggregate(Sum('score'))['score__sum']
            else:
                continue # don't score free-text answers
            try:
                score = Submission.objects.get(question=question.slug, user=user).score
            except Submission.DoesNotExist:
                score = 0
            if max_score:
                scores.append(100.0 * score / max_score)
        if len(scores):
            return sum(scores) / len(scores)
        else:
            return 0
