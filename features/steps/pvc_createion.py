from behave import given
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim

from utils import rp_attach_json


@given(r"a PVC specification with access mode (?P<access_modes>.+) and storage mode (?P<volume_mode>.+)")
def define_pvcs(context, access_modes, volume_mode):
    """
    Define a new PersistentVolumeClaim with the given configuration parameters.
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
    pvc.to_dict()
    context.pvcs = [pvc]
    rp_attach_json(
        context.logger.info,
        f"Defined PersistentVolumeClaim {pvc.name} with manifest",
        "pvc.json",
        pvc.res,
    )
