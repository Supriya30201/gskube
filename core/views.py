from django.shortcuts import render
from . import constants
from lib.active_directory import active_directory as ad
from django.contrib.auth import login as django_login
from db import models as sol_db
from db import db_service


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
            name = user.user_full_name.split()
            request.session[constants.USER_FIRST_NAME] = name[0]

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
    create user method is used to create a user in AD and sol.
    GET request will load the template and POST request will create a user.
    :param request:
    :return:
    """
    if request.method == constants.GET:
        return render(request, constants.CREATE_USER_TEMPLATE)

    user_detail = ad.retrieve_user_details(db_service.get_auth_ad(), request.POST["id"])
    if constants.ERROR_MESSAGE in user_detail:
        return list_sol_users(request, error_message=user_detail[constants.ERROR_MESSAGE])

    user_detail[constants.USER_PASSWORD] = request.POST["new_password"]

    result = ad.create_user(db_service.get_local_ad(), user_detail)
    if result and constants.ERROR_MESSAGE in result:
        return list_sol_users(request, error_message=result[constants.ERROR_MESSAGE])

    db_service.create_user(user_detail)

    return list_sol_users(request, message="User created successfully.")


def change_user_status(request, username=None):
    result = ad.change_status(db_service.get_local_ad(), username)
    if constants.ERROR_MESSAGE in result:
        list_sol_users(request, error_message=result[constants.ERROR_MESSAGE])

    db_service.change_user_status(username)
    return list_sol_users(request, message=result[constants.MESSAGE])


def delete_user(request, username=None):
    result = ad.delete_user(db_service.get_local_ad(), username)
    if result and constants.ERROR_MESSAGE in result:
        list_sol_users(request, error_message=result[constants.ERROR_MESSAGE])

    db_service.delete_user(username)
    return list_sol_users(request, message="User deleted successfully.")


def active_directory_configuration(request):
    if request.method == constants.GET:
        local_active_directory = db_service.get_local_ad()
        auth_active_directory = db_service.get_auth_ad()
        return render(request, constants.ACTIVE_DIRECTORY_TEMPLATE, {'auth_ad': auth_active_directory,
                                                                     'local_ad': local_active_directory})

    message = None
    error_message = None
    auth_active_directory = None
    local_active_directory = None
    try:
        local_active_directory = db_service.store_local_ad(request.POST['local_ad_ip'], request.POST['local_ad_port'],
                                                           request.POST['local_ad_dn'], request.POST['local_ad_domain'],
                                                           request.POST['local_ad_username'],
                                                           request.POST['local_ad_password'])
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
    user_detail = db_service.get_user(username)
    active_directory = db_service.get_local_ad()
    all_groups = ad.load_all_groups(active_directory)
    if isinstance(all_groups, dict):
        return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE,
                      {constants.ERROR_MESSAGE: all_groups[constants.ERROR_MESSAGE], 'user_detail': user_detail})
    user_groups = ad.load_all_groups(active_directory, username)
    if isinstance(user_groups, dict):
        return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE,
                      {constants.ERROR_MESSAGE: user_groups[constants.ERROR_MESSAGE], 'user_detail': user_detail})

    return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE,
                  {'user_detail': user_detail, 'all_groups': all_groups, 'user_groups': user_groups,
                   constants.MESSAGE: message, constants.ERROR_MESSAGE: error_message})


def add_remove_ad_group(request, username=None, add_group=True):
    groups = request.POST.getlist('groups')
    response = ad.add_remove_ad_groups(db_service.get_local_ad(), username, groups, add_group)
    if response and constants.ERROR_MESSAGE in response:
        return list_active_directory_group(request, username, error_message=response[constants.ERROR_MESSAGE])

    return list_active_directory_group(request, username, message="Groups processed successfully.")


def openvpn_configuration(request):
    if request.method == constants.GET:
        openvpn_conf = db_service.get_openvpn_configuration()
        return render(request, constants.OPENVPN_TEMPLATE, {'openvpn_conf': openvpn_conf})
