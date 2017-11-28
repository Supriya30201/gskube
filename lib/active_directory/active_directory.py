from db import models as sol_db
from db import db_service
from core import constants
from django.contrib.auth import authenticate
import ldap
import winrm
import re as regex
from core import services
from exception.active_directory_exception import ActiveDirectoryException


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
        if isinstance(e.message, dict) and 'desc' in e.message:
            response_dict[constants.ERROR_MESSAGE] = e.message['desc']  # passing the error message
            return response_dict
        else:
            response_dict[constants.ERROR_MESSAGE] = "Unable to communicate to Active Directory."
            return response_dict
    response_dict[constants.AUTH] = True  # as there is no issue auth is successful.
    response_dict[constants.SOL_USER] = user  # passing user for further process if any.
    return response_dict


def retrieve_user_details(active_directory, username):
    """
    Get the details for specified user from auth AD
    :param object of auth AD details(username,host, domain, password)
    :param username
    :return: either user_details list or error_message

    """
    username = str(username).upper()
    conn = None
    try:
        conn = ldap_connection(active_directory[constants.AUTH_AD_HOST], active_directory[constants.AUTH_AD_PORT],
                               active_directory[constants.AUTH_AD_DOMAIN], active_directory[constants.AUTH_AD_USERNAME],
                               services.decode(active_directory[constants.AUTH_AD_PASSWORD]))
        ad_filter = "(&(objectclass=user))";
        attributes = ["distinguishedName", "description", 'name', 'SamAccountName', 'givenName', 'sn', 'mail']
        ldap_result_id = conn.search(active_directory[constants.AUTH_AD_DN], ldap.SCOPE_SUBTREE, ad_filter, attributes)
        result_set = []
        user_detail = {
            constants.USERNAME: username,
        }
        pattern = r'^\s*(\[\'\s*)?|(\s*\'\])?\s*$'
        while 1:
            result_type, result_data = conn.result(ldap_result_id, 0)
            if not result_data or constants.USER_EMAIL in user_detail:
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
                    for result in result_data:
                        temp_dict = result[1]
                        sam_account_name = regex.sub(pattern, '', str(temp_dict['sAMAccountName']))
                        if sam_account_name == username:
                            user_detail[constants.USER_FULL_NAME] = regex.sub(pattern, '', str(temp_dict['name']))
                            user_detail[constants.USER_EMAIL] = regex.sub(pattern, '', str(temp_dict['mail']))
    except ldap.SERVER_DOWN:
        return {constants.ERROR_MESSAGE: "Unable to connect to AD, Please try again."}
    except ldap.LDAPError, e:
        if isinstance(e.message, dict) and 'desc' in e.message:
            return {constants.ERROR_MESSAGE: "Other LDAP error: " + e.message['desc']}
        else:
            return {constants.ERROR_MESSAGE: "Other LDAP error: " + e}
    finally:
        if conn is not None:
            conn.unbind_s()

    return user_detail


def create_user(active_directory, user_detail):
    name = user_detail[constants.USER_FULL_NAME].split()
    fname = name[0]
    lname = name[len(name) - 1]
    name = user_detail[constants.USER_FULL_NAME]
    user_name = user_detail[constants.USERNAME]
    email = user_detail[constants.USER_EMAIL]
    password = user_detail[constants.USER_PASSWORD]
    try:
        script = 'New-ADUser "' + name + '" -GivenName "' + fname + '" -SurName "' + lname + '" -DisplayName "' + name \
                 + '" -EmailAddress "' + email + '" -SamAccountName "' + user_name + \
                 '" -AccountPassword (ConvertTo-SecureString  -Force -AsPlainText -String "' + password + \
                 '") | Set-ADuser -ChangePasswordAtLogon $False '

        execute_script_winrm(active_directory, script)

        execute_script_winrm(active_directory, 'Enable-ADAccount -Identity "' + user_name + '"')

    except Exception as e:
        if 'The specified account already exists' not in e.message:
            execute_script_winrm(active_directory, 'Remove-ADUser -Identity "' + user_name + '" -Confirm:$false')
        raise e


def change_status(active_directory, username):
    user = sol_db.User.objects.get(username=username)
    script = 'Enable-ADAccount -Identity "' + username + '"'

    if bool(user.active):
        script = 'Disable-ADAccount -Identity "' + username + '"'

    execute_script_winrm(active_directory, script)


def delete_user(active_directory, username):
    """
     Delete user from Active Directory
      :param object of local AD details
      :param :username that wants to delete
      :return: error message or either none
    """
    script = 'Remove-ADUser -Identity "' + username + '" -Confirm:$false'
    execute_script_winrm(active_directory, script)


def load_all_groups(active_directory, username=None):
    """
    It will get the list of all groups from AD or if username given then get the groups in which user exist
    :param active_directory: object of local AD details
    :param username
    :return: group list or either error_message
    """
    script = 'Get-ADGroup -Filter *' if not username else 'Get-ADPrincipalGroupMembership -Identity "' + username + '"'
    script = script + ' | Select Name'

    groups = filter(None, execute_script_winrm(active_directory, script).split('\r\n'))
    group_list = []
    for group in range(2, len(groups), 1):
        group_list.append(groups[group].strip())
    return group_list


def add_remove_ad_groups(active_directory, username, groups, add_group):
    """
    It will assign the one or more group to user or either remove it
    :param active_directory: object of local AD details
    :param username: which wants to get add/remove
    :param groups:
    :param add_group: its flag, its value decide to get added or removed
    :return: error_message or either  none
    """
    script = 'Remove-ADGroupMember "' if not add_group else 'Add-ADGroupMember "'
    for group in groups:
        try:
            execute_script_winrm(active_directory, script + group + '" "' + username + '"')
        except Exception as e:
            e.message = 'Unable to process "' + group + '" due to : ' + e.message
            raise e


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


def change_password(active_directory, username, old_password, new_password):
    try:
        connection = ldap_connection(active_directory[constants.LOCAL_AD_HOST],
                                     active_directory[constants.LOCAL_AD_PORT],
                                     active_directory[constants.LOCAL_AD_DOMAIN], username, old_password)
        connection.unbind_s()

        script = 'Set-ADAccountPassword -Reset -PassThru -Identity ' + username + \
                 ' -NewPassword (ConvertTo-SecureString  -Force -AsPlainText -String ' + new_password + \
                 ')| Set-ADuser -ChangePasswordAtLogon $False'
        execute_script_winrm(active_directory, script)

    except ldap.INVALID_CREDENTIALS:
        raise ActiveDirectoryException(message="Invalid old password, please try again.")


def execute_script_winrm(active_directory, script):
    """
    To execute AD powershell commands in windows machine (to perform AD operations)
    This method executes winrm script.
    we are executing script on local AD that's why we have used auth="0" while getting AD_Server_Details
      :param :  server_ip, port, domain, username, password etc
      :return : return either success response or error Message
   """
    try:
        s = winrm.Session(active_directory[constants.LOCAL_AD_HOST],
                          auth=(active_directory[constants.LOCAL_AD_USERNAME],
                                services.decode(active_directory[constants.LOCAL_AD_PASSWORD])))
        output = s.run_ps(script)

        if output.status_code != 0:
            raise ActiveDirectoryException(message=output.std_err)
        return output.std_out
    except Exception as e:
        raise e
