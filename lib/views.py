from core import constants
from django.shortcuts import render
from . import factory
from exception.openstack_session_exception import OpenstackSessionException
from exception.openstack_exception import OpenstackException
from core import views as core_views


def create_project(request):
    if request.method == constants.GET:
        return render(request, constants.CREATE_PROJECT_TEMPLATE)

    hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
    domain = hypervisor[constants.DOMAIN]
    name = request.POST["name"]
    description = request.POST["description"]
    message = None
    error_message = None
    try:
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        adapter.create_project(domain, name, description)
        request.session[constants.PROJECTS] = adapter.get_all_projects()
        message = 'Project Created Successfully.'
    except OpenstackSessionException as ose:
        if constants.IS_DJANGO_ADMIN in request.session:
            clear_session_variables(request, [constants.PROJECTS, constants.SELECTED_HYPERVISOR_OBJ])
        error_message = ose.get_message()
    except OpenstackException as oe:
        error_message = oe.get_message()
    except Exception as e:
        error_message = e.message

    if constants.IS_DJANGO_ADMIN in request.session:
        return core_views.hypervisor_management(request, message=message, error_message=error_message)


def update_project(request):
    message = None
    error_message = None
    hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
    try:
        if request.method == constants.GET:
            adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
            adapter.get_project()
    except OpenstackSessionException as ose:
        if constants.IS_DJANGO_ADMIN in request.session:
            clear_session_variables(request, [constants.PROJECTS, constants.SELECTED_HYPERVISOR_OBJ])
            error_message = ose.get_message()
    except OpenstackException as oe:
        error_message = oe.get_message()
    except Exception as e:
        error_message = e.message

    if constants.IS_DJANGO_ADMIN in request.session:
        return core_views.hypervisor_management(request, message=message, error_message=error_message)


def delete_project(request, project_id=None):
    message = None
    error_message = None
    hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
    try:
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        adapter.delete_project(project_id)
        request.session[constants.PROJECTS] = adapter.get_all_projects()
    except OpenstackSessionException as ose:
        if constants.IS_DJANGO_ADMIN in request.session:
            clear_session_variables(request, [constants.PROJECTS, constants.SELECTED_HYPERVISOR_OBJ])
            error_message = ose.get_message()
    except OpenstackException as oe:
        error_message = oe.get_message()
    except Exception as e:
        error_message = e.message

    if constants.IS_DJANGO_ADMIN in request.session:
        return core_views.hypervisor_management(request, message=message, error_message=error_message)


def clear_session_variables(request, variables):
    for variable in variables:
        if variable in request.session:
            del request.session[variable]
