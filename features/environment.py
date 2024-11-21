import logging

from behave import fixture, use_fixture
from behave_reportportal.behave_agent import BehaveAgent, create_rp_service
from behave_reportportal.config import read_config
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.storage_class import StorageClass
from reportportal_client import RPLogger, RPLogHandler


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
        yield ns


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
        yield sc


def before_all(context):
    cfg = read_config(context)
    context.rp_client = create_rp_service(cfg)
    # Workaround for ssl issue
    context.rp_client.verify_ssl = False
    context.rp_agent = BehaveAgent(cfg, context.rp_client)
    context.rp_agent.start_launch(context)
    logging.setLoggerClass(RPLogger)
    log = logging.getLogger(__name__)
    log.setLevel("DEBUG")
    rph = RPLogHandler(rp_client=context.rp_client)
    log.addHandler(rph)
    context.log = log


def after_all(context):
    context.rp_agent.finish_launch(context)
    context.rp_client.terminate()


def before_feature(context, feature):
    use_fixture(dynamic_client, context)
    use_fixture(random_namespace, context)
    context.rp_agent.start_feature(context, feature)


def after_feature(context, feature):
    context.rp_agent.finish_feature(context, feature)


def before_scenario(context, scenario):
    use_fixture(storage_class, context)
    context.rp_agent.start_scenario(context, scenario)


def after_scenario(context, scenario):
    context.rp_agent.finish_scenario(context, scenario)


def before_step(context, step):
    context.rp_agent.start_step(context, step)


def after_step(context, step):
    context.rp_agent.finish_step(context, step)
