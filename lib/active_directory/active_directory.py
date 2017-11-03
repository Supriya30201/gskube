from db import models as sol_db
from db import db_service
from core import constants
from django.contrib.auth import authenticate
import ldap


def sol_authentication(username, password, domain=None):
    """
    sol_authentication method can be used to check user authentication/authorization of sol application.
    this method handles authentication for django_admin and sol_user.
    :param username:
    :param password:
    :param domain: optional
    :return:
    """
    # prepare response dict, setting default ath to False and default error message.
    # depending on situation, both variables can be changed.
    response_dict = {
        constants.AUTH: False,
        constants.ERROR_MESSAGE: "Invalid Credentials"
    }
    # if domain is not specified, check for django_admin authentication.
    if not domain:
        # using default authenticate method of django framework.
        user = authenticate(username=username, password=password)
        if not user:  # Invalid credentials
            return response_dict  # no need to make any changes to default dict.
        if not user.is_superuser:  # Only Superuser is allowed to login.
            response_dict[constants.ERROR_MESSAGE] = "Authorization Exception, Please contact Administrator."
            return response_dict
        response_dict[constants.AUTH] = True  # as auth is successful changing the auth flag.
        response_dict[constants.DJANGO_USER] = user  # passing the user for further process if any.
        return response_dict

    try:
        # getting the sol_user from database
        user = sol_db.User.objects.filter(username=username)

        # if user is not there in db
        if not user:
            response_dict[constants.ERROR_MESSAGE] = "User does not exist/inactive, Please contact Administrator."
            return response_dict

        user = user.first()
        # also if user is deleted or not active we need to give same exception
        if user.deleted or not user.active:
            response_dict[constants.ERROR_MESSAGE] = "User does not exist/inactive, Please contact Administrator."
            return response_dict

        # getting the AD details
        auth_ad = db_service.get_auth_ad()
        # checking if AD is not configured.
        if not auth_ad:
            response_dict[constants.ERROR_MESSAGE] = "Active directory not configured, Please contact Administrator"
            return response_dict
        # connecting to the AD with given credentials.
        connection = ldap_connection(auth_ad[constants.AUTH_AD_HOST], auth_ad[constants.AUTH_AD_PORT], domain, username,
                                     password)
        connection.unbind_s()
    except ldap.INVALID_CREDENTIALS:
        return response_dict  # no need to change default message.
    except ldap.SERVER_DOWN:  # Unable to connect to Active Directory
        response_dict[constants.ERROR_MESSAGE] = "Unable to connect to AD Server, Please contact Administrator"
        return response_dict
    except ldap.LDAPError, e:  # other LDAP error
        if type(e.message) == dict and 'desc' in e.message:
            response_dict[constants.ERROR_MESSAGE] = e.message['desc']  # passing the error message
            return response_dict
        else:
            response_dict[constants.ERROR_MESSAGE] = "Unable to communicate to Active Directory."
            return response_dict
    response_dict[constants.AUTH] = True  # as there is no issue auth is successful.
    response_dict[constants.SOL_USER] = user  # passing user for further process if any.
    return response_dict


def ldap_connection(host, port, domain, username, password):
    """
    ldap_connection method checks connection to ldap using provided details.
    :param host:
    :param port:
    :param domain:
    :param username:
    :param password:
    :return:
    """
    try:
        domain_user = domain + "\\" + username  # create user with domain\username
        ldap_conn = 'ldap://' + host + ':' + port  # ldap connection string
        connection = ldap.initialize(ldap_conn)  # connection object of ldap
        connection.protocol_version = 3  # specify the version
        connection.set_option(ldap.OPT_REFERRALS, 0)
        connection.simple_bind_s(domain_user, password)  # connect to ldap
        return connection
    except Exception as e:
        e.message['desc'] = e.message['desc'] + "(" + host + ")"  # modify error message and add host details.
        raise e


