from behave import given
from ocp_resources.datavolume import DataVolume

import utils


@given(r"a DV with access mode (?P<access_modes>.+) and volume mode (?P<volume_mode>.+)")
def define_dv(context, access_modes, volume_mode):
    """
    Define a new DataVolume with the given configuration parameters.

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
    dv.to_dict()
    context.dvs = [dv]
    utils.rp_attach_json(
        context.logger.info,
        f"Defined DataVolume {dv.name} with manifest",
        "dv.json",
        dv.res,
    )
