""" Core main app user views
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import redirect
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED

from core_main_app.components.version_manager import api as version_manager_api
from core_main_app.settings import INSTALLED_APPS
from core_main_app.utils.rendering import render
from core_main_app.views.user.forms import LoginForm


def custom_login(request):
    """ Custom login page.
    
        Parameters:
            request: 
    
        Returns:
    """
    def _login_redirect(to_page):
        if to_page is not None and to_page != "":
            return redirect(to_page)

        return redirect(reverse("core_main_app_homepage"))

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        next_page = request.POST["next_page"]

        try:
            user = authenticate(username=username, password=password)

            if not user.is_active:
                return render(request, "core_main_app/user/login.html",
                              context={'login_form': LoginForm(initial={'next_page': next_page}), 'login_locked': True,
                                       'with_website_features': "core_website_app" in INSTALLED_APPS})

            login(request, user)

            return _login_redirect(next_page)
        except Exception as e:
            return render(request, "core_main_app/user/login.html",
                          context={'login_form': LoginForm(initial={'next_page': next_page}), 'login_error': True,
                                   'with_website_features': "core_website_app" in INSTALLED_APPS})
    elif request.method == "GET":
        if request.user.is_authenticated():
            return redirect(reverse("core_main_app_homepage"))

        next_page = None
        if "next" in request.GET:
            next_page = request.GET["next"]

        return render(request, "core_main_app/user/login.html",
                      context={'login_form': LoginForm(initial={"next_page": next_page}),
                               'with_website_features': "core_website_app" in INSTALLED_APPS})
    else:
        return HttpResponse(status=HTTP_405_METHOD_NOT_ALLOWED)


def custom_logout(request):
    """ Custom logout page.
    
        Parameters:
            request: 
    
        Returns:
    """
    logout(request)
    return redirect(reverse("core_main_app_login"))


def homepage(request):
    """ Homepage for the website

        Parameters:
            request:

        Returns:
    """
    assets = {
        "js": []
    }

    if finders.find("core_main_app/css/homepage.css") is not None:
        assets["css"] = ["core_main_app/css/homepage.css"]

    if finders.find("core_main_app/js/homepage.js") is not None:
        assets["js"].append(
            {
                "path": "core_main_app/js/homepage.js",
                "is_raw": False
            }
        )

    return render(request, "core_main_app/user/homepage.html", assets=assets)


@login_required(login_url='/login')
def manage_template_versions(request, version_manager_id):
    """View that allows template versions management

    Args:
        request:
        version_manager_id:

    Returns:

    """

    # get the version manager
    version_manager = None
    try:
        version_manager = version_manager_api.get(version_manager_id)
    except:
        # TODO: catch good exception, redirect to error page
        pass

    if not request.user.is_staff and version_manager.user != str(request.user.id):
        raise Exception("You don't have the rights to perform this action.")

    context = get_context_manage_template_versions(version_manager)

    assets = {
                "js": [
                    {
                        "path": 'core_main_app/common/js/templates/versions/set_current.js',
                        "is_raw": False
                    },
                    {
                        "path": 'core_main_app/common/js/templates/versions/restore.js',
                        "is_raw": False
                    },
                    {
                        "path": 'core_main_app/common/js/templates/versions/modals/disable.js',
                        "is_raw": False
                    },
                    {
                        "path": 'core_main_app/common/js/backtoprevious.js',
                        "is_raw": True
                    }
                ]
            }

    modals = ["core_main_app/admin/templates/versions/modals/disable.html"]

    return render(request,
                  'core_main_app/common/templates/versions.html',
                  assets=assets,
                  modals=modals,
                  context=context)


def get_context_manage_template_versions(version_manager):
    """ Get the context to manage the template versions.

    Args:
        version_manager:

    Returns:

    """

    # Use categorized version for easier manipulation in template
    versions = version_manager.versions
    categorized_versions = {
        "available": [],
        "disabled": []
    }
    for index, version in enumerate(versions, 1):
        indexed_version = {
            "index": index,
            "object": version
        }

        if version not in version_manager.disabled_versions:
            categorized_versions["available"].append(indexed_version)
        else:
            categorized_versions["disabled"].append(indexed_version)
    version_manager.versions = categorized_versions

    context = {
        'object_name': 'Template',
        'version_manager': version_manager,
    }

    return context
