import openshift_client as oc

drain_node = oc.drain_node
node_ssh_await = oc.node_ssh_await
node_ssh_client = oc.node_ssh_client
node_ssh_client_exec = oc.node_ssh_client_exec


def uncordon_node(
    node_name,
    dry_run=False,
    selector=None,
    auto_raise=True,
):
    r = oc.Result("uncordon")

    base_args = list()

    if dry_run:
        base_args.append(f"--dry-run={dry_run}")

    if selector:
        base_args.append(f"--selector={selector}")

    r.add_action(oc.oc_action(oc.cur_context(), "adm", cmd_args=["uncordon", node_name, base_args], no_namespace=True))

    if auto_raise:
        r.fail_if("Error during uncordon of node: {}".format(node_name))

    return r
