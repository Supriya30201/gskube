from core import constants
from django.shortcuts import render
from . import factory
from exception.openstack_session_exception import OpenstackSessionException
from exception.openstack_exception import OpenstackException
from core import views as core_views
from db import db_service


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
            hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
            adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
            token, endpoint_urls, is_admin = adapter.is_admin_for_project(project['id'])
            request.session[constants.TOKEN] = token
            request.session[constants.ENDPOINT_URLS] = endpoint_urls
            if is_admin:
                request.session[constants.IS_ADMIN] = True
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


def manage_instances(request):
    return render(request, constants.INSTANCES_TEMPLATE)


def create_instance(request, instance_id=None):
    if request.method == constants.GET:
        try:
            hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
            hypervisor[constants.PROJECT_ID] = request.session[constants.SELECTED_PROJECT]['id']
            adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
            request.session[constants.IMAGES] = adapter.get_image_list(request.session[constants.ENDPOINT_URLS],
                                                                       request.session[constants.TOKEN])
            request.session[constants.NETWORKS] = adapter.get_network_list(request.session[constants.ENDPOINT_URLS],
                                                                           request.session[constants.TOKEN])
            request.session[constants.FLAVORS] = adapter.get_flavor_list()
        except OpenstackException as oe:
            return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: oe.get_message()})
        except Exception as e:
            return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: e.message})
        return render(request, constants.CREATE_INSTANCE_TEMPLATE, {'button_name': 'Request Server'})


def save_instance_request(request):
    db_service.save_instance_request(request.session[constants.SELECTED_HYPERVISOR_OBJ],
                                     request.session[constants.SELECTED_PROJECT], request.session[constants.USER],
                                     request.POST['server_name'], request.POST['image'], request.POST['network'],
                                     request.POST['flavor'], request.POST['date'])
    return render(request, constants.INSTANCES_TEMPLATE, {constants.MESSAGE: "Instance Requested Successfully."})


def hypervisor_preference(request):
    if request.method == constants.GET:
        return render(request, constants.HYPERVISOR_PREFERENCE_TEMPLATE)


def hypervisor_preference_change(request, host=None):
    if request.method == constants.GET:
        request.session[constants.HYPERVISOR_PREFERENCE_SELECTED_HOST] = host
        return render(request, constants.HYPERVISOR_ADMIN_LOGIN_TEMPLATE,
                      {'redirect': "/hypervisor_admin/hypervisor_preference_change/", 'button_name': 'Load Projects'})
    if 'selected_project' in request.POST:
        return

    hypervisor = get_selected_hypervisor(request, request.session[constants.HYPERVISOR_PREFERENCE_SELECTED_HOST])
    hypervisor[constants.DOMAIN] = request.POST[constants.DOMAIN]
    hypervisor[constants.USERNAME] = request.POST[constants.USERNAME]
    hypervisor[constants.PASSWORD] = request.POST[constants.PASSWORD]
    adapter = factory.get_adapter(hypervisor[constants.TYPE, hypervisor])
    request.session[constants.HYPERVISOR_PREFERENCE_PROJECTS] = adapter.get_projects_using_unscoped_login()
    return render(request, constants.HYPERVISOR_ADMIN_LOGIN_TEMPLATE,
                  {'redirect': "{% url 'hypervisor_preference_change' %}", 'button_name': 'Save'})




def clear_session_variables(request, variables):
    for variable in variables:
        if variable in request.session:
            del request.session[variable]
