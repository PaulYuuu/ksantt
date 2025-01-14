import logging
import os
from pathlib import Path

import yaml
from behave import fixture, use_fixture, use_step_matcher
from behave.runner import Context
from behave_reportportal.behave_agent import BehaveAgent, create_rp_service
from behave_reportportal.config import read_config
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.storage_class import StorageClass
from reportportal_client import RPLogger, RPLogHandler

import utils

use_step_matcher("re")


@fixture
def dynamic_client(context: Context):
    """
    Initialize and configure the Kubernetes dynamic client.
    """
    dyn_client = DynamicClient(client=config.new_client_from_config())
    context.client = dyn_client
    return dyn_client


@fixture
def load_parameters(context: Context):
    """
    Load parameters from the config file.
    """
    # Parameters
    config_file = Path(__file__).parent / "configs.yaml"
    with open(config_file, "r") as conf:
        params = yaml.safe_load(conf)
        common = params.pop("common", {})
        for section in params:
            for key, value in common.items():
                params[section].setdefault(key, value)
    for key, value in context.config.userdata.items():
        section = key.split(".", 1)
        if section[0] in params:
            params[section[0]][section[1]] = value
        else:
            for section in params:
                params[section][key] = value
    context._params = params


@fixture
def logger(context: Context):
    """
    Logger fixture.
    """
    # ReportPortal and logger
    rp_cfg = read_config(context)
    rp_cfg.api_key = rp_cfg.api_key or os.getenv("rp_api_key")
    rp_cfg.endpoint = rp_cfg.endpoint or os.getenv("rp_endpoint")
    rp_cfg.project = rp_cfg.project or os.getenv("rp_project")
    context.rp_client = create_rp_service(rp_cfg)
    logging.setLoggerClass(RPLogger)
    logger = logging.getLogger("ksantt")
    logger.setLevel("DEBUG")
    context.logger = logger
    if context.rp_client is not None:
        # Workaround for ssl issue
        context.rp_client.verify_ssl = False
        context.rp_agent = BehaveAgent(rp_cfg, context.rp_client)
        context.rp_agent.start_launch(context)
        rph = RPLogHandler(rp_client=context.rp_client)
        logging.getLogger().addHandler(rph)


@fixture
def random_namespace(context: Context):
    """
    Create a random test namespace for isolation.
    """
    random_suffix = utils.generate_random_string()
    ns_name = f"kubesan-ns-{random_suffix}"

    ns = Namespace(name=ns_name, client=context.client)
    ns.logger.propagate = True
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
        "lvmVolumeGroup": context._params["sc"]["vg"],
        "mode": context._params["sc"]["mode"],
        "csi.storage.k8s.io/fstype": context._params["sc"]["fstype"],
    }

    sc = StorageClass(
        name=sc_name,
        client=context.client,
        provisioner=context._params["sc"]["provisioner"],
        reclaim_policy=StorageClass.ReclaimPolicy.DELETE,
        volume_binding_mode=StorageClass.VolumeBindingMode.Immediate,
        allow_volume_expansion=True,
        parameters=parameters,
    )
    sc.logger.propagate = True
    sc.create(wait=True)
    sc.logger.info(f"StorageClass '{sc.name}' created")
    context.sc = sc


def before_all(context: Context):
    """
    Initialize global test environment before any tests run.
    """
    use_fixture(logger, context)
    use_fixture(load_parameters, context)
    use_fixture(dynamic_client, context)


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
    use_fixture(random_namespace, context)
    use_fixture(storage_class, context)


def after_feature(context: Context, feature):
    """
    Clean up environment after each feature completes.
    """
    context.sc.delete(wait=True)
    context.ns.delete(wait=True)
    if context.rp_client is not None:
        context.rp_agent.finish_feature(context, feature)


def before_scenario(context: Context, scenario):
    """
    Set up environment before each scenario starts.
    """
    context.params = context._params.copy()
    if context.rp_client is not None:
        context.rp_agent.start_scenario(context, scenario)


def after_scenario(context: Context, scenario):
    """
    Clean up environment after each scenario completes.
    """
    del context.params
    if context.rp_client is not None:
        context.rp_agent.finish_scenario(context, scenario)


def before_step(context: Context, step):
    """
    Set up environment before each step execution.
    """
    if context.rp_client is not None:
        context.rp_agent.start_step(context, step)


def after_step(context: Context, step):
    """
    Clean up environment after each step completes.
    """
    if context.rp_client is not None:
        context.rp_agent.finish_step(context, step)
