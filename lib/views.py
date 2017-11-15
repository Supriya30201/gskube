from core import constants
from django.shortcuts import render
from . import factory
from exception.openstack_session_exception import OpenstackSessionException
from exception.openstack_exception import OpenstackException
from core import views as core_views


def load_hypervisor_projects(request):
    host = request.POST['current_hypervisor']
    if host == '--select--':
        clear_session_variables(request, [constants.PROJECTS, constants.SELECTED_PROJECT,
                                          constants.SELECTED_HYPERVISOR_OBJ])
        return render(request, constants.DASHBOARD_TEMPLATE)
    selected_hypervisor = get_selected_hypervisor(request, host)
    selected_hypervisor[constants.DOMAIN] = request.POST['domain']
    selected_hypervisor[constants.USERNAME] = request.POST['username']
    selected_hypervisor[constants.PASSWORD] = request.POST['password']
    print selected_hypervisor
    error_message = None
    try:
        adapter = factory.get_adapter(selected_hypervisor[constants.TYPE], selected_hypervisor)
        projects, _ = adapter.get_projects_using_unscoped_login()
        request.session[constants.PROJECTS] = projects
        request.session[constants.SELECTED_HYPERVISOR_OBJ] = selected_hypervisor
    except OpenstackException as oe:
        error_message = oe.get_message()
    except Exception as e:
        error_message = e.message
    return render(request, constants.DASHBOARD_TEMPLATE, {'hypervisor_exception': error_message})


def mark_project_selection(request):
    selected_project = request.POST['hypervisor_project']
    if selected_project == '--select--':
        clear_session_variables(request, [constants.SELECTED_PROJECT])
        return render(request, constants.DASHBOARD_TEMPLATE)
    for project in request.session[constants.PROJECTS]:
        if project['id'] == selected_project:
            request.session[constants.SELECTED_PROJECT] = project
            break
    return render(request, constants.DASHBOARD_TEMPLATE)


def get_selected_hypervisor(request, host):
    for hypervisor in request.session[constants.USER_HYPERVISORS]:
        if hypervisor[constants.HOST] == host:
            return hypervisor


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
