from django.core.management.base import BaseCommand
from django.utils import simplejson
from cms_saq.models import Question

class Command(BaseCommand):
    help = "Dumps django-cms-saq question tags."

    def handle(self, *args, **kwargs):
        questions = Question.objects.all()
        ret = {}
        for question in questions:
            ret[question.slug] = [t.name for t in question.tags.all()]
        self.stdout.write(simplejson.dumps(ret, indent=2, sort_keys=True))
