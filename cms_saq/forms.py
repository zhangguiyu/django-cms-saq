from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

'''
#  https://github.com/danfairs/django-lazysignup
from emailusernames.forms import EmailUserCreationForm
from emailusernames.utils import _email_to_username
'''

from hvad.forms import TranslatableModelForm

from cms_saq.models import Question, Answer, validate_qa

'''
class SAQSignupForm(EmailUserCreationForm):
    """LazySignup signup form."""
    def get_credentials(self):
        return {'email': self.cleaned_data['email'], 'password': self.cleaned_data['password1']}

    def save(self, commit=True):
        user = super(EmailUserCreationForm, self).save(commit=False)
        user.username = _email_to_username(self.cleaned_data['email'])
        if commit:
            user.save()
        return user
'''


class AnswerForm(TranslatableModelForm):
    class Meta:
        model = Answer

    def clean_name(self):
        print "------------------------title = %s" % title
        # do something that validates your data
        # return self.cleaned_data["name"]

class QuestionForm(TranslatableModelForm): 
    class Meta:
        model = Question        

    def clean_depends_on_question(self):
        dq = self.cleaned_data.get('depends_on_question')
        if dq is not None:
            if dq.slug == self.cleaned_data['slug']:
               raise ValidationError(_("Question cannot depend on itself: %s" % dq)) 
        return self.cleaned_data['depends_on_question']
 
    def clean_depends_on_answer(self):
        dq = self.cleaned_data.get('depends_on_question')
        da = self.cleaned_data.get('depends_on_answer')
        if dq is not None:
            validate_qa(dq, da)
        elif da is not None:
            # no question given, slug should be unique for the page/survey/tag
            # TODO: filter by survey/page/tag
            aset = da.answerset		  		
            # 2nd check answerset is only attached to 1 question for this page/survey/tag
            q = aset.questions.all()
            if len(q)>1:
                raise ValidationError(_("Selected dependent answer %s has multiple associated questions. You did not specify a dependent question, please do so." % a)) 
        return self.cleaned_data['depends_on_answer']


