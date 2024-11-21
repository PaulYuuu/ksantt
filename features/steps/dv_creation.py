from behave import given, then, when
from behave.runner import Context
from ocp_resources.datavolume import DataVolume

from ksantt import utils


@given("a DataVolume with accessModes {access_modes} and volumeMode {volume_mode}")
def dv(context: Context, access_modes: str, volume_mode: str):
    """Fixture to init DV and return it."""
    sc_mode = context.sc.instance.parameters.mode
    dv_name = f"dv-{sc_mode.lower()}-{volume_mode.lower()}-{access_modes.lower()}"
    url = "https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-latest.x86_64.qcow2"

    dv = DataVolume(
        name=dv_name,
        namespace=context.ns.name,
        client=context.client,
        source="http",
        url=url,
        storage_class=context.sc.name,
        access_modes=access_modes,
        volume_mode=volume_mode,
        size="10Gi",
        preallocation=False,
        teardown=False,
    )
    dv.to_dict()
    utils.rp_attachment_json(
        context.log.info, f"Defined DV with following manifest:\n{dv.to_yaml()}", "dv.json", dv.res
    )
    context.dv = dv


@when("I create a DataVolume")
def step_create_dv(context: Context):
    """Test creating a DV in the dynamically created test namespace"""
    # Create the DV in the test namespace
    context.dv.create()
    context.log.info(f"Created DV {context.dv.name} in namespace {context.dv.namespace}")


@then("the DataVolume should be Succeeded")
def step_dv_should_be_succeeded(context: Context):
    """Verify that the DV transitions to the 'Succeeded' status."""
    context.dv.wait_for_dv_success(timeout=360)
    context.log.info(
        f"DV {context.dv.name} is Created in namespace {context.dv.namespace} with "
        f"volume mode {context.dv.volume_mode} and access mode {context.dv.access_modes}"
    )


@when("I delete the DataVolume")
def step_delete_dv(context: Context):
    """Delete the DataVolume if it exists."""
    if context.dv.exists:
        context.dv.delete(wait=True)
        context.log.info(f"Deleted DV '{context.dv.name}' from namespace '{context.dv.namespace}'.")
    else:
        context.log.warning(f"DataVolume '{context.dv.name}' does not exist.")


@then("the DataVolume should not exist")
def step_dv_should_not_exist(context: Context):
    """Verify that the DV no longer exists."""
    assert not context.dv.exists, f"DV '{context.dv.name}' still exists after deletion."
    context.log.info(f"Confirmed DV '{context.dv.name}' no longer exists in namespace '{context.dv.namespace}'.")
