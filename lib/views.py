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
    try:
        hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
        hypervisor[constants.PROJECT_ID] = request.session[constants.SELECTED_PROJECT]['id']
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        instances = adapter.list_servers(request.session[constants.ENDPOINT_URLS], request.session[constants.TOKEN])
        return render(request, constants.INSTANCES_TEMPLATE, {constants.INSTANCES: instances})
    except OpenstackException as oe:
        return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: oe.get_message()})
    except Exception as e:
        return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: e.message})


def create_instance(request, modify=False):
    if request.method == constants.GET:
        try:
            images, networks, flavors = get_image_flavor_network_details(request)
            request.session[constants.IMAGES] = images
            request.session[constants.NETWORKS] = networks
            request.session[constants.FLAVORS] = flavors
        except OpenstackException as oe:
            return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: oe.get_message()})
        except Exception as e:
            return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: e.message})
        return render(request, constants.CREATE_INSTANCE_TEMPLATE, {'button_name': 'Request Server'})

    instance_id = request.POST['request_id']
    request_type = request.POST['request_type'] if 'request_type' in request.POST else None
    if request_type == "approve" or modify:
        try:
            instance = get_instance(request, instance_id)
            hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
            hypervisor[constants.PROJECT_ID] = request.session[constants.SELECTED_PROJECT]['id']
            adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
            server_id = adapter.create_server(instance['name'], instance['image_id'], instance['flavor_id'],
                                              instance['network_id'])
            db_service.update_requested_instance(request_id=instance_id, instance_id=server_id)
            return instance_request(request, load_instance=True, message="Requested instance created successfully.")
        except OpenstackException as oe:
            return instance_request(request, load_instance=True, error_message=oe.get_message())
        except Exception as e:
            return instance_request(request, load_instance=True, error_message=e.message)
    elif request_type == "reject":
        db_service.remove_instance_request(instance_id)
        return instance_request(request, load_instance=True, message="Request rejected successfully.")
    else:
        instance = get_instance(request, instance_id)
        return render(request, constants.CREATE_INSTANCE_TEMPLATE, {'instance': instance, 'modify': True, 'button_name': 'Modify & Approve'})


def get_instance(request, instance_id):
    instances = request.session[constants.REQUESTED_INSTANCES]
    for instance in instances:
        if int(instance['instance_id']) == int(instance_id):
            return instance


def get_image_flavor_network_details(request):
    hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
    hypervisor[constants.PROJECT_ID] = request.session[constants.SELECTED_PROJECT]['id']
    adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
    images = adapter.get_image_list(request.session[constants.ENDPOINT_URLS], request.session[constants.TOKEN])
    networks = adapter.get_network_list(request.session[constants.ENDPOINT_URLS], request.session[constants.TOKEN])
    flavors = adapter.get_flavor_list()
    return images, networks, flavors


def instance_request(request, load_instance=False, message=None, error_message=None):
    if request.method == constants.GET or load_instance:
        instances = db_service.requested_instances(request.session[constants.SELECTED_HYPERVISOR_OBJ],
                                                   request.session[constants.SELECTED_PROJECT])
        instance_list = []
        if instances:
            images, networks, flavors = get_image_flavor_network_details(request)
            request.session[constants.IMAGES] = images
            request.session[constants.FLAVORS] = flavors
            request.session[constants.NETWORKS] = networks
            for instance in instances:
                instance_image = None
                for image in images:
                    if image[constants.IMAGE_ID] == instance.image:
                        instance_image = image[constants.IMAGE_NAME]
                        break
                instance_network = None
                for network in networks:
                    if network[constants.NETWORK_ID] == instance.network:
                        instance_network = network[constants.NETWORK_NAME]
                        break

                instance_flavor = None
                for flavor in flavors:
                    if flavor[constants.FLAVOR_ID] == instance.flavor:
                        instance_flavor = flavor[constants.FLAVOR_NAME]
                        break

                instance_list.append({
                    'instance_id': instance.id,
                    'name': instance.instance_name,
                    'flavor_id': instance.flavor,
                    'flavor_name': instance_flavor,
                    'network_id': instance.network,
                    'network_name': instance_network,
                    'image_id': instance.image,
                    'image_name': instance_image,
                    'username': instance.user.username,
                    'user_f_name': instance.user.full_name,
                    'doe': instance.doe.isoformat()
                })
        request.session[constants.REQUESTED_INSTANCES] = instance_list
        return render(request, constants.REQUESTED_INSTANCES_TEMPLATE, {constants.MESSAGE: message,
                                                                        constants.ERROR_MESSAGE: error_message})

    if 'modify' in request.POST:
        db_service.update_requested_instance(request_id=request.POST['request_id'], image=request.POST['image'],
                                             network=request.POST['network'], flavor=request.POST['flavor'],
                                             doe=request.POST['date'])
        return create_instance(request, modify=True)

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
