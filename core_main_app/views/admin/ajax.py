"""Admin AJAX views
"""
import json

from django.http.response import HttpResponse, HttpResponseBadRequest

from core_main_app.components.template.api import init_template_with_dependencies
from core_main_app.components.template.models import Template
from core_main_app.components.template_version_manager.models import TemplateVersionManager
from core_main_app.components.template import api as template_api
from core_main_app.components.version_manager import api as version_manager_api
from core_main_app.components.template_version_manager import api as template_version_manager_api
import HTMLParser


def disable_template(request):
    """Disables a template

    Args:
        request:

    Returns:

    """
    try:
        version_manager = version_manager_api.get(request.GET['id'])
        version_manager_api.disable(version_manager)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def restore_template(request):
    """Restores a disabled template

    Args:
        request:

    Returns:

    """
    try:
        version_manager = version_manager_api.get(request.GET['id'])
        version_manager_api.restore(version_manager)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def disable_template_version(request):
    """Disables a version of a template

    Args:
        request:

    Returns:

    """
    try:
        version = template_api.get(request.GET['id'])
        version_manager_api.disable_version(version)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def restore_template_version(request):
    """Restores a disabled version of a template

    Args:
        request:

    Returns:

    """
    try:
        version = template_api.get(request.GET['id'])
        version_manager_api.restore_version(version)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def set_current_version(request):
    """Sets the current version of a template

    Args:
        request:

    Returns:

    """
    try:
        version = template_api.get(request.GET['id'])
        version_manager_api.set_current(version)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def edit_template(request):
    """Edit the template

    Args:
        request:

    Returns:

    """
    try:
        version_manager = version_manager_api.get(request.POST['id'])
        version_manager.title = request.POST['title']
        version_manager_api.upsert(version_manager)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def resolve_dependencies(request):
    """Resolve import/includes to avoid local references

    Args:
        request:

    Returns:

    """
    try:
        # Get the parameters
        name = request.POST.get('name', None)
        version_manager_id = request.POST.get('version_manager_id', '')
        filename = request.POST['filename']
        xsd_content = request.POST['xsd_content']
        schema_locations = request.POST.getlist('schemaLocations[]')
        dependencies = request.POST.getlist('dependencies[]')

        # create new object
        template = Template(filename=filename, content=_get_xsd_content_from_html(xsd_content))
        init_template_with_dependencies(template, _get_dependencies_dict(schema_locations, dependencies))

        # get the version manager or create a new one
        if version_manager_id != '':
            template_version_manager = version_manager_api.get(version_manager_id)
        else:
            template_version_manager = TemplateVersionManager(title=name)
        template_version_manager_api.insert(template_version_manager, template)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def _get_dependencies_dict(schema_locations, dependencies):
    """Build a dict from lists of schema locations and dependencies

    Args:
        schema_locations:
        dependencies:

    Returns:

    """
    string_to_python_dependencies = []
    # transform 'None' into python None
    for dependency in dependencies:
        if dependency == 'None':
            string_to_python_dependencies.append(None)
        else:
            string_to_python_dependencies.append(dependency)
    return dict(zip(schema_locations, string_to_python_dependencies))


def _get_xsd_content_from_html(xsd_content):
    """Decodes XSD content from HTML

    Args:
        xsd_content:

    Returns:

    """
    html_parser = HTMLParser.HTMLParser()
    xsd_content = str(html_parser.unescape(xsd_content).encode("utf-8"))
    return xsd_content
