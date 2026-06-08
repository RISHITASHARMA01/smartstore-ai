AUTH_BYPASS = True  # Set to False to re-enable auth

from .dependencies import get_current_user, get_current_user_bypass, require_admin


def get_user_dependency():
    if AUTH_BYPASS:
        return get_current_user_bypass
    return get_current_user


def require_admin_dependency():
    if AUTH_BYPASS:
        return get_current_user_bypass
    return require_admin
