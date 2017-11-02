from django.shortcuts import render
from . import constants


def login(request):
    """
    login method is used either to load login page or to authenticate user.
    :param request:
    :return:
    """
    if request.method == constants.GET:
        return render(request, constants.LOGIN_TEMPLATE)
