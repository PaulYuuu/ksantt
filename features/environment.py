import logging
import os

from behave import fixture, use_fixture
from behave.runner import Context
from behave_reportportal.behave_agent import BehaveAgent, create_rp_service
from behave_reportportal.config import read_config
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.storage_class import StorageClass
from reportportal_client import RPLogger, RPLogHandler

import utils


@fixture
def dynamic_client(context: Context):
    """
    Initialize and configure the Kubernetes dynamic client.
    """
    dyn_client = DynamicClient(client=config.new_client_from_config())
    context.client = dyn_client
    return dyn_client


@fixture
def random_namespace(context: Context):
    """
    Create a random test namespace for isolation.
    """
    random_suffix = utils.generate_random_string()
    ns_name = f"kubesan-ns-{random_suffix}"

    ns = Namespace(name=ns_name, client=context.client)
    if context.rph:
        ns.logger.addHandler(context.rph)
    ns.create(wait=True)
    ns.logger.info(f"Created namespace '{ns.name}'")
    context.ns = ns


@fixture
def storage_class(context: Context):
    """
    Create a KubeSAN StorageClass with specified parameters.
    """
    random_suffix = utils.generate_random_string()
    sc_name = f"kubesan-sc-{random_suffix}"

    parameters = {
        "lvmVolumeGroup": context.config.userdata["sc_vg"],
        "mode": context.config.userdata["sc_mode"],
        "csi.storage.k8s.io/fstype": context.config.userdata["sc_fstype"],
    }

    sc = StorageClass(
        name=sc_name,
        client=context.client,
        provisioner=context.config.userdata["sc_provisioner"],
        reclaim_policy=StorageClass.ReclaimPolicy.DELETE,
        volume_binding_mode=StorageClass.VolumeBindingMode.Immediate,
        parameters=parameters,
    )
    if context.rph:
        sc.logger.addHandler(context.rph)
    sc.create(wait=True)
    sc.logger.info(f"StorageClass '{sc.name}' created")
    context.sc = sc


def before_all(context: Context):
    """
    Initialize global test environment before any tests run.
    """
    rp_cfg = read_config(context)
    rp_cfg.api_key = rp_cfg.api_key or os.getenv("rp_api_key")
    rp_cfg.endpoint = rp_cfg.endpoint or os.getenv("rp_endpoint")
    rp_cfg.project = rp_cfg.project or os.getenv("rp_project")
    context.rp_client = create_rp_service(rp_cfg)
    context.rph = None
    logging.setLoggerClass(RPLogger)
    log = logging.getLogger("ksantt")
    log.setLevel("DEBUG")
    if context.rp_client is not None:
        # Workaround for ssl issue
        context.rp_client.verify_ssl = False

        context.rp_agent = BehaveAgent(rp_cfg, context.rp_client)
        context.rp_agent.start_launch(context)
        rph = RPLogHandler(rp_client=context.rp_client)
        log.addHandler(rph)
        context.rph = rph
    context.log = log


def after_all(context: Context):
    """
    Clean up global test environment after all tests complete.
    """
    if context.rp_client is not None:
        context.rp_agent.finish_launch(context)
        context.rp_client.terminate()


def before_feature(context: Context, feature):
    """
    Set up environment before each feature starts.
    """
    if context.rp_client is not None:
        context.rp_agent.start_feature(context, feature)
    use_fixture(dynamic_client, context)
    use_fixture(random_namespace, context)


def after_feature(context: Context, feature):
    """
    Clean up environment after each feature completes.
    """
    if context.rp_client is not None:
        context.rp_agent.finish_feature(context, feature)
    context.ns.delete(wait=True)


def before_scenario(context: Context, scenario):
    """
    Set up environment before each scenario starts.
    """
    use_fixture(storage_class, context)
    if context.rp_client is not None:
        context.rp_agent.start_scenario(context, scenario)


def after_scenario(context: Context, scenario):
    """
    Clean up environment after each scenario completes.
    """
    if context.rp_client is not None:
        context.rp_agent.finish_scenario(context, scenario)
    context.sc.delete(wait=True)


def before_step(context: Context, step):
    """
    Prepare environment before each step execution.
    """
    if context.rp_client is not None:
        context.rp_agent.start_step(context, step)


def after_step(context: Context, step):
    """
    Clean up environment after each step completes.
    """
    if context.rp_client is not None:
        context.rp_agent.finish_step(context, step)
