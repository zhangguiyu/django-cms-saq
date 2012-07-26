# Django CMS Self-Assessment Questionnaires

This is a Django app that provides some generic building blocks for creating
self-assessment questionnaires using Django CMS.

## Quick Start

(assuming you already have a working Django CMS project)

1. Install django-cms-saq and django-taggit using pip

    pip install django-cms-saq django-taggit

2. Add `cms_saq` and `taggit` to your `INSTALLED_APPS`

    INSTALLED_APPS = (
        ...
        'taggit',
        'cms_saq',
        ...
    )

3. Add `cms_saq.urls` to your urls.py

    urlpatterns = patterns('',
        ...
        url(r'^saq/', include('cms_saq.urls'),
        ...
    )

4. The django-cms-saq plugins should now be available to add to your CMS
   pages.

## Available Plugins

### Questions

The core of django-cms-saq is the question plugins.  Each question is
uniquely identified by its **slug**.  Answers to questions are be stored
with references to their **slug**s and the users that submitted them.

There is no formal grouping of questions in the models, so there's no concept
of a *questionnaire*.  Questions are merely plugins placed on pages.  Where
you need to aggregate answers to questions (eg. for average/total scores for
a series of questions grouped on a page, or in a section), you can use
**tags**.

#### Question Types

- **Single Choice Question**

  Displays a list of radio buttons, from which a user can select a single
  answer.

- **Multi Choice Question**

  Displays a list of checkboxes, from which a user can select *one or more*
  answers.

  Scores for multi-choice questions will be the sum of the scores for all the
  chosen answers.

- **Free Text Question**

  Displays a text input box.

  Free text questions are not scored.  They are simply for collecting
  information about the user (eg. name / address / company details).

- **Drop-down Question**

  Displays a select box.

- **Grouped Drop-down Question**

  Displays a select box with optgroups.

### Back / Next Buttons

This plugin contains the javascript code that submits answers to the
`cms_saq.views.submit` view.  This plugin **must** be included on each page
of questions.

### Sectioned Scoring

This is a simple analysis plugin.  It displays aggregate total scores for
questions grouped by tags.  Scores are displayed as percentages of the
maximum score available for each group.

## Adding your own analysis -- how to access user submissions

Each user submission is stored in a `cms_saq.models.Submission` object, which
references the user, the question and the answer(s), as well as containing a
score calculated at submission.  For some guidance on creating a plugin to
display your own analysis (and how to query submissions by question tags),
take a look at the source code for
`cms_saq.cms_plugins.SectionedScoringPlugin`.

## Integration with django-lazysignup

If you add `SAQ_LAZYSIGNUP=True` to your settings.py, the
`cms_saq.views.submit` view will use the `allow_lazy_user` decorator from
django-lazysignup.

See https://github.com/danfairs/django-lazysignup for more info on lazysignup.

