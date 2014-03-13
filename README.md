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

## Available Models

### Question

The core of django-cms-saq used to be the question plugins.  Each question is
uniquely (note) identified by its **slug**.  Answers to questions are be stored
with references to their **slug**s and the users that submitted them.

(note) However, from Django 1.5, whenever a page is published, django-cms creates a published copy of the page, along with a copy of all plugins on that published page. Which means there will be 2 copies, 1 draft 1 published of each CMSplugin (e.g. questions, answers). That is, there will be 2 identical questions (1 draft 1 published) with the same slug for every question you created. Likewise, there will be 2 answers. Keep note of this when you select dependent and end option questions/answers in the various plugins. Always choose the later copy (with higher id, denoting they are the published version).

In this new design, Question is simply a translatable model, which is linked to
an existing AnswerSet.

You can define any number of translations for the question, and they will be asssociated to the same AnswerSet (also defineable in various languages).

There is no formal grouping of questions in the models, so there's no concept
of a *questionnaire*.  Questions are merely pointed to from plugins placed on
pages.  Where you need to aggregate answers to questions
(eg. for average/total scores for a series of questions grouped on a page,
or in a section), you can use **tags**.

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

  Displays a select box with optgroups, for visually grouping answers only.

### AnswerSet

An AnswerSet is a translateble model containing multiple Answers.

The same AnswerSet can be reused in multiple Questions,
to save the time in entering the same responses, e.g.,
the answerset, (poor, satisfactory, good, great),
along with its translations in various languages,
can now be reused over multiple questions.

## Available Plugins

### QAPlugin

In the new design, QAPlugin points to a Question. This way, when the QAPlugin
is published along with the container CMS page, only the QAPlugin is replicated.
There will be 2 copies of each QAPlugin instance, one draft, one published, and
both will be pointing to the same Question, which exists in the system only
once.


In the orignal design, each QuestionPlugin instance existed, along with its
associated answers, and translations, as 2 copiesa - draft, published.
That led to a lot of unnecessary cleanup and copy_relations code,
not to mention problems with referencing a dependent question or answer; e.g.,
on a page that depends on another question or answer, the dependency will be
broken once the question/answer's parent/container page is published.


### Back / Next Buttons

This plugin contains the javascript code that submits answers to the
`cms_saq.views.submit` view.  This plugin **must** be included on each page
of questions.

Button labels are optional. If not entered, default values will be shown, e.g., Previous, Next, End / Analysis.
End button will display if and only if
    - end page dependent question is defined
    - end question is answerض
Buttons are shown only if links are selected. For example, if the next link is NLL, the next button will not be shown.

Submit Tags


### Sectioned Scoring

This is a simple analysis plugin.  It displays aggregate total scores for
questions grouped by tags.  Scores are displayed as percentages of the
maximum score available for each group.

### Progress Bar

This simply adds a progress bar to any page that is part of the questionnaire.
It displays the number of answered questions out of the total available in the
entire tree. You can also filter out optional questions to show progress on
required questions only (though this won't count answers to optional questions,
so might be misleading).

### Bulk Answer

Useful for 'skip this section' type functionality, this allows the insertion of
a button into the page that marks all **single-choice** questions with a given
answer. It only works on questions where the given answer value is one of the
options and disregards any other user input.

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

