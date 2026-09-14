"""Django management command to seed an Open edX sandbox with deterministic test data.

Reads a JSON fixture describing organizations, courses, libraries, users, and authz
role assignments, and creates them idempotently (get_or_create), so the command is
safe to run repeatedly against a Sandbox.

Course and library creation only work when run against CMS (Studio), since that's
where those APIs live. Organizations, users, and role assignments work from either
CMS or LMS.

Example usage:
    python manage.py cms seed_sandbox_data
    python manage.py cms seed_sandbox_data --data-file /path/to/custom.json
    python manage.py cms seed_sandbox_data --reset
"""

import json
import logging
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_authz.api.users import assign_role_to_user_in_scope
from openedx_authz.engine.enforcer import AuthzEnforcer
from organizations.api import add_organization, get_organizations
from organizations.models import Organization

log = logging.getLogger(__name__)

DEFAULT_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "sandbox_seed_data.json")
DEFAULT_PASSWORD = "edx"
SEEDER_USERNAME = "sandbox_seeder_bot"


class Command(BaseCommand):
    """Seed an Open edX sandbox with orgs, courses, libraries, users, and authz role assignments."""

    help = "Seed the Sandbox with orgs, courses, libraries, users, and authz role assignments from a JSON fixture."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--data-file",
            type=str,
            default=None,
            help="Path to the JSON seed data file (default: bundled sandbox_seed_data.json).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously seeded users (identified by username) before seeding.",
        )

    def handle(self, *args, **options):
        data_file = options["data_file"] or DEFAULT_DATA_FILE
        with open(data_file, encoding="utf-8") as fh:
            seed_data = json.load(fh)

        user_model = get_user_model()
        usernames = [user["username"] for user in seed_data.get("users", [])]

        if options["reset"]:
            self._delete_course_creator_rows(usernames)
            deleted, _ = user_model.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"Removed {deleted} previously seeded record(s)."))

        counts = {"created": 0, "skipped": 0, "failed": 0}
        self._seed_organizations(seed_data.get("organizations", []), counts)
        self._seed_courses(seed_data.get("courses", []), counts)
        self._seed_libraries(seed_data.get("libraries", []), counts)
        self._seed_users(seed_data.get("users", []), user_model, counts)

        AuthzEnforcer.get_enforcer().load_policy()

        summary = "Seeding complete: {created} created, {skipped} skipped, {failed} failed.".format(**counts)
        if counts["failed"]:
            self.stdout.write(self.style.ERROR(summary))
            raise CommandError(f"{counts['failed']} seed item(s) failed, see logs above for details.")
        self.stdout.write(self.style.SUCCESS(summary))

    def _delete_course_creator_rows(self, usernames):
        """Delete CourseCreator rows for these users before deleting the users themselves.

        Works around a recursion bug in edx-platform: CourseCreator has a post_init signal
        that computes all_organizations, and when Django's delete collector cascades from
        User into CourseCreator to delete it, that signal ends up in infinite recursion
        (RecursionError) while building the cascade's subquery. Deleting CourseCreator rows
        directly first, with a plain filter (not part of a cascade), avoids the collector
        ever needing to touch this table.
        """
        # edx-platform (CMS) only, not installed when linting this package on its own.
        try:
            from cms.djangoapps.course_creators.models import CourseCreator  # pylint: disable=import-outside-toplevel
        except ImportError:
            return
        CourseCreator.objects.filter(user__username__in=usernames).delete()

    def _seed_organizations(self, organizations, counts):
        """Create any organization from the fixture that doesn't already exist, tallying counts."""
        existing = {org["short_name"] for org in get_organizations()}
        for org in organizations:
            if org["short_name"] in existing:
                counts["skipped"] += 1
                continue
            try:
                add_organization(org)
                counts["created"] += 1
            # One bad organization shouldn't stop the rest of the fixture from seeding.
            except Exception:  # pylint: disable=broad-exception-caught
                log.exception("Failed to create organization %s", org.get("short_name"))
                counts["failed"] += 1

    def _ensure_profile(self, user):
        """Create the UserProfile row a user needs for course enrollment, if it's missing."""
        # edx-platform only, not installed when linting this package on its own.
        from common.djangoapps.student.models import UserProfile  # pylint: disable=import-error,import-outside-toplevel

        UserProfile.objects.get_or_create(user=user, defaults={"name": user.username})

    def _get_seeder_user(self, user_model):
        """Get or create the technical user that owns any course created by this command."""
        user, was_created = user_model.objects.get_or_create(
            username=SEEDER_USERNAME,
            defaults={"email": f"{SEEDER_USERNAME}@example.com", "is_staff": True, "is_superuser": True},
        )
        if was_created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            self._ensure_profile(user)
        return user

    def _seed_courses(self, courses, counts):
        """Create any course from the fixture that doesn't already exist, tallying counts."""
        if not courses:
            return
        # edx-platform (CMS) only, not installed when linting this package on its own.
        # pylint: disable=import-outside-toplevel
        try:
            from cms.djangoapps.contentstore.views.course import create_new_course
            from xmodule.modulestore.django import modulestore
            from xmodule.modulestore.exceptions import DuplicateCourseError
        except ImportError:
            log.exception("Course creation is only available when running under CMS.")
            counts["failed"] += len(courses)
            return
        # pylint: enable=import-outside-toplevel

        user_model = get_user_model()
        seeder = self._get_seeder_user(user_model)
        store = modulestore()
        for course in courses:
            course_key = store.make_course_key(course["org"], course["number"], course["run"])
            if store.has_course(course_key, ignore_case=True):
                counts["skipped"] += 1
                continue
            try:
                create_new_course(
                    seeder,
                    course["org"],
                    course["number"],
                    course["run"],
                    {"display_name": course.get("display_name", course["number"])},
                )
                counts["created"] += 1
            except DuplicateCourseError:
                counts["skipped"] += 1
            # One bad course shouldn't stop the rest of the fixture from seeding.
            except Exception:  # pylint: disable=broad-exception-caught
                log.exception("Failed to create course %s", course_key)
                counts["failed"] += 1

    def _seed_libraries(self, libraries, counts):
        """Create any content library from the fixture that doesn't already exist, tallying counts."""
        if not libraries:
            return
        # edx-platform only, not installed when linting this package on its own.
        # pylint: disable=import-error,import-outside-toplevel
        from openedx.core.djangoapps.content_libraries import api as lib_api
        from openedx.core.djangoapps.content_libraries.models import ContentLibrary

        # pylint: enable=import-error,import-outside-toplevel

        for library in libraries:
            library_key = LibraryLocatorV2(org=library["org"], slug=library["slug"])
            if ContentLibrary.objects.filter(org__short_name=library["org"], slug=library["slug"]).exists():
                counts["skipped"] += 1
                continue
            try:
                org = Organization.objects.get(short_name=library["org"])
                lib_api.create_library(org, library["slug"], library.get("title", library["slug"]))
                counts["created"] += 1
            # One bad library shouldn't stop the rest of the fixture from seeding.
            except Exception:  # pylint: disable=broad-exception-caught
                log.exception("Failed to create library %s", library_key)
                counts["failed"] += 1

    def _seed_users(self, users, user_model, counts):
        """Create/update each user from the fixture and assign their roles, tallying counts."""
        for user_data in users:
            username = user_data["username"]
            user, was_created = user_model.objects.get_or_create(
                username=username,
                defaults={"email": user_data.get("email", f"{username}@example.com")},
            )
            if was_created:
                user.set_password(user_data.get("password", DEFAULT_PASSWORD))
                user.is_staff = user_data.get("is_staff", False)
                user.is_superuser = user_data.get("is_superuser", False)
                user.save()
                self._ensure_profile(user)
                counts["created"] += 1
            else:
                counts["skipped"] += 1

            for assignment in user_data.get("roles", []):
                try:
                    assign_role_to_user_in_scope(username, assignment["role"], assignment["scope"])
                # One bad role assignment shouldn't stop the rest of the fixture from seeding.
                except Exception:  # pylint: disable=broad-exception-caught
                    log.exception(
                        "Failed to assign role %s to %s in scope %s",
                        assignment["role"],
                        username,
                        assignment["scope"],
                    )
                    counts["failed"] += 1
