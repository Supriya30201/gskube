from django.shortcuts import render
from . import constants
from lib.active_directory import active_directory as ad
from django.contrib.auth import login as django_login
from db import models as sol_db
from db import db_service
import logging
from lib import factory
from exception.sol_exception import SOLException

logger = logging.getLogger(__name__)


def load_dashboard(request):
    """
    This method just loads dashboard page.
    :param request:
    :return:
    """
    return render(request, constants.DASHBOARD_TEMPLATE)


def login(request):
    """
    login method is used either to load login page or to authenticate user.
    :param request:
    :return:
    """
    # in case if it's GET request redirect to login page.
    if request.method == constants.GET:
        return logout(request)

    # get values for domain, username and password
    domain = request.POST['domain']
    username = request.POST['username']
    password = request.POST['password']

    # pass credentials with domain to authenticate method
    auth_resp = ad.sol_authentication(username, password, domain)

    # authenticate method return dict object, which contains "auth" flag to indicate successful authentication.
    if auth_resp[constants.AUTH]:
        # if domain is not specified, it should be a django_admin
        if not domain:
            # login django_admin to session so that user can also visit admin site.
            django_login(request, auth_resp[constants.DJANGO_USER])
            # set session variables.
            request.session[constants.IS_DJANGO_ADMIN] = True
        else:
            # for SOL user, we should put first name in session, to show welcome message.
            user = auth_resp[constants.SOL_USER]
            name = user.full_name.split()
            request.session[constants.USER] = {constants.USERNAME: username, constants.USER_FIRST_NAME: name[0]}
            request.session[constants.USER_HYPERVISORS] = db_service.get_hypervisor_of_user(username)

        return load_dashboard(request)

    return render(request, constants.LOGIN_TEMPLATE, {constants.ERROR_MESSAGE: auth_resp[constants.ERROR_MESSAGE]})


def logout(request):
    """
    clear the session and redirect to login page.
    :param request:
    :return:
    """
    for key in request.session.keys():
        del request.session[key]
    request.session.flush()
    return render(request, constants.LOGIN_TEMPLATE)


def list_sol_users(request, message=None, error_message=None):
    """
    list_sol_users method retrieves all users from database and converts them to user_list of dictionary.
    :param request:
    :param message: success message
    :param error_message: exception message
    :return:
    """
    # Get all users from user table
    users = sol_db.User.objects.all()
    user_list = []

    # will enable this while adding code for single page project management
    # remove_variables_from_session(request, {constants.ADD_REMOVE_USER_OPENSTACK, constants.ADD_REMOVE_OPENSTACK})

    # iterate over users and add them to list
    for user in users:
        # split user full name to first name and last name
        name = user.full_name.split()
        if not user.deleted:
            user_list.append({'username': user.username,
                              'fname': name[0],
                              # In case if user do not have last name this won't throw error
                              'lname': name[len(name)-1],
                              'email': user.email_id,
                              'active': user.active})

    return render(request, constants.USERS_TEMPLATE, {'users': user_list, constants.MESSAGE: message,
                                                      constants.ERROR_MESSAGE: error_message})


def create_user(request):
    """
    create user method is used to create a user in AD and in sol db.
    GET request will load the template and POST request will create a user.
    :param request:
    :return:
    """
    # in case if it's GET request redirect to create user page.
    if request.method == constants.GET:
        return render(request, constants.CREATE_USER_TEMPLATE)
    # get user details from auth AD and pass username
    user_detail = ad.retrieve_user_details(db_service.get_auth_ad(), request.POST["id"])
    if constants.ERROR_MESSAGE in user_detail:
        return list_sol_users(request, error_message=user_detail[constants.ERROR_MESSAGE])

    user_detail[constants.USER_PASSWORD] = request.POST["new_password"]
    # pass the user's details taken from auth AD to create user in local AD
    result = ad.create_user(db_service.get_local_ad(), user_detail)
    if result and constants.ERROR_MESSAGE in result:
        return list_sol_users(request, error_message=result[constants.ERROR_MESSAGE])
    # add that created user in SOL database
    db_service.create_user(user_detail)

    return list_sol_users(request, message="User created successfully.")


def change_user_status(request, username=None):
    """
      Change AD user's status i.e activate or deactivate
       Change the active flag form SOL db
        :param request
        :param username wants to create it in AD
        :return render to list_users page with message or error_message
    """
    # pass username and local ad details to change the AD user's status
    result = ad.change_status(db_service.get_local_ad(), username)
    if constants.ERROR_MESSAGE in result:
        list_sol_users(request, error_message=result[constants.ERROR_MESSAGE])
    # change that user status from SOL database
    db_service.change_user_status(username)
    return list_sol_users(request, message=result[constants.MESSAGE])


def delete_user(request, username=None):
    """
    Delete user from AD as well as from SOL db
    :param request
    :param username wants ro delete
    :return render to list_users page with message or error_message
    """
    # pass username with local ad details to delete user from AD
    result = ad.delete_user(db_service.get_local_ad(), username)
    if result and constants.ERROR_MESSAGE in result:
        list_sol_users(request, error_message=result[constants.ERROR_MESSAGE])
    #delete the user from SOL database
    db_service.delete_user(username)
    return list_sol_users(request, message="User deleted successfully.")


def active_directory_configuration(request):
    """
    Store the AD details in SOL database
    :param request:
    :return:
    """
    # in case if it's GET request redirect to active directory template with AD details if any.
    if request.method == constants.GET:
        # if ad details are already stored in db then it should able to see, so we render this details to AD_template
        local_active_directory = db_service.get_local_ad()
        auth_active_directory = db_service.get_auth_ad()
        return render(request, constants.ACTIVE_DIRECTORY_TEMPLATE, {'auth_ad': auth_active_directory,
                                                                     'local_ad': local_active_directory})

    message = None
    error_message = None
    auth_active_directory = None
    local_active_directory = None
    try:
        #store local AD details in SOL DB
        local_active_directory = db_service.store_local_ad(request.POST['local_ad_ip'], request.POST['local_ad_port'],
                                                           request.POST['local_ad_dn'], request.POST['local_ad_domain'],
                                                           request.POST['local_ad_username'],
                                                           request.POST['local_ad_password'])
        # store auth AD details in SOL DB
        auth_active_directory = db_service.store_auth_ad(request.POST['auth_ad_ip'], request.POST['auth_ad_port'],
                                                         request.POST['auth_ad_dn'], request.POST['auth_ad_domain'],
                                                         request.POST['auth_ad_username'],
                                                         request.POST['auth_ad_password'])
        # store_ad_in_session(request, local_active_directory)
        message = "AD Details Saved Successfully"
    except Exception as e:
        if isinstance(e.message, dict):
            error_message = 'Unable to connect AD : ' + e.message['desc']
        else:
            error_message = "Unable to connect AD : " + e.message

    return render(request, constants.ACTIVE_DIRECTORY_TEMPLATE, {'auth_ad': auth_active_directory,
                                                                 'local_ad': local_active_directory,
                                                                 'message': message, 'error_message': error_message})


def list_active_directory_group(request, username=None, message=None, error_message=None):
    """
    List all the groups from local AD, and if username is given it will list groups accordingly
    :param request:
    :param username:
    :param message:
    :param error_message:
    :return:
    """
    # get the user details
    user_detail = db_service.get_user(username)
    #get AD details
    active_directory = db_service.get_local_ad()
    # pass AD details to load all groups from AD
    all_groups = ad.load_all_groups(active_directory)
    if isinstance(all_groups, dict):
        return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE,
                      {constants.ERROR_MESSAGE: all_groups[constants.ERROR_MESSAGE], 'user_detail': user_detail})
    # pass user details and AD details to load groups from AD which user is added
    user_groups = ad.load_all_groups(active_directory, username)
    if isinstance(user_groups, dict):
        return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE,
                      {constants.ERROR_MESSAGE: user_groups[constants.ERROR_MESSAGE], 'user_detail': user_detail})

    return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE,
                  {'user_detail': user_detail, 'all_groups': all_groups, 'user_groups': user_groups,
                   constants.MESSAGE: message, constants.ERROR_MESSAGE: error_message})


def add_remove_ad_group(request, username=None, add_group=True):
    """
    Add/Remove the groups from specified username
    :param request:
    :param username:
    :param add_group:
    :return:
    """
    #get the list of group from html
    groups = request.POST.getlist('groups')
    response = ad.add_remove_ad_groups(db_service.get_local_ad(), username, groups, add_group)
    if response and constants.ERROR_MESSAGE in response:
        return list_active_directory_group(request, username, error_message=response[constants.ERROR_MESSAGE])

    return list_active_directory_group(request, username, message="Groups processed successfully.")


def openvpn_configuration(request):

    if request.method == constants.GET:
        openvpn_conf = db_service.get_openvpn_configuration()
        return render(request, constants.OPENVPN_TEMPLATE, {'openvpn_conf': openvpn_conf})


def hypervisor_management(request, message=None, error_message=None):

    return render(request, constants.HYPERVISORS_TEMPLATE, {'hypervisors': db_service.load_hypervisors(),
                                                            constants.MESSAGE: message,
                                                            constants.ERROR_MESSAGE: error_message})


def create_hypervisor(request):
    if request.method == constants.GET:
        return render(request, constants.CREATE_HYPERVISOR_TEMPLATE)

    hypervisor_type = request.POST['hypervisor_type']
    protocol = request.POST['protocol']
    host = request.POST['host']
    port = request.POST['port']
    domain = request.POST['domain']
    username = request.POST['username']
    password = request.POST['password']

    adapter = factory.get_adapter(hypervisor_type, {constants.PROTOCOL: protocol, constants.HOST: host,
                                                    constants.PORT: port, constants.DOMAIN: domain,
                                                    'username': username, 'password': password})
    user_detail = adapter.create_sol_user()

    if constants.ERROR_MESSAGE in user_detail:
        return hypervisor_management(request, error_message=user_detail[constants.ERROR_MESSAGE])

    hypervisor = db_service.create_hypervisor(hypervisor_type, protocol, host, port)
    user = db_service.get_user(constants.HYPERVISOR_SOLUSER_NAME)
    if not user:
        user = db_service.create_user({constants.USERNAME: constants.HYPERVISOR_SOLUSER_NAME,
                                       constants.USER_EMAIL: constants.HYPERVISOR_SOLUSER_EMAIL,
                                       constants.USER_FULL_NAME: constants.HYPERVISOR_SOLUSER_NAME})
    db_service.save_user_credentials(user, hypervisor, domain, constants.HYPERVISOR_SOLUSER_NAME,
                                     user_detail['user_password'])
    db_service.update_hypervisor_user_id(user, hypervisor, user_detail['user_id'])

    return hypervisor_management(request, message='Hypervisor added successfully.')


def assign_hypervisor(request, hypervisor_id=None, username=None):
    message = None
    error_message = None
    if username:
        db_service.set_hypervisor_user_access(username, hypervisor_id, False)

    if request.method == constants.POST:
        username = request.POST['username']
        hypervisor_id = request.POST['hypervisor_id']
        db_service.set_hypervisor_user_access(username, hypervisor_id)

    users = db_service.get_user()
    hypervisor_users = db_service.get_hypervisor_users(hypervisor_id)
    return render(request, constants.HYPERVISOR_USERS_TEMPLATE, {'hypervisor_id': hypervisor_id, 'users': users,
                                                                 'hypervisor_users': hypervisor_users,
                                                                 constants.MESSAGE: message,
                                                                 constants.ERROR_MESSAGE: error_message})


def load_projects(request, host=None):
    if request.method == constants.GET:
        request.session[constants.SELECTED_HYPERVISOR] = host
        return render(request, constants.HYPERVISOR_ADMIN_LOGIN_TEMPLATE)
    hypervisor = db_service.get_hypervisor(request.session[constants.SELECTED_HYPERVISOR])
    try:
        adapter = factory.get_adapter(hypervisor.type, {constants.PROTOCOL: hypervisor.protocol,
                                                        constants.HOST: hypervisor.host,
                                                        constants.PORT: hypervisor.port,
                                                        constants.DOMAIN: request.POST['domain'],
                                                        'username': request.POST['username'],
                                                        'password': request.POST['password']})
        token, _ = adapter.generate_admin_auth()
        request.session[constants.DOMAIN] = request.POST['domain']
        request.session[constants.SELECTED_HYPERVISOR_OBJ] = {constants.PROTOCOL: hypervisor.protocol,
                                                              constants.HOST: hypervisor.host,
                                                              constants.PORT: hypervisor.port,
                                                              constants.DOMAIN: request.POST['domain'],
                                                              constants.TOKEN: token, constants.TYPE: hypervisor.type}

        result = adapter.get_all_projects()
        request.session[constants.PROJECTS] = result

        return hypervisor_management(request)
    except SOLException as se:
        return hypervisor_management(request, error_message=se.get_message())
    except Exception as e:
        return hypervisor_management(request, error_message=e.message)
