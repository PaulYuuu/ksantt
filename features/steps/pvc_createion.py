from behave import given, then, when
from behave.runner import Context
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim

from ksantt import utils


@given("a PVC with accessModes {access_modes} and volumeMode {volume_mode}")
def step_given_pvc(context: Context, access_modes: str, volume_mode: str):
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
        teardown=False,
    )
    pvc.to_dict()
    utils.rp_attachment_json(
        context.log.info, f"Defined PVC with following manifest:\n{pvc.to_yaml()}", "pvc.json", pvc.res
    )
    context.pvc = pvc


@when("I create a PVC")
def step_create_pvc(context: Context):
    """Create the PersistentVolumeClaim (PVC) in the namespace."""
    context.pvc.create()
    context.log.info(f"Created PVC '{context.pvc.name}' in namespace '{context.pvc.namespace}'.")


@then("the PVC should be Bound")
def step_pvc_should_be_bound(context: Context):
    """Verify that the PVC transitions to the 'Bound' status."""
    context.pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
    context.log.info(f"PVC '{context.pvc.name}' is Bound in namespace '{context.pvc.namespace}'.")


@when("I delete the PVC")
def step_delete_pvc(context: Context):
    """Delete the PersistentVolumeClaim (PVC) if it exists."""
    if context.pvc.exists:
        context.pvc.delete(wait=True)
        context.log.info(f"Deleted PVC '{context.pvc.name}' from namespace '{context.pvc.namespace}'.")
    else:
        context.pvc.logger.warning(f"PVC '{context.pvc.name}' does not exist.")


@then("the PVC should not exist")
def step_pvc_should_not_exist(context: Context):
    """Verify that the PVC no longer exists."""
    assert not context.pvc.exists, f"PVC '{context.pvc.name}' still exists after deletion."
    context.log.info(f"Confirmed PVC '{context.pvc.name}' no longer exists in namespace '{context.pvc.namespace}'.")
