from django.contrib import admin
from backoffice.models import *
from datetime import datetime,timedelta
from django.utils.html import format_html
admin.site.empty_value_display = '(No value)'
from django.utils.safestring import mark_safe
import csv
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.contrib.admin import AdminSite
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.db.models.functions import TruncDay
import json
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.urls import path
from django.template.response import TemplateResponse

# Custom admin site
class MyUltimateAdminSite(AdminSite):
    site_header = 'My Django Admin ultimate guide'
    site_title  = 'Django Admin ultimate Administration'
    index_title = 'Welcome to my backoffice'
    index_template = 'backoffice/templates/admin/my_index.html'
    #login_template = 'backoffice/templates/admin/custom_login.html'
    login_template = 'backoffice/templates/admin/login.html'

    def get_urls(self):
        urls = super(MyUltimateAdminSite, self).get_urls()
        custom_urls = [
            path('my_view/', self.admin_view(self.my_view),name="my_view"),
        ]
        return urls + custom_urls

    def my_view(self, request):
        # your business code
        context = dict(
            self.each_context(request),
            # Anything else you want in the context...
            welcome="Welcome to my new view",
        )
        return TemplateResponse(request, "admin/backoffice/custom_view.html", context)

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["my_variable"] = "MA VARIABLE"
        return super(MyUltimateAdminSite, self).index(request, extra_context)

"""
    def get_app_list(self,request):
        #Return a sorted list of our models  
        ordering = {"The Choices": 1, "The Questions": 2, "The Authors": 3, "The Authors clone": 4}
        app_dict = self._build_app_dict(request)
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        for app in app_list:
            app['models'].sort(key=lambda x: ordering[x['name']])
        return app_list
        """

site = MyUltimateAdminSite()

class MySecondAccessAdminSite(AdminSite):
    site_header = "Second Admin site"
    site_title = "Second Admin Portal"
    index_title = "Welcome to your second dashboard"

second_admin_site = MySecondAccessAdminSite()
second_admin_site.register(Author)

def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; \
        filename={}.csv'.format(opts.verbose_name)
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not field.many_to_many and not field.one_to_many]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])
    # Write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            if isinstance(value, datetime):
                value = value.strftime('%d/%m/%Y %H:%M')
            data_row.append(value)
        writer.writerow(data_row)
    return response

export_to_csv.short_description = 'Export to CSV'


class QuestionInline(admin.StackedInline):
    model = Question

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    #inlines = [QuestionInline,]
    empty_value_display = 'Unknown'
    fieldsets = [
        ("Author information", {'fields': ['name','createdDate','updatedDate']}),

    ]
    list_display = ('name','createdDate','updatedDate',)
    search_fields = ('name',)
    readonly_fields = ('createdDate','updatedDate',)

    def save_model(self, request, obj, form, change):
        print("Author saved by user %s" %request.user)
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        # Aggregate new authors per day
        chart_data = (
            Author.objects.annotate(date=TruncDay("updatedDate"))
                .values("date")
                .annotate(y=Count("id"))
                .order_by("-date")
        )

        # Serialize and attach the chart data to the template context
        as_json = json.dumps(list(chart_data), cls=DjangoJSONEncoder)
        print("Json %s"%as_json)
        extra_context = extra_context or {"chart_data": as_json}
        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        nbQuestion = Question.objects.filter(refAuthor=object_id).count()
        response_data = [
            nbQuestion
        ]
        extra_context = extra_context or {}
        # Serialize and attach the chart data to the template context
        as_json = json.dumps(response_data, cls=DjangoJSONEncoder)
        extra_context = extra_context or {"nbQuestion": as_json}
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    """
    def get_queryset(self, request):
        qs = super(AuthorAdmin, self).get_queryset(request)
        return qs.filter(name__startswith='j')
   """

@admin.register(AuthorClone)
class AuthorCloneAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Author information", {'fields': ['name','createdDate','updatedDate']}),

    ]
    list_display = ('name','createdDate','updatedDate',)
    search_fields = ('name',)


class QuestionPublishedListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = ('Published questions')
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'pub_date'
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('Published', ('Published questions')),
            ('Unpublished', ('Unpublished questions')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'Published':
            return queryset.filter(pub_date__lt=datetime.now())
        if self.value() == 'Unpublished':
            return queryset.filter(pub_date__gte=datetime.now())

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Question information", {
            'fields': ('question_text',)
        }),
        ("Date", {
            'fields': ('pub_date',)
        }),

        ('The author', {
            'classes': ('collapse',),
            'fields': ('refAuthor',),
        }),
    )

    list_display = ('question_text','my_question_text','goToChoices', 'refAuthor','has_been_published','pub_date','createdDate', 'updatedDate',)
    list_display_links = ('question_text','refAuthor',)
    list_per_page = 50

    def my_question_text(self, obj):
        return obj.question_text

    my_question_text.empty_value_display = '???'

    @mark_safe
    def goToChoices(self, obj):
        return format_html(
            '<a class="button" href="/admin/backoffice/choice/?question__id__exact=%s" target="blank">Choices</a>&nbsp;'% obj.pk)
    goToChoices.short_description = 'Choices'
    goToChoices.allow_tags = True

    def has_been_published(self,obj):
        present = datetime.now()
        return obj.pub_date.date() < present.date()

    has_been_published.short_description = 'Published?'
    has_been_published.boolean = True

    def colored_question_text(self,obj):
        return format_html(
            '<span style="color: #{};">{}</span>',
            "ff5733",
            obj.question_text,
        )

    def make_published(modeladmin, request, queryset):
        queryset.update(pub_date=datetime.now()- timedelta(days=1))
    make_published.short_description = "Mark selected questions as published"

    def make_published_custom(self, request, queryset):
        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:
            queryset.update(pub_date=datetime.now()- timedelta(days=1))

            # Redirect to our admin view after our update has
            # completed with a nice little info message saying
            # our models have been updated:
            self.message_user(request,
                              "Changed to published on {} questions".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())
        return render(request,
                      'admin/backoffice/custom_makepublished.html',
                      context={'questions':queryset})

    make_published_custom.short_description = "Custom make published"

    #list_editable = ('question_text',)
    list_filter = (QuestionPublishedListFilter,'refAuthor',)
    list_select_related = ('refAuthor',)
    autocomplete_fields = ['refAuthor']
    raw_id_fields = ("refAuthor",)
    search_fields = ('question_text',)
    show_full_result_count = False
    ordering = ('-pub_date',)
    date_hierarchy = 'pub_date'
    save_on_top = True
    actions = [make_published,export_to_csv,make_published_custom]

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('question', 'choice_text','votes','createdDate', 'updatedDate',)
    list_filter = ('question__refAuthor','question',)
    list_select_related = ('question','question__refAuthor',)
    search_fields = ('choice_text','question__refAuthor__name','question__question_text',)
    ordering = ('-createdDate',)

    def has_change_permission(self, request, obj=None):
        hasPermission = request.user.has_perm('backoffice.change_choice')
        return hasPermission

    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        try:
            user=request.user
            if request.user.is_superuser:
                return super(ChoiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
            else:
                if db_field.name == "question":
                    kwargs["queryset"] =  Question.objects.filter(refAuthor=140)
                    return super(ChoiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
                else:
                    return super(ChoiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        except Exception as e:
            print(e)
            """
    """
    def get_queryset(self, request):
        qs = super(ChoiceAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            myAuthor = Author.objects.get(id=140)
            return qs.filter(question__refAuthor_id=myAuthor.id)
            """

site.register(Author,AuthorAdmin)
site.register(Question,QuestionAdmin)
site.register(Choice,ChoiceAdmin)
site.register(Group)
site.register(User)
