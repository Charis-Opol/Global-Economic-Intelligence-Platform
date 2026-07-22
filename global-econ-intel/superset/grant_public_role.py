"""
Grants the `Public` role (GUEST_ROLE_NAME in superset_config.py) the
permissions embedded guest sessions actually need, beyond what `superset
init` sets up on its own.

Run once after `superset init` (see docker-compose.yml's superset-init
service) - idempotent, safe to run on every startup.

`superset init`'s own role sync (`SupersetSecurityManager.sync_role_definitions`)
populates Admin/Alpha/Gamma/sql_lab, but leaves `Public` with whatever the
dashboard/dataset import granted directly (dashboard read + per-dataset
`datasource_access`, from `superset import-assets`). That's not enough:
the `@superset-ui/embedded-sdk` iframe's own bootstrap code calls
`GET /api/v1/me/roles/` (and other `/api/v1/*` reads) as a guest user before
it renders anything, and 403s there surface as an opaque "Something went
wrong with embedded authentication" in the iframe - no dashboard-specific
error, so it's easy to mistake for the dashboard/uuid setup being wrong
instead of a role permission gap.
"""
from __future__ import annotations

from superset.app import create_app

# (permission, view/resource name) - the minimum an anonymous guest session
# needs to load an embedded dashboard end to end, found by tracing which
# `/api/v1/*` calls the embedded bundle itself makes before it draws anything
# and matching each 403 to the FAB permission-view it required.
REQUIRED_PERMISSIONS = [
    ("can_read", "CurrentUserRestApi"),
    ("can_read", "Chart"),
    ("can_read", "CssTemplate"),
    ("can_read", "Annotation"),
    ("can_read", "Log"),
    ("can_read", "Explore"),
    ("menu_access", "Dashboards"),
]


def main() -> None:
    app = create_app()
    with app.app_context():
        from superset.extensions import db

        sm = app.appbuilder.sm
        public = sm.find_role(app.config["GUEST_ROLE_NAME"])
        if public is None:
            print(f"No '{app.config['GUEST_ROLE_NAME']}' role found - skipping.")
            return

        # `ab_permission_view_role`'s sequence has been observed out of sync
        # with its actual max id after `superset init`'s bulk role-permission
        # sync - a plain add_permission_role() insert can collide with an
        # existing row and silently no-op the rest of this script's grants.
        # Realigning it first is a no-op when it's already correct.
        db.session.execute(
            db.text(
                "SELECT setval('ab_permission_view_role_id_seq', "
                "(SELECT COALESCE(MAX(id), 1) FROM ab_permission_view_role))"
            )
        )
        db.session.commit()

        for perm, view in REQUIRED_PERMISSIONS:
            pv = sm.find_permission_view_menu(perm, view)
            if pv is None:
                print(f"skip (no such permission-view): {perm} on {view}")
                continue
            if pv in public.permissions:
                print(f"already granted: {perm} on {view}")
                continue
            sm.add_permission_role(public, pv)
            db.session.commit()
            print(f"granted: {perm} on {view}")


if __name__ == "__main__":
    main()
