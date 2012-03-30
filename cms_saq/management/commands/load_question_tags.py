import sys
from django.core.management.base import BaseCommand
from django.utils import simplejson
from cms_saq.models import Question

class Command(BaseCommand):
    help = "Dumps django-cms-saq question tags."

    def handle(self, *args, **kwargs):
        questions = simplejson.loads(sys.stdin.read())
        for slug, tags in questions.iteritems():
            try:
                question = Question.objects.get(slug=slug)
                question.tags.clear()
                question.tags.add(*tags)
            except Question.DoesNotExist:
                self.stdout.write("Skipping non-existent question: %s\n" % slug)
