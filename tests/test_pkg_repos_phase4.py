"""Phase 4: pkg_repo_uri helper (no use_internal_rpm_apt_repo)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FILTER = REPO_ROOT / "filter_plugins" / "pkg_repo.py"
HOSTS = REPO_ROOT / "roles" / "11_k8s_hosts" / "tasks" / "main.yaml"
README = REPO_ROOT / "README.md"


def _load() -> object:
    spec = importlib.util.spec_from_file_location("pkg_repo", FILTER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class PkgReposPhase4K8sTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load()

    def test_base_wins(self) -> None:
        uri = self.mod.pkg_repo_uri(
            "k8s-ubuntu-1.36",
            "https://nexus.example/repository",
            "repo.example.com",
            [],
        )
        self.assertEqual(uri, "https://nexus.example/repository/k8s-ubuntu-1.36")

    def test_nginx_slug_host(self) -> None:
        uri = self.mod.pkg_repo_uri("k8s-ubuntu-1.36", "", "repo.example.com", [])
        self.assertEqual(uri, "https://k8s-ubuntu-1-36.repo.example.com")

    def test_public_k8s_patterns(self) -> None:
        self.assertEqual(
            self.mod.pkg_repo_uri("k8s-ubuntu-1.36", "", "", []),
            "https://pkgs.k8s.io/core:/stable:/v1.36/deb/",
        )
        self.assertEqual(
            self.mod.pkg_repo_uri("k8s-1.36", "", "", []),
            "https://pkgs.k8s.io/core:/stable:/v1.36/rpm/",
        )

    def test_hosts_role_uses_pkg_repo_uri_not_mode_enum(self) -> None:
        text = HOSTS.read_text(encoding="utf-8")
        self.assertIn("pkg_repo_uri", text)
        self.assertNotIn("use_internal_rpm_apt_repo", text)
        self.assertIn("k8s-ubuntu-{{ k8s_apt_repo_version }}", text)
        self.assertIn("ubuntu-containerd", text)
        self.assertIn("debian-containerd", text)

    def test_readme_dropped_mode_enum(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertNotIn("use_internal_rpm_apt_repo", readme)
        self.assertIn("pkg_repo_base", readme)
