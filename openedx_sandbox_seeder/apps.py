"""
openedx_sandbox_seeder Django application initialization.
"""

from typing import ClassVar

from django.apps import AppConfig


class OpenedxSandboxSeederConfig(AppConfig):
    """
    Configuration for the openedx_sandbox_seeder Django application.
    """

    name = 'openedx_sandbox_seeder'
    verbose_name = 'Open edX Sandbox Seeder'

    # Required for edx_django_utils.plugins to register this app in INSTALLED_APPS,
    # even though this app has no url_config or settings_config of its own.
    plugin_app: ClassVar[dict] = {}
