import pytest
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.storage_class import StorageClass

import ksantt.utils
from ksantt.utils.options import KubeSanOptions


# pytest_addoption implementation
def pytest_addoption(parser: pytest.Parser):
    options = KubeSanOptions(parser)
    options.add_options()


@pytest.fixture(scope="module")
def dynamic_client():
    """Fixture to initialize the Kubernetes DynamicClient."""
    dyn_client = DynamicClient(client=config.new_client_from_config())
    return dyn_client


@pytest.fixture(scope="module")
def random_ns(dynamic_client: DynamicClient):
    """Fixture to create a random test namespace."""
    # Generate a random string for the namespace
    random_suffix = ksantt.utils.generate_random_string()
    ns_name = f"kubesan-ns-{random_suffix}"

    # Create the test namespace
    with Namespace(name=ns_name, client=dynamic_client) as ns:
        ns.wait_for_status(status=Namespace.Status.ACTIVE, timeout=30)
        ns.logger.info(f"Created namespace '{ns.name}'")
        yield ns


@pytest.fixture(scope="module")
def kubesan_sc(request: pytest.FixtureRequest, dynamic_client: DynamicClient):
    """Fixture to create and return a KubeSAN StorageClass."""
    random_suffix = ksantt.utils.generate_random_string()
    sc_name = f"kubesan-sc-{random_suffix}"

    parameters = {
        "lvmVolumeGroup": request.config.getoption("--sc-vg"),
        "mode": request.config.getoption("--sc-mode"),
        "csi.storage.k8s.io/fstype": request.config.getoption("--sc-fstype"),
    }

    # Create the KubeSAN StorageClass
    with StorageClass(
        name=sc_name,
        client=dynamic_client,
        provisioner="kubesan.gitlab.io",
        reclaim_policy=StorageClass.ReclaimPolicy.DELETE,
        volume_binding_mode=StorageClass.VolumeBindingMode.Immediate,
        parameters=parameters,
    ) as sc:
        sc.logger.info(f"StorageClass '{sc.name}' created")
        yield sc
