from django.shortcuts import render
from . import constants
from lib.active_directory import active_directory as ad
from django.contrib.auth import login as django_login
from db import db_service
import logging
from lib import factory
import lib
from exception.sol_exception import SOLException
from core import services
from tabulate import tabulate
import sol_email
import reporting
from datetime import datetime

logger = logging.getLogger(__name__)


def load_dashboard(request, error_message=None):
    """
    This method just loads dashboard page.
    :param request:
    :param error_message
    :return:
    """
    return render(request, constants.DASHBOARD_TEMPLATE, {'hypervisor_exception': error_message})


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
    try:
        sol_user = ad.sol_authentication(username, password, domain)
    except Exception as e:
        return render(request, constants.LOGIN_TEMPLATE, {constants.ERROR_MESSAGE: e.message})

    # authenticate method return dict object, which contains "auth" flag to indicate successful authentication.
    if not domain:
        # login django_admin to session so that user can also visit admin site.
        django_login(request, sol_user)
        # set session variables.
        request.session[constants.IS_DJANGO_ADMIN] = True
        request.session[constants.USER] = {constants.USERNAME: username}
    else:
        # for SOL user, we should put first name in session, to show welcome message.
        name = sol_user.full_name.split()
        session_user = {constants.USERNAME: username, constants.USER_FIRST_NAME: name[0]}
        request.session[constants.USER_HYPERVISORS] = db_service.get_hypervisor_of_user(username)
        if sol_user.default_project:
            hypervisor = sol_user.default_project.hypervisor.host
            project_id = sol_user.default_project.project_id
            project_name = sol_user.default_project.name
            domain, username, password = db_service.get_user_creds(hypervisor, username)
            session_user[constants.DEFAULT_HYPERVISOR] = hypervisor
            session_user[constants.DEFAULT_PROJECT] = project_name
            request.session[constants.USER] = session_user
            lib.views.load_hypervisor_projects(request, hypervisor, domain, username, password)
            return lib.views.mark_project_selection(request, project_id)
        request.session[constants.USER] = session_user
    request.session['last_activity'] = datetime.now().isoformat()
    return load_dashboard(request)


def logout(request, error_message=None):
    """
    clear the session and redirect to login page.
    :param request:
    :return:
    """
    for key in request.session.keys():
        del request.session[key]
    request.session.flush()
    return render(request, constants.LOGIN_TEMPLATE, {constants.ERROR_MESSAGE: error_message})


def list_sol_users(request, message=None, error_message=None):
    """
    list_sol_users method retrieves all users from database and converts them to user_list of dictionary.
    :param request:
    :param message: success message
    :param error_message: exception message
    :return:
    """
    # Get all users from user table
    users = db_service.get_user()
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
    try:
        # get user details from auth AD and pass username
        user_detail = ad.retrieve_user_details(db_service.get_auth_ad(), request.POST["id"])

        user_detail[constants.USER_PASSWORD] = request.POST["new_password"]
    # pass the user's details taken from auth AD to create user in local AD
        ad.create_user(db_service.get_local_ad(), user_detail)
    except Exception as e:
            return list_sol_users(request, error_message=e.message)
    # add that created user in SOL database
    db_service.create_user(user_detail)

    subject = " User(created): Welcome to ServiceOnline."
    users_information_table = tabulate(
        [["Name : ", user_detail[constants.USER_FULL_NAME]], ["EmailAddress : ", user_detail[constants.USER_EMAIL]],
         ["Username : ", user_detail[constants.USERNAME]], ["Password:", user_detail[constants.USER_PASSWORD]]])
    name = user_detail[constants.USER_FULL_NAME].split()
    fname = name[0]
    message = "Hi " + fname + ", \n\tWelcome to ServiceOnline. \nRecently Administrator created your account on " \
                              "ServiceOnline. Please find the access details below, \n\n" + users_information_table + \
              "\n\nIn case of any access related issue, please get in touch with Administrator."
    sol_email.send_mail(receiver=user_detail[constants.USER_EMAIL], subject=subject, message=message)

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
    try:
        ad.change_status(db_service.get_local_ad(), username)
    except Exception as e:
        list_sol_users(request, error_message="Unable to (de)active user due to : " + e.message)
    # change that user status from SOL database
    db_service.change_user_status(username)
    user = db_service.get_user(username)
    fullname = user.full_name.split()
    subject = 'SOL: Activation/Deactivation from SOL'
    user_status = "Successfully Activated" if user.active else "Successfully Deactivated"
    message = "Hi " + fullname[0] + ",\n\tYour account has been " + user_status + \
              ", Please contact Administrator in case of any issue."
    sol_email.send_mail(receiver=user.email_id, subject=subject, message=message)
    return list_sol_users(request, message="User (de)activated successfully.")


def delete_user(request, username=None):
    """
    Delete user from AD as well as from SOL db
    :param request
    :param username wants ro delete
    :return render to list_users page with message or error_message
    """
    # pass username with local ad details to delete user from AD
    try:
        ad.delete_user(db_service.get_local_ad(), username)
    except Exception as e:
        list_sol_users(request, error_message=e.message)
    #delete the user from SOL database
    user = db_service.delete_user(username)

    fullname = user.full_name.split()
    subject = 'Thank you for using ServiceOnline'
    message = "Hi " + fullname[0] + ",\n\tRecently your account has been deleted from ServiceOnline, now you " \
                                    "will not be able to access ServiceOnline. Thank you for using our services. " \
                                    "In case if you again want access of ServiceOnline, please get in touch with " \
                                    "Administrator."
    sol_email.send_mail(receiver=user.email_id, subject=subject, message=message)

    return list_sol_users(request, message="User deleted successfully.")


def active_directory_configuration(request):
    # in case if it's GET request redirect to active directory template with AD details if any.
    message = None
    if request.method == constants.GET:
        # if ad details are already stored in db then it should able to see, so we render this details to AD_template
        local_active_directory = db_service.get_local_ad()
        auth_active_directory = db_service.get_auth_ad()
    else:
        #store local AD details in SOL DB
        local_active_directory = {constants.LOCAL_AD_HOST: request.POST[constants.LOCAL_AD_HOST],
                                  constants.LOCAL_AD_PORT: request.POST[constants.LOCAL_AD_PORT],
                                  constants.LOCAL_AD_DN: request.POST[constants.LOCAL_AD_DN],
                                  constants.LOCAL_AD_DOMAIN: request.POST[constants.LOCAL_AD_DOMAIN],
                                  constants.LOCAL_AD_USERNAME: request.POST[constants.LOCAL_AD_USERNAME],
                                  constants.LOCAL_AD_PASSWORD: request.POST[constants.LOCAL_AD_PASSWORD]}
        db_service.store_local_ad(local_active_directory)
        # store auth AD details in SOL DB
        auth_active_directory = {constants.AUTH_AD_HOST: request.POST[constants.AUTH_AD_HOST],
                                 constants.AUTH_AD_PORT: request.POST[constants.AUTH_AD_PORT],
                                 constants.AUTH_AD_DN: request.POST[constants.AUTH_AD_DN],
                                 constants.AUTH_AD_DOMAIN: request.POST[constants.AUTH_AD_DOMAIN],
                                 constants.AUTH_AD_USERNAME: request.POST[constants.AUTH_AD_USERNAME],
                                 constants.AUTH_AD_PASSWORD: request.POST[constants.AUTH_AD_PASSWORD],}
        db_service.store_auth_ad(auth_active_directory)
        # store_ad_in_session(request, local_active_directory)
        message = "AD Details Saved Successfully"

    return render(request, constants.ACTIVE_DIRECTORY_TEMPLATE, {'auth_ad': auth_active_directory,
                                                                 'local_ad': local_active_directory,
                                                                 constants.MESSAGE: message})


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
    try:
        all_groups = ad.load_all_groups(active_directory)
    except Exception as e:
        return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE, {constants.ERROR_MESSAGE: e.message,
                                                                           'user_detail': user_detail})
    # pass user details and AD details to load groups from AD which user is added
    try:
        user_groups = ad.load_all_groups(active_directory, username)
    except Exception as e:
        return render(request, constants.ACTIVE_DIRECTORY_GROUP_TEMPLATE, {constants.ERROR_MESSAGE: e.message,
                                                                           'user_detail': user_detail})

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
    try:
        ad.add_remove_ad_groups(db_service.get_local_ad(), username, groups, add_group)
    except Exception as e:
        return list_active_directory_group(request, username, error_message=e.message)

    user = db_service.get_user(username)
    fullname = user.full_name.split()
    subject = "SOL: add/remove in AD Group"
    add_remove = "assigned " if add_group else "unassigned "
    group_info = tabulate(["Group Name : ", groups])
    message = "Hi " + fullname[0] + ", \n\tYour account's AD configuration has been modified, you are " + add_remove + \
              " to below groups.\n" + group_info + "\nPlease contact Administrator in case of any issue.\n\n"
    sol_email.send_mail(receiver=user.email_id, subject=subject, message=message)

    return list_active_directory_group(request, username, message="Groups processed successfully.")


def openvpn_configuration(request):
    message = None
    if request.method == constants.GET:
        openvpn_conf = db_service.get_openvpn_configuration()
    else:
        openvpn_conf = {constants.OPENVPN_HOST: request.POST[constants.OPENVPN_HOST],
                        constants.OPENVPN_USERNAME: request.POST[constants.OPENVPN_USERNAME],
                        constants.OPENVPN_PASSWORD: request.POST[constants.OPENVPN_PASSWORD],
                        constants.OPENVPN_FOLDER_LOCATION: request.POST[constants.OPENVPN_FOLDER_LOCATION],
                        constants.OPENVPN_TEMP_FOLDER_LOCATION: request.POST[constants.OPENVPN_TEMP_FOLDER_LOCATION]}
        db_service.save_openvpn_configuration(openvpn_conf)
        message = "OpenVPN configuration updated successfully."

    return render(request, constants.OPENVPN_TEMPLATE, {'openvpn_conf': openvpn_conf, constants.MESSAGE: message})


def generate_openvpn_certificate(request, username=None):
    if not username:
        username = request.session[constants.USER][constants.USERNAME]

    try:
        return services.generate_openvpn_certificate(db_service.get_openvpn_configuration(), username)
    except Exception as e:
        if constants.IS_DJANGO_ADMIN in request.session:
            return list_sol_users(request, error_message=e.message)
        return load_dashboard(request, error_message=e.message)


def hypervisor_management(request, message=None, error_message=None):
    if 'hypervisor_id' in request.POST:
        hypervisor_id = request.POST['hypervisor_id']
        sol_user_id = db_service.get_sol_user_id(hypervisor_id=hypervisor_id)
        db_hypervisor = db_service.get_hypervisor(id=hypervisor_id)
        hypervisor = {constants.TYPE: db_hypervisor.type, constants.PROTOCOL: db_hypervisor.protocol,
                      constants.HOST: db_hypervisor.host, constants.PORT: db_hypervisor.port,
                      constants.DOMAIN: request.POST[constants.DOMAIN],
                      constants.USERNAME: request.POST[constants.USERNAME],
                      constants.PASSWORD: request.POST[constants.PASSWORD]}
        try:
            adapter = factory.get_adapter(hypervisor[constants.TYPE], hypervisor)
            adapter.generate_admin_auth()
            adapter.delete_user(sol_user_id)
            db_service.delete_hypervisor(hypervisor_id)
            message = "Hypervisor removed successfully."
        except Exception as e:
            error_message = e.message

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
    db_service.save_user_credentials(user.username, hypervisor.host, domain, constants.HYPERVISOR_SOLUSER_NAME,
                                     user_detail['user_password'])
    db_service.update_hypervisor_user_id(user.username, hypervisor.host, user_detail['user_id'])

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
                                                        constants.DOMAIN: request.POST[constants.DOMAIN],
                                                        constants.USERNAME: request.POST[constants.USERNAME],
                                                        constants.PASSWORD: request.POST[constants.PASSWORD]})
        token, _, _ = adapter.generate_admin_auth()
        request.session[constants.DOMAIN] = request.POST[constants.DOMAIN]
        request.session[constants.SELECTED_HYPERVISOR_OBJ] = {constants.PROTOCOL: hypervisor.protocol,
                                                              constants.HOST: hypervisor.host,
                                                              constants.PORT: hypervisor.port,
                                                              constants.DOMAIN: request.POST[constants.DOMAIN],
                                                              constants.TOKEN: token, constants.TYPE: hypervisor.type,
                                                              constants.USERNAME: request.POST[constants.USERNAME],
                                                              constants.PASSWORD: request.POST[constants.PASSWORD]}

        result = adapter.get_all_projects()
        request.session[constants.PROJECTS] = result

        return hypervisor_management(request)
    except SOLException as se:
        return hypervisor_management(request, error_message=se.get_message())
    except Exception as e:
        return hypervisor_management(request, error_message=e.message)


def smtp_configuration(request):
    message = None
    if request.method == constants.POST:
        smtp_config = {constants.SMTP_SERVER: request.POST[constants.SMTP_SERVER],
                       constants.SMTP_PORT: request.POST[constants.SMTP_PORT],
                       constants.SMTP_USERNAME: request.POST[constants.SMTP_USERNAME],
                       constants.SMTP_PASSWORD: request.POST[constants.SMTP_PASSWORD]}
        db_service.set_smtp_configuration(smtp_config)
        message = "SMTP configuration updated successfully."
    else:
        smtp_config = db_service.get_smtp_configuration()
    return render(request, constants.SMTP_CONFIGURATION_TEMPLATE, {'smtp_config':smtp_config,
                                                                   constants.MESSAGE: message})


def change_password(request):
    if request.method == constants.GET:
        return render(request, constants.CHANGE_PASSWORD_TEMPLATE)

    username = request.session[constants.USER][constants.USERNAME]
    old_password = request.POST['old_password']
    new_password = request.POST['new_password']

    if constants.IS_DJANGO_ADMIN in request.session:
        try:
            ad.sol_authentication(username, old_password)
        except Exception as e:
            return render(request, constants.CHANGE_PASSWORD_TEMPLATE, {constants.ERROR_MESSAGE: e.message})
        db_service.change_password(username, new_password)
    else:
        try:
            ad.change_password(db_service.get_local_ad(), username, old_password, new_password)
        except Exception as e:
            return render(request, constants.CHANGE_PASSWORD_TEMPLATE, {constants.ERROR_MESSAGE: e.message})
    return render(request, constants.CHANGE_PASSWORD_TEMPLATE, {constants.MESSAGE: "Password changed successfully."})


def hypervisor_user_management(request, username=None, message=None, error_message=None):
    if request.method == constants.POST:
        username = request.POST[constants.USERNAME]
        host = request.POST[constants.HOST]
        hypervisor = db_service.get_hypervisor(host)
        domain, sol_username, password = db_service.get_user_creds(host, constants.HYPERVISOR_SOLUSER_NAME)
        user = db_service.get_user(username)
        try:
            adapter = factory.get_adapter(hypervisor.type, {constants.PROTOCOL: hypervisor.protocol,
                                                            constants.HOST: hypervisor.host,
                                                            constants.PORT: hypervisor.port, constants.DOMAIN: domain,
                                                            constants.USERNAME: sol_username,
                                                            constants.PASSWORD: password})
            adapter.generate_admin_auth()
            if 'user_id' in request.POST:
                user_id = request.POST['user_id']
                adapter.delete_user(user_id)
                user_id = None
                message = "User deleted successfully."
            else:
                user_id = adapter.create_user(user.username, request.POST['password'], user.email_id, user.full_name)
                message = "User created successfully."
            db_service.update_hypervisor_user_id(username, host, user_id)
        except Exception as e:
            error_message = e.message

    return render(request, constants.HYPERVISOR_USER_MGMT_TEMPLATE,
                  {'mappings': db_service.get_user_hypervisor_mapping(username), constants.USERNAME: username,
                   constants.MESSAGE: message, constants.ERROR_MESSAGE: error_message})


def get_report(request):
    return render(request, constants.REPORT_TEMPLATE, {'reports_dict': reporting.generate_report()})
