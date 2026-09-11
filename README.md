# atlas-k8s-core

Ansible playbooks for Kubernetes **control-plane bootstrap**: Keepalived/Nginx L4 VIP,
node prep (containerd / kubeadm packages), kubeadm init/join, and admin kubeconfig fetch.

**Canonical playbook:** `playbooks/cluster_core.yaml`  
**Runner:** `./run.sh`  
**Vars catalog:** `group_vars/all/atlas-k8s-core.yml`  
**Secrets overlay:** `group_vars/all/atlas-k8s-core.secrets.yml` (prefer Ansible Vault)  
**License:** Apache-2.0 (see `LICENSE`)

CNI (Calico), Helm bootstrap, and platform charts live in sibling **atlas-k8s-addons** — not in this repository.

```
  kubectl / clients
         |
         v
  https://kubelb.<dns>:6443   (API VIP)
         |
         +-----> k8s_lbs       Keepalived + Nginx stream --> masters:6443
         +-----> k8s_masters   kubeadm control plane
         +-----> k8s_workers   kubeadm workers (group may be empty)
```

Role pipeline:

```
  ensure_workspace --> controller_tooling --> validate --> facts/time
         |
         v
  09_lb_vip_dns (optional TF) --> 10_lb --> 11_k8s_hosts --> cluster_state
         |
         v
  kubeadm_init --> join_token --> fetch_kubeconfig --> join_masters/workers
         |
         v
  (optional upgrades 25/26)
```

After core succeeds, install CNI/Helm via **atlas-k8s-addons** before expecting Pod networking / Ready nodes.

## Compatibility

Targeted at:
- **Ubuntu** / **Debian** (kubeadm apt packages)
- **Oracle Linux** / RHEL-family (kubeadm rpm packages)

Inventory contract (required groups — override names via vars if needed):

| Group (default) | Targeting var | Roles |
|-----------------|---------------|-------|
| `k8s_lbs` | `k8s_lb_hosts` | `10_lb` |
| `k8s_masters` | `k8s_master_hosts` | `11_k8s_hosts`, `21_kubeadm_init`, joins, upgrades |
| `k8s_workers` | `k8s_worker_hosts` | `11_k8s_hosts`, `24_join_workers`, `12_workers_kernel_rbd` |
| (localhost) | — | `09_lb_vip_dns` (optional VIP DNS via Terraform) |

Optional parent group `k8s` may nest the three groups (see `inventory-example.yml`).

- `k8s_lbs` ≥ 1 (lab: 2 for Keepalived VIP)
- `k8s_masters` ≥ 1 (lab: 3 for HA)
- `k8s_workers` group **must exist** (may be empty; lab: ≥ 1)

To use different inventory group names (single group each):

```yaml
# group_vars/all/atlas-k8s-core.yml
k8s_lb_hosts: my_k8s_lbs
k8s_master_hosts: my_k8s_masters
k8s_worker_hosts: my_k8s_workers
```

Every host should set `ansible_host` and a stable **`hostname:`** (prefer FQDN). Node names used by kubeadm default to that `hostname`.

## Quickstart

### Prerequisites

- Ansible 2.14+ recommended
- `ansible-galaxy collection install -r requirements.yml` (`ansible.posix`, `community.general`)
- SSH access to targets (Python 3 on targets)
- Replace every `CHANGEME` and set VIP / CA URL in `group_vars/all/atlas-k8s-core.yml` (prefer Ansible Vault)
- Nodes need package access for kubeadm/containerd (public pkgs.k8s.io when `pkg_repo_base` and `pkg_repo_nginx_ingress_domain` are empty)
- Controller can reach `pki_ca_url` (HTTPS) for CA material used by controller tooling
- DNS or `/etc/hosts` so `{{ k8s_lb_hostname }}.{{ dns_domain_suffix }}` resolves to `vip_address` from masters/workers/clients
- OS bootstrap (users, base packages, firewall policy) is **out of scope** — provide a reachable Linux baseline first

### Clone

```bash
git clone <atlas-k8s-core-url>
cd atlas-k8s-core
ansible-galaxy collection install -r requirements.yml
```

### Inventory

```bash
cp inventory-example.yml inventory.yml
vi inventory.yml
```

Set `ansible_host` and **`hostname:`** on every node (prefer FQDN).

### Variables

**SoT:** `group_vars/all/atlas-k8s-core.yml` — **REQUIRED** (identity, workspace, VIP, kube versions, CA/mirror placeholders, cert SANs) and **OPTIONAL** (registry/repo modes, NTP, Keepalived tunables).  
Deep knobs live in `roles/*/defaults/main.yml` when not listed in `group_vars/all/atlas-k8s-core.yml` (LB packages/nginx, containerd mirrors, sync_time thresholds).

Minimum settings for a real deploy:

```yaml
dns_domain_suffix: example.com
cluster_domain: k8s.example.com          # must match CLUSTER_WORKSPACE_ID
k8s_cluster_name: atlas
vip_address: "192.168.1.210"
vip_auth_pass: "CHANGEME"                # Keepalived PASS — max 8 characters
keepalived_interface: ""               # "" = auto default IPv4 NIC (ens18 vs eth0)
pki_ca_url: "https://ca.example.com:8443/roots.pem"
k8s_apt_repo_version: "1.36"
k8s_version_ubuntu: "1.36.2-2.1"
k8s_version_oracle: "1.36.2"
```

`cluster_workspace_id` must equal `k8s_cluster_domain` (validate contract). Prefer letting `./run.sh` set absolute `CLUSTER_WORKSPACE_*` paths.

Optional vault overlay:

```bash
cp examples/secrets.example.yml ~/k8s-core-secrets.yml
# edit, optionally: ansible-vault encrypt ~/k8s-core-secrets.yml
EXTRA_VARS_FILE=~/k8s-core-secrets.yml ./run.sh
```

### Run

```bash
./run.sh --tags 01_validate_vars   # contract check (localhost)
./run.sh                           # full core stack
```

Recommended staged tags (same order as the playbook). Co-tag `04_cluster_state` with
each lifecycle gate so `k8s_needs_*` facts exist in the same `ansible-playbook` process
(tag-split runs do not keep in-memory `set_fact`):

```bash
./run.sh --tags 00_controller_tooling
./run.sh --tags 03_sync_time
./run.sh --tags 09_lb_vip_dns
./run.sh --tags 10_lb
./run.sh --tags 11_k8s_hosts
./run.sh --tags 04_cluster_state,21_kubeadm_init
./run.sh --tags 04_cluster_state,22_cluster_join_token
./run.sh --tags 29_fetch_kubeconfig
./run.sh --tags 04_cluster_state,23_join_masters
./run.sh --tags 04_cluster_state,24_join_workers,12_workers_kernel_rbd
```

Optional upgrades (only when package versions change and `k8s_needs_upgrade` is true):

```bash
./run.sh --tags 04_cluster_state,25_kubeadm_upgrade_control_plane
./run.sh --tags 04_cluster_state,26_kubeadm_upgrade_workers
```

Or manually:

```bash
ansible-playbook -i inventory.yml playbooks/cluster_core.yaml
```

### `./run.sh` environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `INVENTORY` | `inventory.yml` or `inventory-example.yml` | Inventory path |
| `PLAYBOOK` | `playbooks/cluster_core.yaml` | Playbook path |
| `EXTRA_VARS_FILE` | — | Optional `-e @file` (vaulted secrets) |
| `SSH_KEY` / `ANSIBLE_PRIVATE_KEY_FILE` | `~/.ssh/id_ed25519` or `id_rsa` | SSH private key |
| `CLUSTER_WORKSPACE_ID` | `k8s.example.com` | Workspace dir name (must match `k8s_cluster_domain`) |
| `CLUSTER_WORKSPACE_PARENT` | `./workspace` (absolute via runner) | Parent of workspace |
| `CLUSTER_WORKSPACE_ROOT` | `<parent>/<id>` | Controller workspace (kubeconfig, manifests, stubs) |
| `ANSIBLE_CONFIG` | `./ansible.cfg` | Ansible config |

All extra CLI arguments are forwarded to `ansible-playbook`.

## Architecture (role order)

`playbooks/cluster_core.yaml`:

```
  tooling --> validate --> facts/time --> 09_lb_vip_dns --> lb --> packages
         |
         v
  cluster_state --> kubeadm_init --> join_token --> kubeconfig
         |
         v
  join_masters --> join_workers --> (optional upgrades)
```

1. **00_ensure_workspace** (localhost, tag `always`) — controller workspace directories  
2. **00_controller_tooling** — local tooling / CA on the Ansible controller  
3. **01_validate_vars** — inventory groups + required vars + workspace path contract  
4. **02_gather_facts** / **03_sync_time** — all LB/master/worker nodes  
5. **09_lb_vip_dns** — optional Terraform RFC2136 A for `k8s_lb_hostname` → `vip_address` (off by default)  
6. **10_lb** — Keepalived VIP + Nginx stream to masters  
7. **11_k8s_hosts** — containerd / kube packages on masters + workers  
8. **04_cluster_state** + **21_kubeadm_init** — probe then first master (`groups[k8s_master_hosts][0]`)  
9. **04_cluster_state** + **22_cluster_join_token** — probe then join material on controller  
10. **29_fetch_kubeconfig** — admin kubeconfig on controller  
11. **04_cluster_state** + **23_join_masters** — probe then remaining masters (`serial: 1`)
12. **04_cluster_state** + **24_join_workers** / **12_workers_kernel_rbd** — probe then workers + optional RBD
13. **04_cluster_state** + **25** / **26** — probe then optional kubeadm upgrades (`k8s_needs_upgrade`)

Admin kubeconfig on the controller (default):

`$CLUSTER_WORKSPACE_ROOT/controller-state/kubeconfig/admin.conf`

## Identity, VIP, and networking

| Variable | Default (catalog) | Purpose |
|----------|-------------------|---------|
| `dns_domain_suffix` | `example.com` | DNS suffix for LB hostname |
| `cluster_domain` / `k8s_cluster_domain` | `k8s.example.com` | Cluster identity + workspace id |
| `k8s_lb_hostname` | `kubelb` | Short name in `control_plane_endpoint` |
| `k8s_api_port` | `6443` | API port behind VIP |
| `control_plane_endpoint` | `kubelb.example.com:6443` | kubeadm controlPlaneEndpoint |
| `vip_address` | `192.168.1.210` | Keepalived virtual IP |
| `vip_auth_pass` | `CHANGEME` | VRRP auth (≤ 8 chars) |
| `keepalived_interface` | `""` (auto) | VRRP NIC; empty → `ansible_default_ipv4.interface` per LB |
| `k8s_lb_dns_tf_manage_a_record` | `false` | `true` → Terraform creates VIP apex A (RFC2136); `false` → BIND / manual DNS |
| `pod_subnet` | `172.16.0.0/16` | kubeadm pod CIDR (CNI later) |
| `service_subnet` | `10.0.0.0/12` | kubeadm service CIDR |

`nexus_host` / `nexus_base_url` are **placeholder strings** required by validate even when package URI knobs are empty and `use_internal_docker_registry: none` (standalone public upstreams).

When `k8s_lb_dns_tf_manage_a_record: true`, set TSIG via `k8s_lb_dns_*` or reuse `provision_dns_*` / `dns_server_ip` (see `roles/09_lb_vip_dns/defaults`). Do not also let BIND invent the same hostname.

## Controller workspace (00)

Role **00_ensure_workspace** creates dirs under `cluster_workspace_root` (kubeconfig, manifests, certs, staging, layout stubs). Prefer absolute paths from `./run.sh` so validate path-prefix checks succeed. The role re-resolves `CLUSTER_WORKSPACE_*` from the environment and realigns `controller_*` paths under the active root.

| Variable | Purpose |
|----------|---------|
| `cluster_workspace_id` | Must equal `k8s_cluster_domain` |
| `cluster_workspace_parent` | Parent directory (default `./workspace`) |
| `cluster_workspace_root` | Full workspace root |
| `controller_kubeconfig` | Fetched admin kubeconfig path |
| `k8s_api_cert_sans` | kubeadm API cert SANs (VIP + LB DNS) |
| `k8s_admin_home` | Node home for optional break-glass kubeconfig / join temp files |

Deep knobs (LB packages, nginx stream, containerd mirrors, chrony thresholds) live in `roles/*/defaults/main.yml` — override via group_vars or `EXTRA_VARS_FILE` when needed.

## LB VIP DNS (09)

Optional role **09_lb_vip_dns** (tag `09_lb_vip_dns`) creates the apex A record
`{{ k8s_lb_hostname }}.{{ dns_domain_suffix }}` → `vip_address` with Terraform
(`hashicorp/dns` / RFC2136) when `k8s_lb_dns_tf_manage_a_record: true`. Default is
`false` so BIND (or manual DNS) remains the owner. Requires `terraform` on the
controller and a non-`CHANGEME` TSIG secret. State lives under
`k8s_lb_dns_tf_workspace` (default: `controller_staging_dir/lb-vip-dns`).

## Load balancer (10)

Keepalived owns `vip_address`; Nginx stream proxies `{{ k8s_api_port }}` to all hosts in `groups[k8s_master_hosts]`. Leave `keepalived_interface` empty to auto-pick `ansible_default_ipv4.interface` on each LB (mixed-OS: `ens18` vs `eth0`); set it only for multi-NIC overrides. Lab sizing typically uses two LBs for VRRP.
`{{ k8s_lb_hostname }}` must resolve to `vip_address` before kubeadm join-token generation (role 09, BIND, or `/etc/hosts`).

## Node packages (11)

Installs containerd and Kubernetes packages on masters and workers according to distro (`k8s_version_ubuntu` / `k8s_version_oracle`, `k8s_apt_repo_version`). Prefers foundation catalog drop-ins when present; otherwise bakes URIs via `pkg_repo_base` → `pkg_repo_nginx_ingress_domain` → public. Registry mirror mode defaults to `use_internal_docker_registry: none`.

## Init, join, kubeconfig (21–29)

| Stage | Tag | Notes |
|-------|-----|-------|
| Init first master | `21_kubeadm_init` | Idempotent if admin.conf already exists (unless forced) |
| Join token | `22_cluster_join_token` | Controller-side join command material |
| Fetch kubeconfig | `29_fetch_kubeconfig` | Writes `controller_kubeconfig` |
| Join masters | `23_join_masters` | Remaining masters, one at a time |
| Join workers | `24_join_workers` | All workers |

kubeadm skips kube-proxy addon phase at init (`--skip-phases=addon/kube-proxy`); networking is completed in **atlas-k8s-addons**.

## Greenfield checklist

| Check | Expectation |
|-------|-------------|
| Validate | `./run.sh --tags 01_validate_vars` succeeds |
| VIP | `vip_address` is up on an LB (`ip addr` / Keepalived active) |
| API via VIP | `curl -k https://<control_plane_endpoint>/healthz` → `ok` |
| Masters | `kubectl get nodes` (with controller kubeconfig) lists all control-plane nodes |
| Workers | Worker nodes listed (if inventory non-empty) |
| Kubeconfig | `$CLUSTER_WORKSPACE_ROOT/controller-state/kubeconfig/admin.conf` exists |
| CNI | Not in this repo — run **atlas-k8s-addons** before expecting Pod Ready / cluster DNS |
| Time | Chrony/NTP healthy on nodes after `03_sync_time` |

Example:

```bash
export KUBECONFIG="$CLUSTER_WORKSPACE_ROOT/controller-state/kubeconfig/admin.conf"
kubectl get nodes -o wide
kubectl get --raw='/healthz'
```

## Troubleshooting

### Validate fails: missing inventory groups

`groups[k8s_master_hosts]` must be non-empty; `groups[k8s_lb_hosts]` must be non-empty; the group named by `k8s_worker_hosts` must exist (may be empty). Fix inventory (or targeting vars) and re-run:

```bash
./run.sh --tags 01_validate_vars
```

### Validate fails: workspace id / path contract

`cluster_workspace_id` must equal `k8s_cluster_domain`, and workspace paths must live under `cluster_workspace_root` with `cluster_workspace_root` under `cluster_workspace_parent`. Prefer:

```bash
CLUSTER_WORKSPACE_ID=k8s.example.com ./run.sh --tags 01_validate_vars
```

(matching `cluster_domain` / `k8s_cluster_domain` in `group_vars/all/atlas-k8s-core.yml`). Avoid relative roots that diverge from what validate sees.

### Validate fails: required core variables

Ensure VIP, `pki_ca_url`, versions, subnets, `control_plane_endpoint`, and Keepalived knobs are set in `group_vars/all/atlas-k8s-core.yml`. Placeholders `nexus_*` must still be non-empty strings even in `none` registry/repo modes.

### Keepalived VIP does not come up

Confirm the VRRP NIC (`keepalived_interface` empty = auto `ansible_default_ipv4.interface`; a configured name that is missing on the host falls back to that default — assert only if the default NIC is missing too), `vip_auth_pass` is ≤ 8 characters, no VRID clash (`keepalived_virtual_router_id`), and L2 connectivity allows VRRP. Re-run:

```bash
./run.sh --tags 10_lb
```

### Masters cannot reach API via controlPlaneEndpoint

`{{ k8s_lb_hostname }}.{{ dns_domain_suffix }}` must resolve to `vip_address` on every master/worker (DNS or hosts file). Nginx on LBs must stream to master IPs on `k8s_api_port`.

### Package install fails on nodes

With empty `pkg_repo_base` / `pkg_repo_nginx_ingress_domain`, nodes need outbound access to public Kubernetes package repos. For air-gapped labs, set `pkg_repo_base` (repository root) or `pkg_repo_nginx_ingress_domain` (nginx mirrors) via overlay vars (not shipped as org defaults here).

### `kubeadm init` / join preflight errors

Check time sync (`03_sync_time`), swap disabled / required sysctls from node prep, and that containerd is running after `11_k8s_hosts`. Re-run the failed stage tag after fixing the host.

### Join masters/workers fail with expired token

Re-probe cluster state, re-generate join material, and re-run joins:

```bash
./run.sh --tags 04_cluster_state,22_cluster_join_token
./run.sh --tags 04_cluster_state,23_join_masters
./run.sh --tags 04_cluster_state,24_join_workers
```

### Nodes NotReady / no Pod networking

Expected until CNI is installed. Continue with sibling **atlas-k8s-addons** (Calico + Helm bootstrap). Core only delivers kubeadm membership and API access via VIP.

### Controller missing `admin.conf`

```bash
./run.sh --tags 29_fetch_kubeconfig
ls -l "$CLUSTER_WORKSPACE_ROOT/controller-state/kubeconfig/admin.conf"
```

### Upgrade roles ran unexpectedly

Roles `25_*` / `26_*` are no-ops unless `k8s_needs_upgrade` is true. To force a planned upgrade, set versions in `group_vars/all/atlas-k8s-core.yml` and run those tags deliberately after reading the role tasks (drain on workers).

### SSH host key changed after VM recreate

```bash
ssh-keygen -f ~/.ssh/known_hosts -R '192.168.1.225'
```

## Testing / CI

Local checks (same gates as GitHub Actions):

```bash
./tests/run_ci.sh
# or piecemeal:
scripts/check-no-hardcoded-domains.sh
python3 -m unittest discover -s tests -v
ansible-playbook --syntax-check -i inventory-example.yml playbooks/cluster_core.yaml
ansible-lint --profile min
```

CI workflow: `.github/workflows/ci.yml` (unit tests, syntax-check, ansible-lint `min`, org-hostname scan, publish hygiene greps).

Optional stricter lint locally: `ansible-lint --profile basic` (many legacy style findings; not a merge gate yet).

Contract / hygiene tests live in `tests/test_k8s_core_layout.py`.

## Project structure

```
atlas-k8s-core/
├── playbooks/
│   └── cluster_core.yaml
├── run.sh
├── ansible.cfg
├── requirements.yml
├── inventory-example.yml
├── group_vars/
│   └── all/
│       └── atlas-k8s-core.yml
├── examples/
│   ├── hosts.example.yml
│   └── secrets.example.yml
├── host_vars/
│   └── example.yml
├── roles/
│   ├── 00_ensure_workspace/
│   ├── 00_controller_tooling/
│   ├── 01_validate_vars/
│   ├── 02_gather_facts/
│   ├── 03_sync_time/
│   ├── 04_cluster_state/
│   ├── 09_lb_vip_dns/
│   ├── 10_lb/
│   ├── 11_k8s_hosts/
│   ├── 12_workers_kernel_rbd/
│   ├── 21_kubeadm_init/
│   ├── 22_cluster_join_token/
│   ├── 23_join_masters/
│   ├── 24_join_workers/
│   ├── 25_kubeadm_upgrade_control_plane/
│   ├── 26_kubeadm_upgrade_workers/
│   ├── 29_fetch_kubeconfig/
│   └── common/
├── filter_plugins/
├── docs/
│   ├── examples/
│   └── optional_addons/          # reference Helm values; not installed by core
├── scripts/
│   └── check-no-hardcoded-domains.sh
├── tests/
│   ├── run_ci.sh
│   └── test_k8s_core_layout.py
├── .github/workflows/ci.yml
├── .ansible-lint
├── requirements-dev.txt
├── LICENSE
└── SECURITY.md
```

## Integrations

External orchestrators can call the same playbook with their own inventory and group/host vars. Set inventory groups (or override `k8s_lb_hosts` / `k8s_master_hosts` / `k8s_worker_hosts`) and knobs from `group_vars/all/atlas-k8s-core.yml` as needed (VIP, kube versions, CA URL, registry/repo modes).

Org-specific lab overlays (domains, mirrors, CA, package-repo prefixes) belong in the orchestrator inventory — not in this repository’s defaults.

Suggested tag sequence for split runs: validate → controller tooling → LB → hosts → init → join token / kubeconfig → join masters → join workers.

Helm/CNI and platform charts: sibling **atlas-k8s-addons**. Reference values under `docs/optional_addons/` are not installed by this playbook.

## Security

See [`SECURITY.md`](SECURITY.md) for reporting, secret-handling, and the pre-publish git history note. Do not commit real credentials, vault files, kubeconfigs, or live inventories (`inventory.yml` and local workspace paths are gitignored).

## Contributing

1. Keep `playbooks/cluster_core.yaml` as the only supported playbook entry.  
2. Document new operator-facing variables in `group_vars/all/atlas-k8s-core.yml` and role `defaults/`.  
3. Extend `tests/test_k8s_core_layout.py` for layout/contract changes.  
4. Keep `./tests/run_ci.sh` green before opening a PR.  
5. Update this README when behaviour, tags, or inventory contracts change.  
6. Keep product sources free of org lab hostnames (see `scripts/check-no-hardcoded-domains.sh`).

## Support

Open an issue in the repository for bugs and questions.
