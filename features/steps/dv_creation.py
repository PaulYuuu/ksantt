from behave import given
from behave.runner import Context
from ocp_resources.datavolume import DataVolume

import utils


@given(r"a DV specification with access mode (?P<access_modes>.+) and storage mode (?P<volume_mode>.+)")
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
    url = context.params["dv"]["url"]
    size = context.params["dv"]["size"]
    source = context.params["dv"]["source"]

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
    )
    if context.rph:
        dv.logger.addHandler(context.rph)
    dv.to_dict()
    context.dvs = [dv]
    utils.rp_attach_json(context.log.info, "Defined DataVolume with manifest", "dv.json", dv.res)
