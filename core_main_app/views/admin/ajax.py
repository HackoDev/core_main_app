"""Admin AJAX views
"""
import HTMLParser
import json

from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponse, HttpResponseBadRequest

from core_main_app.commons.exceptions import NotUniqueError
from core_main_app.components.template.api import init_template_with_dependencies
from core_main_app.components.template.models import Template
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.components.template_version_manager.models import TemplateVersionManager
from core_main_app.components.version_manager import api as version_manager_api
from core_main_app.components.xsl_transformation import api as xsl_transformation_api
from core_main_app.components.xsl_transformation.models import XslTransformation
from core_main_app.views.admin.forms import EditXSLTForm
from core_main_app.views.common.ajax import EditObjectModalView, DeleteObjectModalView


def resolve_dependencies(request):
    """Resolve import/includes to avoid local references.

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
        return HttpResponseBadRequest(e.message)

    return HttpResponse(json.dumps({}), content_type='application/javascript')


def _get_dependencies_dict(schema_locations, dependencies):
    """Build a dict from lists of schema locations and dependencies.

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
    """Decode XSD content from HTML.

    Args:
        xsd_content:

    Returns:

    """
    html_parser = HTMLParser.HTMLParser()
    xsd_content = str(html_parser.unescape(xsd_content).encode("utf-8"))
    return xsd_content


class EditXSLTView(EditObjectModalView):
    form_class = EditXSLTForm
    model = XslTransformation
    success_url = reverse_lazy("admin:core_main_app_xslt")
    success_message = 'XSLT edited with success.'

    def _save(self, form):
        # Save treatment.
        try:
            xsl_transformation_api.upsert(self.object)
        except NotUniqueError:
            form.add_error(None, "An object with the same name already exists. Please choose "
                                 "another name.")
        except Exception, e:
            form.add_error(None, e.message)


class DeleteXSLTView(DeleteObjectModalView):
    model = XslTransformation
    success_url = reverse_lazy("admin:core_main_app_xslt")
    success_message = 'XSLT deleted with success.'
    field_for_name = 'name'

    def _delete(self, request, *args, **kwargs):
        # Delete treatment.
        xsl_transformation_api.delete(self.object)
