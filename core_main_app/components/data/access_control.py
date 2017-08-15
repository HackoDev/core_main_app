""" Set of functions to define the rules for access control
"""

from core_main_app.utils.access_control.exceptions import AccessControlError
from core_main_app.utils.raw_query.mongo_raw_query import add_access_criteria
from core_workspace_app.components.workspace import api as workspace_api

from django.conf import settings


def can_read_data_id(func, data_id, user):
    """ Can read data.

    Args:
        func:
        data_id:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(data_id, user)

    data = func(data_id, user)
    _check_can_read_data(data, user)
    return data


def can_write_data(func, data, user):
    """ Can write data.

    Args:
        func:
        data:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(data, user)

    _check_can_write_data(data, user)
    return func(data, user)


def can_read_data(func, data, user):
    """ Can read data.

    Args:
        func:
        data:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(data, user)

    _check_can_read_data(data, user)
    return func(data, user)


def can_read_data_query(func, query, user):
    """ Can read a data, given a query.

    Args:
        func:
        query:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(query, user)

    # update the query
    query = _update_can_read_query(query, user)
    # get list of data
    data_list = func(query, user)
    # TODO: check if necessary because it is time consuming (checking that user has access to list of returned data)
    # check that user can access the list of data
    _check_can_read_data_list(data_list, user)
    return data_list


def can_read_user(func, user):
    """ Can read data, given a user.

    Args:
        func:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(user)

    # get list of data
    data_list = func(user)
    # check that the user can access the list of data
    _check_can_read_data_list(data_list, user)
    # return list of data
    return data_list


def can_change_owner(func, data, new_user, user):
    """ Can user change data's owner.

    Args:
        func:
        data:
        new_user:
        user:

    Returns:

    """
    if user.is_superuser:
        return func(data, new_user, user)

    if data.user_id != str(user.id):
        raise AccessControlError("The user doesn't have enough rights to access this data.")

    return func(data, new_user, user)


def _check_can_write_data(data, user):
    """ Check that the user can write a data.

    Args:
        data:
        user:

    Returns:

    """
    # workspace case
    if 'core_workspace_app' in settings.INSTALLED_APPS:
        if data.user_id != str(user.id):
            if hasattr(data, 'workspace') and data.workspace is not None:
                # get list of accessible workspaces
                accessible_workspaces = workspace_api.get_all_workspaces_with_write_access_by_user(user)
                # check that accessed data belongs to an accessible workspace
                if data.workspace not in accessible_workspaces:
                    raise AccessControlError("The user doesn't have enough rights to access this data.")
            # workspace is not set
            else:
                raise AccessControlError("The user doesn't have enough rights to access this data.")
    # general case
    else:
        # general case: owner can write data
        if data.user_id != str(user.id):
            raise AccessControlError("The user doesn't have enough rights to access this data.")


def _check_can_read_data(data, user):
    """ Check that the user can read a data.

    Args:
        data:
        user:

    Returns:

    """
    # workspace case
    if 'core_workspace_app' in settings.INSTALLED_APPS:
        if data.user_id != str(user.id):
            # workspace is set
            if hasattr(data, 'workspace') and data.workspace is not None:
                # get list of accessible workspaces
                accessible_workspaces = workspace_api.get_all_workspaces_with_read_access_by_user(user)
                # check that accessed data belongs to an accessible workspace
                if data.workspace not in accessible_workspaces:
                    raise AccessControlError("The user doesn't have enough rights to access this data.")
            # workspace is not set
            else:
                raise AccessControlError("The user doesn't have enough rights to access this data.")
    else:
        # general case: users can read other users data
        pass


def _check_can_read_data_list(data_list, user):
    """ Check that the user can read each data of the list.

    Args:
        data_list:
        user:

    Returns:

    """
    if 'core_workspace_app' in settings.INSTALLED_APPS:
        # get list of accessible workspaces
        accessible_workspaces = workspace_api.get_all_workspaces_with_read_access_by_user(user)
        # check that all data belong to a workspace accessible by the user
        wrong_workspace_data = data_list.filter(user_id__ne=str(user.id),
                                                workspace__ne=None,
                                                workspace__nin=accessible_workspaces).all()
        if len(wrong_workspace_data) > 0:
            raise AccessControlError("The user doesn't have enough rights to access this data.")
        # check that all data outside any workspace belong to the user
        wrong_owner_data = data_list.filter(workspace=None,
                                            user_id__nin=str(user.id)).all()
        if len(wrong_owner_data) > 0:
            raise AccessControlError("The user doesn't have enough rights to access this data.")
    else:
        # general case: users can read other users data
        pass


def _update_can_read_query(query, user):
    """ Update query with access control parameters.

    Args:
        query:
        user:

    Returns:

    """

    # workspace case
    if 'core_workspace_app' in settings.INSTALLED_APPS:
        # list accessible workspaces
        accessible_workspaces = [workspace.id for workspace in
                                 workspace_api.get_all_workspaces_with_read_access_by_user(user)]
        # update query with workspace criteria
        query = add_access_criteria(query, accessible_workspaces, user)
    else:
        # general case: users can read other users data
        pass

    return query