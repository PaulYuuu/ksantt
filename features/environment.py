from kubernetes import config
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.storage_class import StorageClass

from behave import fixture, use_fixture


@fixture
def dynamic_client(context):
    """Fixture to initialize the Kubernetes DynamicClient."""
    # Initialize Kubernetes dynamic client
    dyn_client = DynamicClient(client=config.new_client_from_config())
    context.client = dyn_client
    return dyn_client


@fixture
def random_namespace(context):
    """Fixture to create a random test namespace."""
    # Generate a random name for the namespace (you can add randomness if needed)
    ns_name = "kubesan-ns-behave"

    # Create the test namespace
    with Namespace(name=ns_name, client=context.client) as ns:
        # Wait for the namespace to be in ACTIVE state
        ns.wait_for_status(status=Namespace.Status.ACTIVE, timeout=30)
        ns.logger.info(f"Created namespace '{ns.name}'")
        context.ns = ns
        return ns


@fixture
def storage_class(context):
    """Fixture to create and return a KubeSAN StorageClass."""
    sc_name = "kubesan-sc-behave"

    parameters = {
        "lvmVolumeGroup": "kubesan-vg",
        "mode": "Thin",
        "csi.storage.k8s.io/fstype": "ext4",
    }

    # Create the KubeSAN StorageClass
    with StorageClass(
        name=sc_name,
        client=context.client,
        provisioner="kubesan.gitlab.io",
        reclaim_policy=StorageClass.ReclaimPolicy.DELETE,
        volume_binding_mode=StorageClass.VolumeBindingMode.Immediate,
        parameters=parameters,
    ) as sc:
        sc.logger.info(f"StorageClass '{sc.name}' created")
        context.sc = sc
        return sc


def before_feature(context, feature):
    use_fixture(dynamic_client, context)
    use_fixture(random_namespace, context)


def before_scenario(context, scenario):
    use_fixture(storage_class, context)
