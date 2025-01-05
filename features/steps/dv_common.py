from behave import given, then, when
from behave.runner import Context
from ocp_resources.datavolume import DataVolume
from ocp_resources.pod import Pod
from timeout_sampler import TimeoutExpiredError

import utils
from utils.exceptions import BehaveStepError


class DVSteps:
    @given(r"(?P<count>\d+) DV(?:s)?")
    def define_dvs(context: Context, count: str):
        """
        Define multiple DataVolume(s) in the cluster.

        Args:
            context: Behave context containing test configuration and resources
            count: Number of DataVolumes to define
        """
        context.dvs = []

        access_modes = context.params["dv"]["access_modes"]
        size = context.params["dv"]["size"]
        source = context.params["dv"]["source"]
        url = context.params["dv"]["url"]
        volume_mode = context.params["dv"]["volume_mode"]

        for _ in range(int(count)):
            name = f"dv-{utils.generate_random_string(8)}"
            dv = DataVolume(
                name=name,
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
            context.dvs.append(dv)
            utils.rp_attach_json(context.log.info, f"Defined {dv.name} with manifest", f"{dv.name}.json", dv.res)

    @when(r"I create the DV(?:s)?")
    def create_dvs(context: Context):
        """
        Create multiple DV(s) in the cluster.

        Args:
            context: Behave context containing the DataVolume object to be created
        """
        for dv in context.dvs:
            dv.create()

    @then(r"the DV(?:s)? status should change to Succeeded")
    def dvs_should_be_succeeded(context: Context):
        """
        Monitor the DataVolume(s) status and wait for it to reach the Succeeded state.

        Args:
            context: Behave context containing the DataVolume to verify

        Raises:
            BehaveStepError: If the DataVolume fails to reach 'Succeeded' status within timeout
        """
        timeout = 360
        for dv in context.dvs:
            try:
                dv.wait_for_dv_success(timeout=timeout)
                context.log.info(f"DataVolume {dv.name} is ready")
            except TimeoutExpiredError:
                expected_skipped = False
                prime_pvc = dv.pvc.prime_pvc
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

                context.log.error(f"DataVolume is in {dv.status} phase")
                utils.rp_attach_plain(
                    context.log.debug, f"{dv.name} importer events", f"{dv.name}_events.txt", "\n".join(event_messages)
                )
                if not expected_skipped:
                    raise BehaveStepError(
                        context.step.name, f"Wait until DataVolume succeeded timeout after {timeout}s"
                    )
                context.scenario.skip(f'DataVolume using not supported accessModes "{dv.access_modes}"')

    @when(r"I perform a deletion of the DV(?:s)?")
    def delete_dvs(context: Context):
        """
        Remove the DataVolume(s) from the cluster and ensure deletion is finished.

        Args:
            context: Behave context containing the DataVolume to delete
        """
        for dv in context.dvs:
            dv.delete(wait=True)
            context.log.info(f"DataVolume {dv.name} is deleted")

    @then(r"the DV(?:s)? should be completely removed")
    def dvs_should_not_exist(context: Context):
        """
        Verify that the DataVolume(s) have been completely removed from the system.

        Args:
            context: Behave context containing the DataVolume to verify

        Raises:
            AssertionError: If the DataVolume still exists after deletion
        """
        for dv in context.dvs:
            assert not dv.exists, f"DataVolume '{dv.name}' still exists after deletion."
            context.log.info(f'DataVolume "{dv.name}" no longer exists')
