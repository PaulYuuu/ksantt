from behave import given, then, when
from behave.runner import Context
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from timeout_sampler import TimeoutExpiredError

import utils


class PVCSteps:
    @given(r"(?P<count>\d+) PVC(?:s)?")
    def define_pvcs(context: Context, count: str):
        """
        Define multiple PVC(s) in the cluster.

        Args:
            context: Behave context containing test configuration and resources
            count: Number of PVCs to define
        """
        context.pvcs = []
        access_modes = context.params["pvc"]["access_modes"]
        volume_mode = context.params["pvc"]["volume_mode"]
        size = context.params["pvc"]["size"]
        for _ in range(int(count)):
            name = f"pvc-{utils.generate_random_string(8)}"
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
            context.pvcs.append(pvc)
            utils.rp_attach_json(context.log.info, f"Defined {pvc.name} with manifest", f"{pvc.name}.json", pvc.res)

    @when(r"I create the PVC(?:s)?")
    def create_pvcs(context: Context):
        """
        Create multiple PVC(s) in the cluster.

        Args:
            context: Behave context containing the PVC object to be created
        """
        for pvc in context.pvcs:
            pvc.create()

    @then(r"the PVC(?:s)? status should change to Bound")
    def pvc_should_be_bound(context: Context):
        """
        Monitor the PVC(s) status and wait for it to reach the Bound state.

        Args:
            context: Behave context containing the PVC to verify

        Raises:
            TimeoutExpiredError: If the PVC fails to reach 'Bound' status within timeout
        """
        for pvc in context.pvcs:
            try:
                pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
                context.log.info(f"PersistentVolumeClaim {pvc.name} is bound")
            except TimeoutExpiredError:
                utils.rp_attach_json(
                    context.log.debug,
                    f"PersistentVolumeClaim is in {pvc.status} status",
                    f"{pvc.name}_instance.json",
                    pvc.instance.to_dict(),
                )
                raise

    @when(r"I perform a deletion of the PVC(?:s)?")
    def delete_pvcs(context: Context):
        """
        Remove PVC(s) from the cluster and ensure deletion is finished.

        Args:
            context: Behave context containing the PVC to delete
        """
        for pvc in context.pvcs:
            pvc.delete(wait=True)
            context.log.info(f"PersistentVolumeClaim {pvc.name} is deleted")

    @then(r"the PVC(?:s)? should be completely removed")
    def pvcs_should_not_exist(context: Context):
        """
        Verify that the PVC(s) has been completely removed from the system.

        Args:
            context: Behave context containing the PVC to verify

        Raises:
            AssertionError: If the PVC still exists after deletion
        """
        for pvc in context.pvcs:
            assert not pvc.exists, f"PersistentVolumeClaim '{pvc.name}' still exists after deletion."
            context.log.info(f"PersistentVolumeClaim '{pvc.name}' no longer exists")
