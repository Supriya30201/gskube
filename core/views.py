from django.shortcuts import render
from . import constants
from lib.active_directory import active_directory as ad
from django.contrib.auth import login as django_login
from db import models as sol_db


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
