from core import constants
from django.shortcuts import render
from django.shortcuts import HttpResponseRedirect
from . import factory
from exception.openstack_session_exception import OpenstackSessionException
import core
from db import db_service


def load_hypervisor_projects(request, hypervisor=None, domain=None, username=None, password=None):
    host = hypervisor if hypervisor else request.POST['current_hypervisor']
    if host == '--select--':
        clear_session_variables(request, [constants.PROJECTS, constants.SELECTED_PROJECT,
                                          constants.SELECTED_HYPERVISOR_OBJ])
        return render(request, constants.DASHBOARD_TEMPLATE)
    selected_hypervisor = get_selected_hypervisor(request, host)
    selected_hypervisor[constants.DOMAIN] = domain if domain else request.POST['domain']
    selected_hypervisor[constants.USERNAME] = username if username else request.POST['username']
    selected_hypervisor[constants.PASSWORD] = password if password else request.POST['password']
    print selected_hypervisor
    error_message = None
    try:
        adapter = factory.get_adapter(selected_hypervisor[constants.TYPE], selected_hypervisor)
        projects, _ = adapter.get_projects_using_unscoped_login()
        request.session[constants.PROJECTS] = projects
        request.session[constants.SELECTED_HYPERVISOR_OBJ] = selected_hypervisor
    except Exception as e:
        error_message = e.message
    return render(request, constants.DASHBOARD_TEMPLATE, {'hypervisor_exception': error_message})


def mark_project_selection(request, project_id=None):
    selected_project = project_id if project_id else request.POST['hypervisor_project']
    if selected_project == '--select--':
        clear_session_variables(request, [constants.SELECTED_PROJECT])
        return render(request, constants.DASHBOARD_TEMPLATE)
    for project in request.session[constants.PROJECTS]:
        if project['id'] == selected_project:
            request.session[constants.SELECTED_PROJECT] = project
            hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
            hypervisor[constants.PROJECT_ID] = project['id']
            adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
            token, endpoint_urls, is_admin = adapter.is_admin_for_project()
            request.session[constants.TOKEN] = token
            request.session[constants.ENDPOINT_URLS] = endpoint_urls
            if is_admin:
                request.session[constants.IS_ADMIN] = True
            break
    return render(request, constants.DASHBOARD_TEMPLATE)


def get_instances_for_extend_expiry(request, load_instances=False, message=None, error_message=None):
    if request.method == constants.GET or load_instances:
        instances = db_service.get_created_instances(request.session[constants.SELECTED_HYPERVISOR_OBJ],
                                                     request.session[constants.SELECTED_PROJECT],
                                                     request.session[constants.USER])
        return render(request, constants.EXTEND_EXPIRY_TEMPLATE, {'instances': instances, constants.MESSAGE: message,
                                                                  constants.ERROR_MESSAGE: error_message})

    instance = db_service.get_created_instances(request.session[constants.SELECTED_HYPERVISOR_OBJ],
                                                request.session[constants.SELECTED_PROJECT],
                                                request.session[constants.USER],
                                                request.POST['instance_id'])
    return render(request, constants.CREATE_INSTANCE_TEMPLATE, {'instance': instance, 'extend': True,
                                                                'button_name': 'Modify'})


def get_selected_hypervisor(request, host):
    for hypervisor in request.session[constants.USER_HYPERVISORS]:
        if hypervisor[constants.HOST] == host:
            return hypervisor


def project_management(request):
    return


def create_project(request, project_id=None):
    message = None
    error_message = None
    try:
        if request.method == constants.GET and not project_id:
            return render(request, constants.CREATE_PROJECT_TEMPLATE)

        hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        if request.method == constants.GET:
            return render(request, constants.CREATE_PROJECT_TEMPLATE, {'project': adapter.get_project(project_id)})

        project_id = None if constants.PROJECT_ID not in request.POST else request.POST[constants.PROJECT_ID]
        domain = hypervisor[constants.DOMAIN]
        name = request.POST["name"]
        description = request.POST["description"]

        adapter.create_project(name, description, domain=domain, project_id=project_id)
        request.session[constants.PROJECTS] = adapter.get_all_projects()
        message = 'Project created/updated successfully.'
    except OpenstackSessionException as ose:
        if constants.IS_DJANGO_ADMIN in request.session:
            clear_session_variables(request, [constants.PROJECTS, constants.SELECTED_HYPERVISOR_OBJ])
        error_message = ose.get_message()
    except Exception as e:
        error_message = e.message

    if constants.IS_DJANGO_ADMIN in request.session:
        return core.views.hypervisor_management(request, message=message, error_message=error_message)


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
    except Exception as e:
        error_message = e.message

    if constants.IS_DJANGO_ADMIN in request.session:
        return core.views.hypervisor_management(request, message=message, error_message=error_message)


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
    except Exception as e:
        error_message = e.message

    if constants.IS_DJANGO_ADMIN in request.session:
        return core.views.hypervisor_management(request, message=message, error_message=error_message)


def project_member_management(request, project_id=None, user_id=None, add=False):
    hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
    try:
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        message = None

        if not project_id:
            project_id = request.session[constants.SELECTED_PROJECT]
        else:
            request.session[constants.USERS] = adapter.get_users()
            request.session[constants.ROLES] = adapter.get_roles()
            request.session[constants.SELECTED_PROJECT] = project_id

        if user_id:
            if add == 'True':
                roles = request.POST.getlist('roles')
                adapter.assign_roles(roles, user_id, project_id)
                message = "Roles assigned successfully."
            else:
                roles = request.POST['roles']
                adapter.revoke_roles(roles.split(","), user_id, project_id)
                message = "Roles revoked successfully."

        project_users = adapter.get_user_roles_project(project_id, request.session[constants.USERS])
        request.session[constants.PROJECT_USERS] = project_users
        return render(request, constants.PROJECT_MEMBER_TEMPLATE, {constants.MESSAGE: message})
    except Exception as e:
        if user_id:
            return render(request, constants.PROJECT_MEMBER_TEMPLATE, {constants.ERROR_MESSAGE: e.message})
        return core.views.hypervisor_management(request, error_message=e.message)


def manage_quota(request, project_id=None):
    hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
    try:
        if project_id:
            request.session[constants.SELECTED_PROJECT] = project_id

        hypervisor[constants.PROJECT_ID] = project_id if project_id else request.session[constants.SELECTED_PROJECT]
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        if request.method == constants.GET:
            return render(request, constants.MANAGE_QUOTA_TEMPLATE,
                          {'quotas': adapter.get_quota_details(project_id, True)})

        quotas = {
            constants.TOTAL_CPU: request.POST[constants.TOTAL_CPU],
            constants.TOTAL_MEMORY: request.POST[constants.TOTAL_MEMORY],
            constants.INSTANCES: request.POST[constants.INSTANCES],
            constants.FIXED_IPS: request.POST[constants.FIXED_IPS],
            constants.FLOATING_IPS: request.POST[constants.FLOATING_IPS],
            constants.SECURITY_GROUPS: request.POST[constants.SECURITY_GROUPS],
            constants.SECURITY_GROUP_RULES: request.POST[constants.SECURITY_GROUP_RULES],
            constants.SERVER_GROUPS: request.POST[constants.SERVER_GROUPS],
            constants.SERVER_GROUP_MEMBERS: request.POST[constants.SERVER_GROUP_MEMBERS]
        }
        adapter.set_quota_details(request.session[constants.SELECTED_PROJECT], quotas)
        return core.views.hypervisor_management(request, message="Quotas updated successfully.")
    except Exception as e:
        return core.views.hypervisor_management(request, error_message=e.message)



def manage_instances(request, message=None, error_message=None):
    try:
        hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
        hypervisor[constants.PROJECT_ID] = request.session[constants.SELECTED_PROJECT]['id']
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        instances = adapter.list_servers(request.session[constants.ENDPOINT_URLS], request.session[constants.TOKEN])
        return render(request, constants.INSTANCES_TEMPLATE, {constants.INSTANCES: instances,
                                                              constants.MESSAGE: message,
                                                              constants.ERROR_MESSAGE: error_message})
    except Exception as e:
        return render(request, constants.INSTANCES_TEMPLATE, {constants.ERROR_MESSAGE: e.message})


def create_instance(request, modify=False):
    if request.method == constants.GET:
        try:
            images, networks, flavors = get_image_flavor_network_details(request)
            request.session[constants.IMAGES] = images
            request.session[constants.NETWORKS] = networks
            request.session[constants.FLAVORS] = flavors
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
        except Exception as e:
            return instance_request(request, load_instance=True, error_message=e.message)
    elif request_type == "reject":
        db_service.remove_instance(instance_id)
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
    if 'extend' in request.POST:
        instance_id = request.POST['request_id']
        doe = request.POST['date']
        db_service.extend_expiry(instance_id, doe)
        return get_instances_for_extend_expiry(request, load_instances=True, message="Expiry extended successfully.")

    db_service.save_instance_request(request.session[constants.SELECTED_HYPERVISOR_OBJ],
                                     request.session[constants.SELECTED_PROJECT], request.session[constants.USER],
                                     request.POST['server_name'], request.POST['image'], request.POST['network'],
                                     request.POST['flavor'], request.POST['date'])
    return render(request, constants.INSTANCES_TEMPLATE, {constants.MESSAGE: "Instance Requested Successfully."})


def hypervisor_preference(request, host=None, remove=False):
    user = request.session[constants.USER]
    if host == 'remove_default':
        db_service.remove_default_hypervisor(user)
        del user[constants.DEFAULT_HYPERVISOR]
        del user[constants.DEFAULT_PROJECT]
        request.session[constants.USER] = user
        return render(request, constants.HYPERVISOR_PREFERENCE_TEMPLATE,
                      {constants.MESSAGE: "Default setting removed successfully."})

    if request.method == constants.GET and not host:
        clear_session_variables(request, [constants.HYPERVISOR_PREFERENCE_PROJECTS,
                                          constants.HYPERVISOR_PREFERENCE_SELECTED_HOST])
        return render(request, constants.HYPERVISOR_PREFERENCE_TEMPLATE)

    domain, username, password = None, None, None

    if host:
        request.session[constants.HYPERVISOR_PREFERENCE_SELECTED_HOST] = host
        domain, username, password = db_service.get_user_creds(host, user[constants.USERNAME])
        if not domain:
            return render(request, constants.HYPERVISOR_ADMIN_LOGIN_TEMPLATE,
                          {'redirect': "/hypervisor_admin/hypervisor_preference/", 'button_name': 'Load Projects'})

    if 'selected_project' in request.POST:
        selected_project_id = request.POST['selected_project']
        selected_project = None
        for project in request.session[constants.HYPERVISOR_PREFERENCE_PROJECTS]:
            if project['id'] == selected_project_id:
                selected_project = project
                break
        db_service.set_default_project(request.session[constants.HYPERVISOR_PREFERENCE_SELECTED_HOST], user,
                                       selected_project)
        user[constants.DEFAULT_PROJECT] = selected_project['name']
        user[constants.DEFAULT_HYPERVISOR] = request.session[constants.HYPERVISOR_PREFERENCE_SELECTED_HOST]
        request.session[constants.USER] = user
        return render(request, constants.HYPERVISOR_PREFERENCE_TEMPLATE,
                      {constants.MESSAGE: "Default project updated successfully."})

    hypervisor = get_selected_hypervisor(request, request.session[constants.HYPERVISOR_PREFERENCE_SELECTED_HOST])
    hypervisor[constants.DOMAIN] = domain if domain else request.POST[constants.DOMAIN]
    hypervisor[constants.USERNAME] = username if username else request.POST[constants.USERNAME]
    hypervisor[constants.PASSWORD] = password if password else request.POST[constants.PASSWORD]
    adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
    request.session[constants.HYPERVISOR_PREFERENCE_PROJECTS], _ = adapter.get_projects_using_unscoped_login()
    db_service.save_user_credentials(user[constants.USERNAME], hypervisor[constants.HOST], hypervisor[constants.DOMAIN],
                                     hypervisor[constants.USERNAME], hypervisor[constants.PASSWORD])
    return render(request, constants.HYPERVISOR_ADMIN_LOGIN_TEMPLATE,
                  {'redirect': "/hypervisor_admin/hypervisor_preference/", 'button_name': 'Save',
                   'domain': hypervisor[constants.DOMAIN], 'username': hypervisor[constants.USERNAME],
                   'password': hypervisor[constants.PASSWORD]})


def instance_action(request, instance_id, action):
    try:
        hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
        hypervisor[constants.PROJECT_ID] = request.session[constants.SELECTED_PROJECT]['id']
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        if action == "start":
            adapter.start_instance(instance_id)
            return manage_instances(request, message="Start instance request submitted successfully.")
        elif action == "stop":
            adapter.stop_instance(instance_id)
            return manage_instances(request, message="Stop instance request submitted successfully.")
        elif action == "modify":
            # can be implemented in future.
            return
        elif action == "console":
            vnc_url = adapter.load_console(instance_id)
            return HttpResponseRedirect(vnc_url)
        elif action == "delete":
            adapter.delete_instance(instance_id)
            db_service.remove_instance(instance_id=instance_id)
            return manage_instances(request, message="Delete instance request submitted successfully.")
    except Exception as e:
        return manage_instances(request, error_message=e.message)


def manage_images(request, message=None, error_message=None):
    try:
        hypervisor = request.session[constants.SELECTED_HYPERVISOR_OBJ]
        adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
        images = adapter.get_image_list(request.session[constants.ENDPOINT_URLS], request.session[constants.TOKEN])
        return render(request, constants.IMAGES_TEMPLATE, {constants.IMAGES: images, constants.MESSAGE: message,
                                                           constants.ERROR_MESSAGE: error_message})
    except Exception as e:
        return render(request, constants.IMAGES_TEMPLATE, {constants.ERROR_MESSAGE: e.message})


def clear_session_variables(request, variables):
    for variable in variables:
        if variable in request.session:
            del request.session[variable]
