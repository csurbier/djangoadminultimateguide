from django import template
from backoffice.models import *

register = template.Library()

@register.simple_tag
def number_of_authors(request):
    qs = Author.objects.all()
    return qs.count()


@register.simple_tag
def number_of_questions(request):
    qs = Question.objects.all()
    return qs.count()


@register.simple_tag
def number_of_choices(request):
    qs = Choice.objects.all()
    return qs.count()