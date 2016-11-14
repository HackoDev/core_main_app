import json
from django.http.response import HttpResponse, HttpResponseBadRequest
from core_main_app.components.version_manager import api as version_manager_api
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.utils.xml import get_template_with_server_dependencies
import HTMLParser


def disable_template(request):
    """
    Disable a template
    :param request:
    :return:
    """
    try:
        object_id = request.GET['id']
        version_manager_api.disable(object_id)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def restore_template(request):
    """
    Restore a disabled template
    :param request:
    :return:
    """
    try:
        object_id = request.GET['id']
        version_manager_api.restore(object_id)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def edit_template(request):
    """
    Edit the template
    :param request:
    :return:
    """
    try:
        object_id = request.GET['id']
        object_title = request.GET['title']
        version_manager_api.update_title(object_id, object_title)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def resolve_dependencies(request):
    """
    Resolve import/includes to avoid local references
    :param request:
    :return:
    """
    try:
        html_parser = HTMLParser.HTMLParser()
        xsd_content = str(html_parser.unescape(request.POST['xsd_content']))
        name = request.POST['name']
        filename = request.POST['filename']
        schema_locations = request.POST.getlist('schemaLocations[]')
        dependencies = request.POST.getlist('dependencies[]')

        dependencies_dict = _get_dependencies_dict(schema_locations, dependencies)
        updated_xsd_content = get_template_with_server_dependencies(xsd_content, dependencies_dict)
    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')

    # create new object
    template_version_manager_api.create_manager(template_title=name,
                                                template_filename=filename,
                                                template_content=updated_xsd_content,
                                                template_dependencies=dependencies)

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def _get_dependencies_dict(schema_locations, dependencies):
    """
    Build a dict from lists got from the AJAX
    :param schema_locations:
    :param dependencies:
    :return:
    """
    string_to_python_dependencies = []
    # transform 'None' into python None
    for dependency in dependencies:
        if dependency == 'None':
            string_to_python_dependencies.append(None)
        else:
            string_to_python_dependencies.append(dependency)
    return dict(zip(schema_locations, string_to_python_dependencies))
