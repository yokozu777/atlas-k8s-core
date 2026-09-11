# Changelog

## [Unreleased]

### Fixed

- `10_lb`: resolve Keepalived VRRP interface per host — use configured
  `keepalived_interface` only when it exists on the node, otherwise
  `ansible_facts.default_ipv4.interface` (mixed-OS `ens18` vs `eth0`). Empty
  `keepalived_interface` is the default. Role runs `setup` (`network` subset)
  before resolve so tag-split (`--tags 10_lb`) still has facts when play
  gather_facts is skipped and `02_gather_facts` only collected distribution.
- `10_lb`: restart Keepalived on conf change (separate nginx / keepalived
  template tasks + handlers), not only via final `state=started`.

### Changed (pkg repos — Phase 4)

- Dropped `use_internal_rpm_apt_repo` for package URI baking on role `11_k8s_hosts`.
- Resolve URIs with `pkg_repo_uri`: `pkg_repo_base` → `pkg_repo_nginx_ingress_domain`
  → public; prefer foundation catalog drop-ins when present
  (`k8s-ubuntu-<ver>`, `ubuntu-containerd` / `debian-containerd`).

### Changed (pkg repos — Phase 6)

- No further client path changes; covered by foundation publish/grep gates.
