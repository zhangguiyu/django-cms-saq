from emailusernames.forms import EmailUserCreationForm
from emailusernames.utils import _email_to_username

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

