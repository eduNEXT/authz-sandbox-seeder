"""
authz_sandbox_seeder Django application initialization.
"""

from typing import ClassVar

from django.apps import AppConfig


class AuthzSandboxSeederConfig(AppConfig):
    """
    Configuration for the authz_sandbox_seeder Django application.
    """

    name = 'authz_sandbox_seeder'
    verbose_name = 'Open edX Sandbox Seeder'

    # Required for edx_django_utils.plugins to register this app in INSTALLED_APPS,
    # even though this app has no url_config or settings_config of its own.
    plugin_app: ClassVar[dict] = {}
