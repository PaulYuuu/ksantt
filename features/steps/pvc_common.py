from itertools import zip_longest

from behave import given, then, when
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from timeout_sampler import TimeoutExpiredError

import utils


class PVCSteps:
    @given(r"(?P<count>\d+) PVC(?:s)?")
    def define_pvcs(context, count):
        """
        Define PersistentVolumeClaim(s) in the cluster.
        """
        table = context.table or []
        context.pvcs = []
        pvc_params = {
            "accessmodes": context.params["pvc"]["accessmodes"],
            "volume_mode": context.params["pvc"]["volume_mode"],
            "size": context.params["pvc"]["size"],
        }
        for _, extra_params in zip_longest(range(int(count)), table, fillvalue={}):
            name = f"pvc-{utils.generate_random_string(8)}"
            pvc_params.update(extra_params.items())
            pvc = PersistentVolumeClaim(
                name=name,
                namespace=context.ns.name,
                client=context.client,
                storage_class=context.sc.name,
                **pvc_params,
            )
            pvc.to_dict()
            context.pvcs.append(pvc)
            utils.rp_attach_json(
                context.logger.info,
                f"Defined PersistentVolumeClaim {pvc.name} with manifest",
                f"{pvc.name}.json",
                pvc.res,
            )

    @when(r"I create the PVC(?:s)?")
    def create_pvcs(context):
        """
        Create PersistentVolumeClaim(s) from the defined objects.
        """
        for pvc in context.pvcs:
            pvc.create()

    @then(r"the PVC(?:s)? status should change to Bound")
    def pvc_should_be_bound(context):
        """
        Monitor the PersistentVolumeClaim(s) status and wait for it to reach the Bound state.

        Raises:
            TimeoutExpiredError: If the PVC fails to reach 'Bound' status within timeout
        """
        for pvc in context.pvcs:
            try:
                pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
                context.logger.info(f"PersistentVolumeClaim {pvc.name} is bound")
            except TimeoutExpiredError:
                utils.rp_attach_json(
                    context.logger.debug,
                    f"PersistentVolumeClaim is in {pvc.status} status",
                    f"{pvc.name}_instance.json",
                    pvc.instance.to_dict(),
                )
                raise

    @when(r"I perform a deletion of the PVC(?:s)?")
    def delete_pvcs(context):
        """
        Remove PersistentVolumeClaim(s) from the cluster and ensure deletion is finished.

        Args:
            context: Behave context containing the PVC to delete
        """
        for pvc in context.pvcs:
            pvc.delete(wait=True)
            context.logger.info(f"PersistentVolumeClaim {pvc.name} is deleted")

    @then(r"the PVC(?:s)? should be completely removed")
    def pvcs_should_not_exist(context):
        """
        Verify that the PersistentVolumeClaim(s) has been completely removed from the system.

        Raises:
            AssertionError: If the PVC still exists after deletion
        """
        for pvc in context.pvcs:
            assert not pvc.exists, f"PersistentVolumeClaim '{pvc.name}' still exists after deletion."
            context.logger.info(f"PersistentVolumeClaim '{pvc.name}' no longer exists")
            context.pvcs.remove(pvc)
