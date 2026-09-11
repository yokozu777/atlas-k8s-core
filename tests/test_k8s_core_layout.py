"""Layout / hygiene smoke tests for atlas-k8s-core (step 0)."""

from __future__ import annotations

import base64
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class K8sCoreHygieneTest(unittest.TestCase):
    def test_license_and_security_exist(self) -> None:
        self.assertTrue((REPO_ROOT / "LICENSE").is_file())
        self.assertTrue((REPO_ROOT / "SECURITY.md").is_file())
        self.assertTrue((REPO_ROOT / ".gitignore").is_file())
        self.assertTrue((REPO_ROOT / ".dockerignore").is_file())

    def test_playbook_exists(self) -> None:
        self.assertTrue((REPO_ROOT / "playbooks" / "cluster_core.yaml").is_file())

    def test_gitignore_covers_inventory_and_workspace(self) -> None:
        text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        for needle in ("inventory.yml", "workspace/", "secrets.yml", "!roles/**/tasks/secrets.yml", "kubeconfig"):
            self.assertIn(needle, text)

    def test_pullsecret_example_is_inert(self) -> None:
        path = REPO_ROOT / "docs" / "examples" / "example_pullsecret.yaml"
        text = path.read_text(encoding="utf-8")
        self.assertIn("registry-pullsecret", text)
        self.assertNotIn("nexuscd", text)
        self.assertNotIn("Welcomeback", text)
        self.assertNotIn("mxhash", text.lower())
        # Extract base64 payload after ".dockerconfigjson:"
        b64 = ""
        for line in text.splitlines():
            if ".dockerconfigjson:" in line:
                b64 = line.split(":", 1)[1].strip()
                break
        self.assertTrue(b64)
        payload = json.loads(base64.b64decode(b64).decode("utf-8"))
        auth = payload["auths"]["registry.example.com"]
        self.assertEqual(auth["username"], "CHANGEME")
        self.assertEqual(auth["password"], "CHANGEME")

    def test_readme_has_no_org_urls(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("mxhash", readme.lower())
        self.assertNotIn("gitea.", readme.lower())
        self.assertIn("SECURITY.md", readme)
        self.assertIn("LICENSE", readme)

    def test_playbook_header_is_orchestrator_neutral(self) -> None:
        text = (REPO_ROOT / "playbooks" / "cluster_core.yaml").read_text(encoding="utf-8")
        self.assertNotIn("clusterctl", text)
        self.assertNotIn("platform.yml", text)
        self.assertNotIn("mxhash", text.lower())

    def test_standalone_entrypoints(self) -> None:
        run_sh = REPO_ROOT / "run.sh"
        self.assertTrue(run_sh.is_file())
        self.assertTrue(run_sh.stat().st_mode & 0o111, "run.sh must be executable")
        self.assertTrue((REPO_ROOT / "inventory-example.yml").is_file())
        self.assertTrue((REPO_ROOT / "group_vars" / "all" / "atlas-k8s-core.yml").is_file())
        self.assertTrue((REPO_ROOT / "group_vars" / "all" / "atlas-k8s-core.secrets.yml").is_file())
        self.assertTrue((REPO_ROOT / "group_vars" / "all").is_dir())
        self.assertFalse((REPO_ROOT / "group_vars" / "all.yml").exists())
        self.assertTrue((REPO_ROOT / "requirements.yml").is_file())
        self.assertTrue((REPO_ROOT / "examples" / "secrets.example.yml").is_file())
        self.assertTrue((REPO_ROOT / "examples" / "hosts.example.yml").is_file())
        self.assertTrue((REPO_ROOT / "host_vars" / "example.yml").is_file())
        catalog = (REPO_ROOT / "group_vars" / "all" / "atlas-k8s-core.yml").read_text(encoding="utf-8")
        secrets_overlay = (REPO_ROOT / "group_vars" / "all" / "atlas-k8s-core.secrets.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("REQUIRED", catalog)
        self.assertIn("OPTIONAL", catalog)
        self.assertNotIn('vip_auth_pass: "CHANGEME"', catalog)
        self.assertIn('vip_auth_pass: "CHANGEME"', secrets_overlay)
        self.assertIn("sync_time_max_offset_seconds:", catalog)
        self.assertIn("k8s_lb_dns_key_name:", catalog)
        self.assertIn("k8s_packages_ubuntu:", catalog)
        self.assertIn("containerd_registry_mirrors:", catalog)
        self.assertIn("dir_name: reg.kyverno.io", catalog)
        self.assertIn('dir_name: reg.kyverno.io, server: "https://ghcr.io"', catalog)
        self.assertIn("dir_name: cr.fluentbit.io", catalog)
        self.assertIn(
            'dir_name: cr.fluentbit.io, server: "https://registry-1.docker.io"', catalog
        )
        self.assertIn("kernel_modules:", catalog)
        self.assertIn("k8s_cluster_domain:", catalog)
        self.assertIn("cluster_workspace_root:", catalog)
        self.assertIn("pkg_repo_base:", catalog)
        self.assertNotIn("use_internal_rpm_apt_repo:", catalog)
        self.assertIn("harbor_host:", catalog)
        self.assertIn("harbor_mirror_base:", catalog)
        self.assertIn("k8s_lb_hosts: k8s_lbs", catalog)
        self.assertIn("k8s_master_hosts: k8s_masters", catalog)
        self.assertIn("k8s_worker_hosts: k8s_workers", catalog)
        self.assertIn("k8s_lb_dns_tf_manage_a_record: false", catalog)
        self.assertIn("k8s_control_plane_master_host:", catalog)
        self.assertIn("k8s_api_cert_sans:", catalog)
        self.assertIn("k8s_admin_home:", catalog)
        self.assertIn("k8s_ca_cert_filename:", catalog)
        self.assertIn("00_ensure_workspace", catalog)
        reqs = (REPO_ROOT / "requirements.yml").read_text(encoding="utf-8")
        self.assertIn("ansible.posix", reqs)
        self.assertIn("community.general", reqs)
        inventory = (REPO_ROOT / "inventory-example.yml").read_text(encoding="utf-8")
        for group in ("k8s_lbs", "k8s_masters", "k8s_workers"):
            self.assertIn(group, inventory)
        self.assertIn("k8s_lb_hosts", inventory)
        run_text = run_sh.read_text(encoding="utf-8")
        self.assertIn("playbooks/cluster_core.yaml", run_text)
        self.assertIn("CLUSTER_WORKSPACE_ROOT", run_text)
        self.assertIn("EXTRA_VARS_FILE", run_text)

    def test_workspace_role_and_catalog(self) -> None:
        catalog = (REPO_ROOT / "group_vars" / "all" / "atlas-k8s-core.yml").read_text(encoding="utf-8")
        self.assertIn("cluster_workspace_root:", catalog)
        self.assertIn("cluster_workspace_parent:", catalog)
        self.assertIn("controller_kubeconfig:", catalog)
        defaults = (
            REPO_ROOT / "roles" / "00_ensure_workspace" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("cluster_workspace_root:", defaults)
        self.assertIn("CLUSTER_WORKSPACE_ROOT", defaults)
        self.assertIn("controller_workspace:", defaults)
        validate = (
            REPO_ROOT / "roles" / "00_ensure_workspace" / "tasks" / "validate.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("Resolve cluster workspace root", validate)
        self.assertIn("Align controller paths under resolved workspace root", validate)
        self.assertIn("CLUSTER_WORKSPACE_PARENT", validate)
        create_dirs = (
            REPO_ROOT / "roles" / "00_ensure_workspace" / "tasks" / "create_dirs.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn(".ansible_facts_cache", create_dirs)
        self.assertIn("controller_workspace", create_dirs)
        self.assertNotIn("provision_tf_state_repo_dir", create_dirs)
        playbook = (REPO_ROOT / "playbooks" / "cluster_core.yaml").read_text(encoding="utf-8")
        self.assertIn("tags: [00_ensure_workspace]", playbook)
        self.assertIn("09_lb_vip_dns", playbook)
        self.assertLess(
            playbook.index("09_lb_vip_dns"),
            playbook.index("tags: 10_lb"),
        )
        self.assertLess(
            playbook.index("00_ensure_workspace"),
            playbook.index("01_validate_vars"),
        )

        # Deep knobs must ship in role defaults (standalone without orchestrator overlay).
        lb_defaults = (REPO_ROOT / "roles" / "10_lb" / "defaults" / "main.yml").read_text(
            encoding="utf-8"
        )
        for needle in (
            "lb_packages_debian:",
            "nginx_stream_module_path:",
            "nginx_worker_connections:",
        ):
            self.assertIn(needle, lb_defaults)
        vip_dns_defaults = (
            REPO_ROOT / "roles" / "09_lb_vip_dns" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("k8s_lb_dns_tf_manage_a_record: false", vip_dns_defaults)
        self.assertIn("provision_dns_server", vip_dns_defaults)
        self.assertTrue(
            (REPO_ROOT / "roles" / "09_lb_vip_dns" / "templates" / "main.tf.j2").is_file()
        )
        vip_dns_tasks = (
            REPO_ROOT / "roles" / "09_lb_vip_dns" / "tasks" / "main.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("terraform apply", vip_dns_tasks)
        self.assertIn("dns_a_record_set", (
            REPO_ROOT / "roles" / "09_lb_vip_dns" / "templates" / "main.tf.j2"
        ).read_text(encoding="utf-8"))
        init_defaults = (
            REPO_ROOT / "roles" / "21_kubeadm_init" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("k8s_api_cert_sans:", init_defaults)
        self.assertIn("k8s_admin_home:", init_defaults)
        hosts_defaults = (
            REPO_ROOT / "roles" / "11_k8s_hosts" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("containerd_registry_mirrors:", hosts_defaults)
        self.assertIn("dir_name: reg.kyverno.io", hosts_defaults)
        self.assertIn('dir_name: reg.kyverno.io, server: "https://ghcr.io"', hosts_defaults)
        self.assertIn("dir_name: cr.fluentbit.io", hosts_defaults)
        self.assertIn(
            'dir_name: cr.fluentbit.io, server: "https://registry-1.docker.io"',
            hosts_defaults,
        )
        sync_defaults = (
            REPO_ROOT / "roles" / "03_sync_time" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("sync_time_max_offset_seconds:", sync_defaults)
        tooling_defaults = (
            REPO_ROOT / "roles" / "00_controller_tooling" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("k8s_ca_cert_filename:", tooling_defaults)
        self.assertNotIn("krang", tooling_defaults.lower())

        validate_core = (
            REPO_ROOT / "roles" / "01_validate_vars" / "tasks" / "vars_cluster_core.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("k8s_api_cert_sans", validate_core)
        self.assertIn("k8s_lb_dns_tf_manage_a_record", validate_core)
        validate_defaults = (
            REPO_ROOT / "roles" / "01_validate_vars" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("k8s_lb_dns_tf_manage_a_record: false", validate_defaults)
        self.assertIn("provision_dns_key_secret", validate_defaults)
        self.assertIn("k8s_lb_dns_tf_workspace:", validate_defaults)

    def test_inventory_group_targeting(self) -> None:
        playbook = (REPO_ROOT / "playbooks" / "cluster_core.yaml").read_text(encoding="utf-8")
        for needle in ("k8s_lb_hosts", "k8s_master_hosts", "k8s_worker_hosts"):
            self.assertIn(needle, playbook)
        # Play hosts must use targeting vars, not bare group names alone.
        self.assertIn("k8s_lb_hosts | default('k8s_lbs')", playbook)
        self.assertIn("k8s_master_hosts | default('k8s_masters')", playbook)
        self.assertIn("k8s_worker_hosts | default('k8s_workers')", playbook)
        self.assertIn("groups.get(k8s_master_hosts", playbook)
        self.assertNotIn("hosts: k8s_lbs\n", playbook)
        self.assertNotIn("hosts: k8s_masters\n", playbook)
        self.assertNotIn("hosts: k8s_workers\n", playbook)

        validate = (
            REPO_ROOT / "roles" / "01_validate_vars" / "tasks" / "inventory_bootstrap.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("groups[k8s_master_hosts]", validate)
        self.assertIn("groups[k8s_lb_hosts]", validate)
        self.assertIn("k8s_worker_hosts in groups", validate)
        defaults = (
            REPO_ROOT / "roles" / "01_validate_vars" / "defaults" / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("k8s_lb_hosts: k8s_lbs", defaults)
        self.assertIn("k8s_master_hosts: k8s_masters", defaults)
        self.assertIn("k8s_worker_hosts: k8s_workers", defaults)

        # No leftover hardcoded groups['k8s_*'] in roles/templates.
        hardcoded = _scan_product_sources_for(
            ("groups['k8s_lbs']", "groups['k8s_masters']", "groups['k8s_workers']"),
            case_sensitive=True,
        )
        # README may mention legacy literal names in docs; scan roles+playbooks only.
        role_hits = [h for h in hardcoded if h.startswith("roles/") or h.startswith("playbooks/")]
        self.assertEqual(role_hits, [], f"hardcoded group keys remain: {role_hits}")

        nginx = (REPO_ROOT / "roles" / "10_lb" / "templates" / "nginx.j2").read_text(
            encoding="utf-8"
        )
        keepalived = (
            REPO_ROOT / "roles" / "10_lb" / "templates" / "keepalived.j2"
        ).read_text(encoding="utf-8")
        self.assertIn("groups[k8s_master_hosts]", nginx)
        self.assertIn("groups[k8s_lb_hosts]", keepalived)
        self.assertIn("keepalived_interface_effective", keepalived)

        lb_tasks = (REPO_ROOT / "roles" / "10_lb" / "tasks" / "main.yaml").read_text(
            encoding="utf-8"
        )
        lb_defaults = (REPO_ROOT / "roles" / "10_lb" / "defaults" / "main.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Gather network facts for Keepalived VRRP interface", lb_tasks)
        self.assertIn("Resolve Keepalived VRRP interface", lb_tasks)
        self.assertIn("ansible_facts['default_ipv4']", lb_tasks)
        self.assertIn("keepalived_interface_effective", lb_tasks)
        self.assertIn("Deploy keepalived configuration", lb_tasks)
        self.assertIn("Restart Keepalived", lb_tasks)
        self.assertIn('keepalived_interface: ""', lb_defaults)

        lb_handlers = (
            REPO_ROOT / "roles" / "10_lb" / "handlers" / "main.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("Restart Keepalived", lb_handlers)

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("k8s_lb_hosts", readme)
        self.assertIn("k8s_master_hosts", readme)
        self.assertIn("k8s_worker_hosts", readme)
        self.assertIn("Targeting var", readme)

    def test_readme_is_standalone_first(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("./run.sh", readme)
        self.assertIn("Quickstart", readme)
        self.assertIn("group_vars/all/atlas-k8s-core.yml", readme)
        self.assertIn("inventory-example.yml", readme)
        self.assertIn("Troubleshooting", readme)
        self.assertIn("Greenfield checklist", readme)
        self.assertIn("Contributing", readme)
        self.assertIn("Project structure", readme)
        self.assertIn("00_ensure_workspace", readme)
        self.assertIn("09_lb_vip_dns", readme)
        self.assertIn("k8s_lb_dns_tf_manage_a_record", readme)
        self.assertIn("atlas-k8s-addons", readme)
        self.assertIn("community.general", readme)
        # Primary operator path must not be an external orchestrator CLI
        self.assertNotIn("./cluster ", readme)
        self.assertNotIn("./cluster\n", readme)
        self.assertNotIn("clusterctl", readme)
        self.assertNotIn("mxhash", readme.lower())
        quick = readme.index("## Quickstart")
        integ = readme.index("## Integrations")
        self.assertLess(quick, integ)
        self.assertIn("Org-specific lab overlays", readme)
        # Section order: product narrative before Integrations / Security / Contributing
        for earlier, later in (
            ("## Greenfield checklist", "## Troubleshooting"),
            ("## Troubleshooting", "## Testing / CI"),
            ("## Testing / CI", "## Project structure"),
            ("## Project structure", "## Integrations"),
            ("## Integrations", "## Security"),
            ("## Security", "## Contributing"),
        ):
            self.assertLess(readme.index(earlier), readme.index(later), f"{earlier} before {later}")
        self.assertIn("./tests/run_ci.sh", readme)
        self.assertIn(".github/workflows/ci.yml", readme)
        self.assertIn("ansible-lint", readme)
    def test_no_org_fingerprint_in_product_sources(self) -> None:
        needles = ("mxhash", "gitea.", "harbor.", "welcomeback", "upload.mxhash")
        hits = _scan_product_sources_for(needles)
        self.assertEqual(hits, [], f"org fingerprint in product sources: {hits}")

        # Orchestrator overlay / legacy paths must not be the product SoT.
        for needle in ("vars-file.yml", "platform.yml", "clusters/<id>", "atlas-clusterctl"):
            overlay_hits = _scan_product_sources_for((needle,), case_sensitive=True)
            self.assertEqual(
                overlay_hits,
                [],
                f"orchestrator path in product sources ({needle}): {overlay_hits}",
            )

        for rel in (
            "roles/09_lb_vip_dns/defaults/main.yml",
            "roles/10_lb/defaults/main.yml",
            "roles/11_k8s_hosts/defaults/main.yml",
            "roles/21_kubeadm_init/defaults/main.yml",
            "roles/03_sync_time/defaults/main.yml",
            "roles/00_ensure_workspace/defaults/main.yml",
        ):
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("Nexus", text, rel)
            self.assertNotIn("vars-file", text, rel)
            self.assertNotIn("clusterctl", text, rel)


_PRODUCT_SCAN_ROOTS = (
    REPO_ROOT / "roles",
    REPO_ROOT / "playbooks",
    REPO_ROOT / "group_vars",
    REPO_ROOT / "examples",
    REPO_ROOT / "host_vars",
    REPO_ROOT / "filter_plugins",
    REPO_ROOT / "inventory-example.yml",
    REPO_ROOT / "run.sh",
    REPO_ROOT / "ansible.cfg",
    REPO_ROOT / "requirements.yml",
    REPO_ROOT / "README.md",
)
_PRODUCT_SCAN_SUFFIXES = {".yml", ".yaml", ".j2", ".sh", ".cfg", ".md", ".py"}


def _scan_product_sources_for(
    needles: tuple[str, ...],
    *,
    case_sensitive: bool = False,
) -> list[str]:
    hits: list[str] = []
    for root in _PRODUCT_SCAN_ROOTS:
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix.lower() not in _PRODUCT_SCAN_SUFFIXES and path.name != "run.sh":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            haystack = text if case_sensitive else text.lower()
            for needle in needles:
                probe = needle if case_sensitive else needle.lower()
                if probe in haystack:
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{needle}")
    return hits


class K8sApiserverOidcLayoutTest(unittest.TestCase):
    def test_kubeadm_init_does_not_embed_oidc_extra_args(self) -> None:
        tmpl = (
            REPO_ROOT / "roles" / "21_kubeadm_init" / "templates" / "kubeadm.yaml.j2"
        ).read_text(encoding="utf-8")
        self.assertNotIn("oidc-issuer-url", tmpl)
        self.assertNotIn("kube_apiserver_oidc_enabled", tmpl)
        catalog = (REPO_ROOT / "group_vars" / "all" / "atlas-k8s-core.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("kube_apiserver_oidc_enabled", catalog)
        playbook = (REPO_ROOT / "playbooks" / "cluster_core.yaml").read_text(encoding="utf-8")
        self.assertNotIn("27_apiserver_oidc", playbook)
        self.assertFalse((REPO_ROOT / "roles" / "27_apiserver_oidc").is_dir())
        init_tasks = (REPO_ROOT / "roles" / "21_kubeadm_init" / "tasks" / "main.yaml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("27_apiserver_oidc", init_tasks)
        self.assertNotIn("install_oidc_ca.yaml", init_tasks)


class PublishHygieneTest(unittest.TestCase):
    """Contracts that must hold before publishing the repo."""

    def test_license_and_security_files(self) -> None:
        self.assertTrue((REPO_ROOT / "LICENSE").is_file())
        self.assertTrue((REPO_ROOT / "SECURITY.md").is_file())
        self.assertTrue((REPO_ROOT / "README.md").is_file())
        self.assertTrue((REPO_ROOT / ".ansible-lint").is_file())
        self.assertTrue((REPO_ROOT / ".github" / "workflows" / "ci.yml").is_file())
        self.assertTrue((REPO_ROOT / "requirements-dev.txt").is_file())

    def test_ci_entrypoints_executable(self) -> None:
        run_sh = REPO_ROOT / "run.sh"
        run_ci = REPO_ROOT / "tests" / "run_ci.sh"
        domain_check = REPO_ROOT / "scripts" / "check-no-hardcoded-domains.sh"
        self.assertTrue(run_sh.is_file())
        self.assertTrue(run_sh.stat().st_mode & 0o111, "run.sh must be executable")
        self.assertTrue(run_ci.is_file())
        self.assertTrue(run_ci.stat().st_mode & 0o111, "tests/run_ci.sh must be executable")
        self.assertTrue(domain_check.is_file())
        self.assertTrue(
            domain_check.stat().st_mode & 0o111,
            "scripts/check-no-hardcoded-domains.sh must be executable",
        )

    def test_no_obvious_secret_material_in_product_sources(self) -> None:
        needles = ("Welcomeback", "BEGIN OPENSSH PRIVATE", "BEGIN RSA PRIVATE", "AKIA", "gldt-")
        hits = _scan_product_sources_for(needles, case_sensitive=True)
        self.assertEqual(hits, [], f"secret-like material found: {hits}")

    def test_readme_mentions_ci_runner(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("./tests/run_ci.sh", readme)
        self.assertIn("Testing / CI", readme)
        self.assertIn(".github/workflows/ci.yml", readme)
        self.assertIn("ansible-lint --profile min", readme)

    def test_upgrade_roles_clear_dnf_versionlock_by_package_name(self) -> None:
        # Locks pin the installed NEVRA; deleting target version leaves the old lock.
        for role in (
            "25_kubeadm_upgrade_control_plane",
            "26_kubeadm_upgrade_workers",
        ):
            tasks = (REPO_ROOT / "roles" / role / "tasks" / "main.yaml").read_text(
                encoding="utf-8"
            )
            self.assertIn("dnf versionlock delete", tasks, role)
            self.assertIn("- kubelet\n", tasks, role)
            self.assertIn("- kubeadm\n", tasks, role)
            self.assertIn("- kubectl\n", tasks, role)
            self.assertNotIn(
                'dnf versionlock delete {{ item }} || true\n          loop:\n            - "kubelet-{{ k8s_version_oracle }}"',
                tasks,
                role,
            )


class RegistryMirrorFilterTest(unittest.TestCase):
    def _endpoint(self, item: dict) -> str:
        import importlib.util

        path = REPO_ROOT / "filter_plugins" / "registry_mirror.py"
        spec = importlib.util.spec_from_file_location("k8s_registry_mirror", path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        return mod.FilterModule().containerd_mirror_endpoint(item, "registry.example.com")

    def test_fluentbit_vanity_shares_docker_vhost(self) -> None:
        self.assertEqual(
            self._endpoint(
                {
                    "dir_name": "cr.fluentbit.io",
                    "server": "https://registry-1.docker.io",
                    "mirror_path": "docker.io",
                }
            ),
            "https://docker-io.registry.example.com",
        )

    def test_kyverno_vanity_shares_ghcr_vhost(self) -> None:
        self.assertEqual(
            self._endpoint(
                {
                    "dir_name": "reg.kyverno.io",
                    "server": "https://ghcr.io",
                    "mirror_path": "ghcr.io",
                }
            ),
            "https://ghcr-io.registry.example.com",
        )

    def test_docker_hub_keeps_dir_name_slug(self) -> None:
        self.assertEqual(
            self._endpoint(
                {
                    "dir_name": "docker.io",
                    "server": "https://registry-1.docker.io",
                    "mirror_path": "docker-hub",
                }
            ),
            "https://docker-io.registry.example.com",
        )


if __name__ == "__main__":
    unittest.main()
