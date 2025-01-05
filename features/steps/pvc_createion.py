from behave import given
from behave.runner import Context
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim

from utils import rp_attach_json


@given(r"a PVC specification with access mode (?P<access_modes>.+) and storage mode (?P<volume_mode>.+)")
def define_pvc(context: Context, access_modes: str, volume_mode: str):
    """
    Define a new PersistentVolumeClaim object with the given configuration parameters.

    Args:
        context: Behave context containing test configuration and resources
        access_modes: Storage access mode (e.g., ReadWriteOnce, ReadOnlyMany)
        volume_mode: Volume mode for the storage (e.g., Block, Filesystem)
    """
    sc_mode = context.sc.instance.parameters.mode
    name = f"pvc-{sc_mode.lower()}-{volume_mode.lower()}-{access_modes.lower()}"
    size = context.params["pvc"]["size"]

    pvc = PersistentVolumeClaim(
        name=name,
        namespace=context.ns.name,
        client=context.client,
        storage_class=context.sc.name,
        accessmodes=access_modes,
        volume_mode=volume_mode,
        size=size,
    )
    if context.rph:
        pvc.logger.addHandler(context.rph)
    pvc.to_dict()
    context.pvcs = [pvc]
    rp_attach_json(context.log.info, "Defined PersistentVolumeClaim with manifest", "pvc.json", pvc.res)
