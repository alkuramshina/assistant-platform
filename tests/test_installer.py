from __future__ import annotations

import tarfile
import unittest

from installer import install


class InstallerTest(unittest.TestCase):
    def test_package_contains_runtime_app_files(self) -> None:
        package = install.package_app()
        try:
            with tarfile.open(package, "r:gz") as archive:
                names = set(archive.getnames())
        finally:
            package.unlink(missing_ok=True)

        self.assertIn("console/api.py", names)
        self.assertIn("console/static/index.html", names)
        self.assertIn("docker/entrypoint.sh", names)
        self.assertIn("docker/sitecustomize.py", names)
        self.assertIn("Dockerfile", names)
        self.assertIn("docs/PROJECT_SUMMARY.md", names)

    def test_missing_prereqs_includes_compose_and_network(self) -> None:
        missing = install.missing_prereqs(
            {
                "docker": "ok",
                "compose": "missing",
                "network": "unknown",
            }
        )

        self.assertEqual(missing, ["Docker Compose", "outbound network"])


if __name__ == "__main__":
    unittest.main()
