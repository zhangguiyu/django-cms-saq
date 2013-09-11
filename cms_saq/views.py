import re

from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import never_cache
from django.utils import simplejson, datastructures
from django.conf import settings

from cms_saq.models import Question, Answer, Submission, SubmissionSet

ANSWER_RE = re.compile(r'^[\w-]+(,[\w-]+)*$')


@require_POST
def _submit(request):

    post_data = datastructures.MultiValueDict(request.POST)
    submission_set_slug = post_data.pop('end_submission_set', '')
    submission_set_tag = post_data.pop('submission_set_tag', '')

    for question_slug, answers in post_data.iteritems():

        # validate the question
        try:
            question = Question.objects.get(slug=question_slug)
        except Question.DoesNotExist:
            return HttpResponseBadRequest("Invalid question '%s'" % question_slug)
        # check answers is a list of slugs
        if question.question_type != 'F' and not ANSWER_RE.match(answers):
            return HttpResponseBadRequest("Invalid answers: %s" % answers)
        # validate and score the answer
        try:
            score = question.score(answers)
        except Answer.DoesNotExist:
            return HttpResponseBadRequest("Invalid answer '%s:%s'" % (question_slug, answers))

        # save!
        filter_attrs = {
            'user': request.user,
            'question': question_slug,
            'submission_set': None # Don't update submissions belonging to an existing set
        }

        attrs = {'answer': answers, 'score': score}

        rows = Submission.objects.filter(**filter_attrs).update(**attrs)

        if not rows:
            attrs.update(filter_attrs)
            Submission.objects.create(**attrs)


    # Create submission set if requested
    if submission_set_tag and submission_set_slug:
        submission_set_tag = submission_set_tag[0]
        submission_set_slug = submission_set_slug[0]

        if submission_set_tag and submission_set_slug:
            _create_submission_set(request, submission_set_tag, submission_set_slug)

    return HttpResponse("OK")



if getattr(settings, "SAQ_LAZYSIGNUP", False):
    from lazysignup.decorators import allow_lazy_user
    submit = allow_lazy_user(_submit)
else:
    submit = login_required(_submit)

def _create_submission_set(request, submission_set_tag, submission_set_slug):
    """ Creates a submission set from any submissions matching the given
        tag that are not part of an existing set.
    """
    # Find maximum slug name
    exists = True
    bump = 1
    try_slug = submission_set_slug + "1"
    while exists:
        try_slug = "%s%s" % (submission_set_slug, bump)
        bump = bump + 1
        exists = SubmissionSet.objects.filter(
            user=request.user,
            slug=try_slug
        )
    submission_set_slug = try_slug

    # Add all tagged submissions to this set (if not already in a set)
    set_questions = Question.objects.filter(tags__name=submission_set_tag).values_list('slug', flat=True)

    submissions = Submission.objects.filter(
        submission_set=None,
        question__in=set_questions,
        user=request.user
    )

    # Create a new set
    if submissions:
        submission_set = SubmissionSet.objects.create(
            slug=submission_set_slug,
            user=request.user
        )
        submissions.update(submission_set=submission_set)


@require_GET
@never_cache
@login_required
def scores(request):
    slugs = request.GET.getlist('q')
    if slugs == []:
        return HttpResponseBadRequest("No questions supplied")
    submissions = Submission.objects.filter(user=request.user, question__in=slugs)
    submissions = [[s.question, {'answer': s.answer, 'score': s.score}]
            for s in submissions]
    data = {
        "questions": slugs,
        "submissions": dict(submissions),
        "complete": len(submissions) == len(slugs)
    }
    return HttpResponse(simplejson.dumps(data), mimetype="application/json")

# TODO benchmarking

