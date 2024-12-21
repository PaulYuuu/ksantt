from behave import given, then, when
from behave.runner import Context
from ocp_resources.datavolume import DataVolume
from ocp_resources.pod import Pod
from timeout_sampler import TimeoutExpiredError

import utils
from utils.exceptions import BehaveStepError


@given("a DataVolume with accessMode {access_modes} and volumeMode {volume_mode}")
def define_dv(context: Context, access_modes: str, volume_mode: str):
    """Fixture to init DataVolume and return it."""
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


@when("I create a DataVolume")
def create_dv(context: Context):
    """Test creating a DataVolume in the dynamically created test namespace"""
    # Create the DataVolume in the test namespace
    context.dv.create()


@then("the DataVolume should be in Succeeded phase")
def dv_should_be_succeeded(context: Context):
    """Verify that the DataVolume transitions to the 'Succeeded' status."""
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

        context.log.error(f"DataVolume is in {context.dv.status} pahse")
        utils.rp_attach_plain(
            context.log.debug, "DataVolume importer events", "dv_events.txt", "\n".join(event_messages)
        )
        if not expected_skipped:
            raise BehaveStepError(context.step.name, f"Wait until DataVolume succeeded timeout after {timeout}s")
        context.scenario.skip(f'DataVolume using not supported accessModes "{context.dv.access_modes}"')


@when("I delete the DataVolume")
def delete_dv(context: Context):
    """Delete the DataVolume."""
    context.dv.delete(wait=True)
    context.log.info(f"DataVolume {context.dv.name} is deleted")


@then("the DataVolume should not exist")
def dv_should_not_exist(context: Context):
    """Verify that the DataVolume no longer exists."""
    assert not context.dv.exists, f"DataVolume '{context.dv.name}' still exists after deletion."
    context.log.info(f'DataVolume "{context.dv.name}" no longer exists')
