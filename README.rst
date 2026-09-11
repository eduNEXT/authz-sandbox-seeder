openedx-sandbox-seeder
######################

|pypi-badge| |ci-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge| |status-badge|

Purpose
*******

A Django app that adds a single management command, ``seed_sandbox_data``, to an
Open edX install. It creates organizations, courses, content libraries, users, and
`openedx-authz <https://github.com/openedx/openedx-authz>`_ role assignments from a
JSON fixture, so a Sandbox is ready to test course-authoring permissions (course
staff, admin, editor, auditor, library admin, ...) without setting any of that up by
hand. It's idempotent: running it again only creates what's missing.

This started as a management command inside openedx-authz itself
(`openedx-authz#382 <https://github.com/openedx/openedx-authz/issues/382>`_), and was
pulled out into its own package per the discussion on
`openedx-authz#429 <https://github.com/openedx/openedx-authz/pull/429#issuecomment-5605235326>`_:
a plain Django app (rather than a Tutor-only plugin) works for Tutor and non-Tutor
deployments alike, and keeps openedx-authz itself free of a command that's specific
to populating a test environment.

Installation
************

Install it into your LMS/CMS virtualenv like any other Open edX plugin:

.. code-block:: bash

    pip install git+https://github.com/eduNEXT/openedx-sandbox-seeder.git

For a Tutor devstack, add it to your ``OPENEDX_EXTRA_PIP_REQUIREMENTS`` (or mount it
under ``env/build/openedx/requirements/private.txt`` / as an editable install under
``env/apps/openedx``, like any other extra package), then rebuild/restart.

Usage
*****

Course and library creation only work when run against CMS, that's where those APIs
live. Organizations, users, and role assignments work from either CMS or LMS.

.. code-block:: bash

    # Seed the bundled default fixture
    python manage.py cms seed_sandbox_data

    # Seed a fixture of your own
    python manage.py cms seed_sandbox_data --data-file /path/to/custom.json

    # Delete previously seeded users first, for a clean slate
    python manage.py cms seed_sandbox_data --reset

The command prints a summary (``N created, N skipped, N failed``) and exits non-zero
if anything failed, so it's safe to use in a script.

Writing a fixture
==================

See ``openedx_sandbox_seeder/management/commands/data/sandbox_seed_data.json`` for
the bundled default. The shape is:

.. code-block:: json

    {
      "organizations": [{"name": "Sandbox Org", "short_name": "SandboxX"}],
      "courses": [{"org": "SandboxX", "number": "DemoX", "run": "Demo_Course", "display_name": "Sandbox Demo Course"}],
      "libraries": [{"org": "SandboxX", "slug": "sandbox-library", "title": "Sandbox Demo Library"}],
      "users": [
        {
          "username": "sandbox_course_editor",
          "email": "sandbox_course_editor@example.com",
          "roles": [{"role": "course_editor", "scope": "course-v1:SandboxX+DemoX+Demo_Course"}]
        }
      ]
    }

``roles[].role`` is an openedx-authz role external key (``course_staff``,
``course_admin``, ``course_editor``, ``course_auditor``, ``library_admin``, ...), and
``roles[].scope`` is the matching AuthZ scope key: a course (``course-v1:ORG+NUM+RUN``),
an org-wide glob (``course-v1:ORG+*``), the whole platform (``course-v1:*``), or a
library (``lib:ORG:SLUG``). Seeded users default to password ``edx`` unless a
``password`` field is given.

Getting Started with Development
********************************

Please see the Open edX documentation for `guidance on Python development`_ in this repo.

.. _guidance on Python development: https://docs.openedx.org/en/latest/developers/how-tos/get-ready-for-python-dev.html

Getting Help
************

Documentation
=============

PLACEHOLDER: Start by going through `the documentation`_.  If you need more help see below.

.. _the documentation: https://docs.openedx.org/projects/openedx-sandbox-seeder

(TODO: `Set up documentation <https://openedx.atlassian.net/wiki/spaces/DOC/pages/21627535/Publish+Documentation+on+Read+the+Docs>`_)

More Help
=========

If you're having trouble, we have discussion forums at
https://discuss.openedx.org where you can connect with others in the
community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack workspace`_.

For anything non-trivial, the best path is to open an issue in this
repository with as many details about the issue you are facing as you
can provide.

https://github.com/eduNEXT/openedx-sandbox-seeder/issues

For more information about these options, see the `Getting Help <https://openedx.org/getting-help>`__ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack workspace: https://openedx.slack.com/

License
*******

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see `LICENSE.txt <LICENSE.txt>`_ for details.

Contributing
************

Contributions are very welcome.
Please read `How To Contribute <https://openedx.org/r/how-to-contribute>`_ for details.

This project is currently accepting all types of contributions, bug fixes,
security fixes, maintenance work, or new features.  However, please make sure
to discuss your new feature idea with the maintainers before beginning development
to maximize the chances of your change being accepted.
You can start a conversation by creating a new issue on this repo summarizing
your idea.

The Open edX Code of Conduct
****************************

All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

People
******

The assigned maintainers for this component and other project details may be
found in `Backstage`_. Backstage pulls this data from the ``catalog-info.yaml``
file in this repo.

.. _Backstage: https://backstage.openedx.org/catalog/default/component/openedx-sandbox-seeder

Reporting Security Issues
*************************

Please do not report security issues in public. Please email security@openedx.org.

.. |pypi-badge| image:: https://img.shields.io/pypi/v/openedx-sandbox-seeder.svg
    :target: https://pypi.python.org/pypi/openedx-sandbox-seeder/
    :alt: PyPI

.. |ci-badge| image:: https://github.com/eduNEXT/openedx-sandbox-seeder/actions/workflows/ci.yml/badge.svg?branch=main
    :target: https://github.com/eduNEXT/openedx-sandbox-seeder/actions/workflows/ci.yml
    :alt: CI

.. |codecov-badge| image:: https://codecov.io/github/eduNEXT/openedx-sandbox-seeder/coverage.svg?branch=main
    :target: https://codecov.io/github/eduNEXT/openedx-sandbox-seeder?branch=main
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/openedx-sandbox-seeder/badge/?version=latest
    :target: https://docs.openedx.org/projects/openedx-sandbox-seeder
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/openedx-sandbox-seeder.svg
    :target: https://pypi.python.org/pypi/openedx-sandbox-seeder/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/eduNEXT/openedx-sandbox-seeder.svg
    :target: https://github.com/eduNEXT/openedx-sandbox-seeder/blob/main/LICENSE.txt
    :alt: License

.. TODO: Choose one of the statuses below and remove the other status-badge lines.
.. |status-badge| image:: https://img.shields.io/badge/Status-Experimental-yellow
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Deprecated-orange
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Unsupported-red
