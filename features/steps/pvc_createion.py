from behave import given, then, when
from behave.runner import Context
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from timeout_sampler import TimeoutExpiredError

from utils import rp_attach_json


@given("a PVC with accessMode {access_modes} and volumeMode {volume_mode}")
def define_pvc(context: Context, access_modes: str, volume_mode: str):
    """
    Initialize a PersistentVolumeClaim (PVC) with the given parameters.

    :param context: behave context for sharing state across steps.
    :param access_modes: Access modes for the PVC (e.g., "ReadWriteOnce").
    :param volume_mode: Volume mode for the PVC (e.g., "Filesystem" or "Block").
    """
    sc_mode = context.sc.instance.parameters.mode
    pvc_name = f"pvc-{sc_mode.lower()}-{volume_mode.lower()}-{access_modes.lower()}"

    # Define the PVC resource
    pvc = PersistentVolumeClaim(
        name=pvc_name,
        namespace=context.ns.name,  # Assuming namespace is set in context
        client=context.client,  # Assuming client is set in context
        storage_class=context.sc.name,  # Assuming StorageClass is set in context
        accessmodes=access_modes,  # Ensure it's a list
        volume_mode=volume_mode,
        size="1Gi",
    )
    if context.rph:
        pvc.logger.addHandler(context.rph)
    pvc.to_dict()
    context.pvc = pvc
    rp_attach_json(context.log.info, "Defined PersistentVolumeClaim with manifest", "pvc.json", pvc.res)


@when("I create a PVC")
def create_pvc(context: Context):
    """Create the PersistentVolumeClaim (PVC) in the namespace."""
    context.pvc.create()


@then("the PVC should be Bound")
def pvc_should_be_bound(context: Context):
    """Verify that the PVC transitions to the 'Bound' status."""
    try:
        context.pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
        context.log.info(f"PersistentVolumeClaim {context.pvc.name} is bound")
    except TimeoutExpiredError:
        rp_attach_json(
            context.log.debug,
            f"PersistentVolumeClaim is in {context.pvc.status} status",
            "pvc_instance.json",
            context.pvc.instance.to_dict(),
        )
        raise


@when("I delete the PVC")
def delete_pvc(context: Context):
    """Delete the PersistentVolumeClaim (PVC) if it exists."""
    context.pvc.delete(wait=True)
    context.log.info(f"PersistentVolumeClaim {context.pvc.name} is deleted")


@then("the PVC should not exist")
def pvc_should_not_exist(context: Context):
    """Verify that the PVC no longer exists."""
    assert not context.pvc.exists, f"PersistentVolumeClaim '{context.pvc.name}' still exists after deletion."
    context.log.info(f"PersistentVolumeClaim '{context.pvc.name}' no longer exists")
