from behave import given, then, when
from behave.runner import Context
from ocp_resources.datavolume import DataVolume
from ocp_resources.pod import Pod
from timeout_sampler import TimeoutExpiredError

import utils
from utils.exceptions import BehaveStepError


@given("a DV specification with access mode {access_modes} and storage mode {volume_mode}")
def define_dv(context: Context, access_modes: str, volume_mode: str):
    """
    Define a new DataVolume object with the given configuration parameters.

    Args:
        context: Behave context containing test configuration and resources
        access_modes: Storage access mode (e.g., ReadWriteOnce, ReadOnlyMany)
        volume_mode: Volume mode for the storage (e.g., Block, Filesystem)
    """
    sc_mode = context.sc.instance.parameters.mode
    dv_name = f"dv-{sc_mode.lower()}-{volume_mode.lower()}-{access_modes.lower()}"
    url = context.config.userdata["image_url"]
    size = context.config.userdata["image_size"]
    source = context.config.userdata["image_source"]

    dv = DataVolume(
        name=dv_name,
        namespace=context.ns.name,
        client=context.client,
        source=source,
        url=url,
        storage_class=context.sc.name,
        access_modes=access_modes,
        volume_mode=volume_mode,
        size=size,
        preallocation=False,
    )
    if context.rph:
        dv.logger.addHandler(context.rph)
    dv.to_dict()
    context.dv = dv
    utils.rp_attach_json(context.log.info, "Defined DataVolume with manifest", "dv.json", dv.res)


@when("I create the DV")
def create_dv(context: Context):
    """
    Create a new DataVolume instance in the cluster using the predefined specification.

    Args:
        context: Behave context containing the DataVolume object to be created
    """
    context.dv.create()


@then("the DV status should change to Succeeded")
def dv_should_be_succeeded(context: Context):
    """
    Monitor the DataVolume status and wait for it to reach the Succeeded state.

    Args:
        context: Behave context containing the DataVolume to verify

    Raises:
        BehaveStepError: If the DataVolume fails to reach 'Succeeded' status within timeout
    """
    timeout = 360
    try:
        context.dv.wait_for_dv_success(timeout=timeout)
        context.log.info(f"DataVolume {context.dv.name} is ready")
    except TimeoutExpiredError:
        expected_skipped = False
        prime_pvc = context.dv.pvc.prime_pvc
        importer = Pod(
            name=prime_pvc.instance.metadata.annotations["cdi.kubevirt.io/storage.import.importPodName"],
            namespace=context.ns.name,
        )
        event_messages = []
        for event in importer.events(timeout=3):
            event = event["object"]
            message = event.message
            if "Filesystem volumes only support single-node access modes" in message:
                expected_skipped = True
            event_messages.append(message)

        context.log.error(f"DataVolume is in {context.dv.status} phase")
        utils.rp_attach_plain(
            context.log.debug, "DataVolume importer events", "dv_events.txt", "\n".join(event_messages)
        )
        if not expected_skipped:
            raise BehaveStepError(context.step.name, f"Wait until DataVolume succeeded timeout after {timeout}s")
        context.scenario.skip(f'DataVolume using not supported accessModes "{context.dv.access_modes}"')


@when("I perform a deletion of the DV")
def delete_dv(context: Context):
    """
    Remove the DataVolume from the cluster and ensure deletion is finished.

    Args:
        context: Behave context containing the DataVolume to delete
    """
    context.dv.delete(wait=True)
    context.log.info(f"DataVolume {context.dv.name} is deleted")


@then("the DV should be completely removed")
def dv_should_not_exist(context: Context):
    """
    Verify that the DataVolume has been completely removed from the system.

    Args:
        context: Behave context containing the DataVolume to verify

    Raises:
        AssertionError: If the DataVolume still exists after deletion
    """
    assert not context.dv.exists, f"DataVolume '{context.dv.name}' still exists after deletion."
    context.log.info(f'DataVolume "{context.dv.name}" no longer exists')
