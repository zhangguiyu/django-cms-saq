// Client-side SAQ question validation and submission, powered by
// Backbone.js.

$(function () {
    // namespace!
    var SAQ = {};

    // so we can fire global SAQ events! awesome!
    _.extend(SAQ, Backbone.Events);

    SAQ.Question = Backbone.Model.extend({
        defaults: {
            value: null
        },
        postValidate: function (attrs) {
            var value = attrs['value'];
            var optional = attrs['optional'] || false;
            var disabled = attrs['disabled'] || false;
            if (!optional && (value === undefined || value === null || value === "") && !disabled) {
                return "Please submit an answer to this question.";
            }
        }
    });

    SAQ.QuestionView = Backbone.View.extend({
        events: {
            'change': '_changeValue',
            'saq-disable': '_disable',
            'saq-enable': '_enable'
        },
        defaults: {
            value: null
        },
        initialize: function () {
            var self = this;
            this.model.on('error', function (model, error) {
                self.$('.saq-question-error').text(error).show();
            });
            this.model.on('postvalidate', function () {
                self.$('.saq-question-error').hide();
            });
            SAQ.on('submit:start', function () {
                self.$('input, select').attr('disabled','disabled');
            });
            SAQ.on('submit:end', function () {
                self.$('input, select').removeAttr('disabled');
            });
            SAQ.on('input:changed', function() {
                self.changeValue();
            });
            this._changeValue();
        },
        _disable: function(){
            this.model.set('disabled', true);
        },
        _enable: function(){
            this.model.set('disabled', false);
        },
        _changeValue: function (ev) {

            // Defer to overwritten changeValue
            this.changeValue(ev);

            // On any answer change, check our dependent questions
            $.each($('div[data-dependency]'), function(idx, qs){
                dependency = $(qs).attr('data-dependency');

                if(!$('input:[id$=' + dependency + ']').length){
                    $(qs).find('.saq-question').trigger('saq-disable');
                    return;
                }

                input = $('input:checked[id$=' + dependency + ']');
                if(!input.length){
                    if($(qs).is(':visible')){
                        $(qs).slideUp();
                        $(qs).find('.saq-question').trigger('saq-disable');
                    }
                    else{
                        $(qs).hide();
                        $(qs).find('.saq-question').trigger('saq-disable');
                    }
                }
                else{
                    $(qs).slideDown();
                    $(qs).find('.saq-question').trigger('saq-enable');
                }
            });
        },
        changeValue: function () {
            // override in subclasses
        }
    });

    SAQ.SingleChoiceQuestionView = SAQ.QuestionView.extend({
        changeValue: function () {
            this.model.set('value', this.$('input:checked').val());
        }
    });

    SAQ.MultiChoiceQuestionView = SAQ.QuestionView.extend({
        changeValue: function () {
            var vals = $.map(this.$('input:checked'), function (el) {
                return $(el).val();
            }).join(",");
            this.model.set('value', vals);
        }
    });

    SAQ.DropDownQuestionView = SAQ.QuestionView.extend({
        changeValue: function () {
            this.model.set('value', this.$('select').val());
        }
    });

    SAQ.FreeTextQuestionView = SAQ.QuestionView.extend({
        changeValue: function () {
            this.model.set('value', this.$('input').val());
        }
    });

    SAQ.QuestionCollection = Backbone.Collection.extend({
        model: SAQ.Question,
        validate: function () {
            var passed = true;
            this.forEach(function (question) {
                var msg = question.postValidate(question.attributes);
                if (msg) {
                    question.trigger('error', question, msg);
                    passed = false;
                }
                else {
                    question.trigger('postvalidate');
                }
            });
            return passed;
        },
        asMap: function () {
            return SAQ.questions.reduce(function (data, model) {
                value = model.get('value');
                if(!value)
                    return data;
                data[model.get('slug')] = value
                return data;
            }, {});
        }
    });

    SAQ.questions = new SAQ.QuestionCollection();

    SAQ.FormView = Backbone.View.extend({
        events: {
            'click .saq-next-button': 'submitForms',
            'click .saq-end-button': 'submitFormsAndEnd'
        },
        initialize: function () {
            this.submitting = false;
        },
        submitFormsAndEnd: function(e) {
            return this.submitForms(e, true);
        },
        submitForms: function (e, andEnd) {
            var self = this;
            if (!this.submitting && SAQ.questions.validate()) {
                this.submitting = true;
                this.$('.saq-ticker').css('visibility', 'visible');
                SAQ.trigger('submit:start');

                data = SAQ.questions.asMap();
                end_data = this.$('form.saq-end-button-data').serializeArray();
                $.each(end_data, function(idx, item){
                    data[item['name']] = item['value'];
                });

                $.ajax({
                    url: this.options.submitUrl,
                    data: data,
                    type: 'POST',
                    error: function () { self.onSubmitError(); },
                    success: function () {
                        if (andEnd) {
                            self.onSubmitSuccessEnd();
                        } else {
                            self.onSubmitSuccess();
                        }
                    },
                    complete: function () { self.onSubmitComplete(); }
                });
            }
            else {
                //console.log("validation failed?");
            }
            return false;
        },
        onSubmitError: function () {
            alert("There was a problem submitting your answers. Please try again later.");
            // TODO we can do better than an alert()
        },
        onSubmitSuccessEnd: function () {
            window.location = this.options.endUrl;
        },
        onSubmitSuccess: function () {
            window.location = this.options.nextUrl;
        },
        onSubmitComplete: function () {
            SAQ.trigger('submit:end');
            this.$('.saq-ticker').css('visibility', 'hidden');
            this.submitting = false;
        }
    });

    SAQ.BulkAnswer = Backbone.View.extend({
        events: {
            'click .saq-bulk-answer': 'markAnswers'
        },
        markAnswers: function (e) {
            // For every single-choice question with the given answer available
            // as an answer, mark the answer appropriately.
            $('.saq-question-single input[value=' + this.options.answerValue + ']').each(function(i, elt) {
                $(elt).click();
            });
            SAQ.trigger('input:changed');
            
            // If we have some prev/next buttons on the page, scroll there so
            // we can proceed post-update (we don't auto-advance).
            if ($('div.saq-form-nav')) {
                $('html, body').animate({
                    scrollTop: $("div.saq-form-nav").offset().top
                }, 2000);
            }
            return false;
        }
    });
    window.SAQ = SAQ;
});


// CSRF token protection for AJAX
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken",
                $('input[name="csrfmiddlewaretoken"]').val());
        }
   }
});

