from itertools import zip_longest

from behave import given, then, when
from ocp_resources.datavolume import DataVolume
from ocp_resources.pod import Pod
from timeout_sampler import TimeoutExpiredError

import utils
from utils.exceptions import BehaveScenarioError


class DVSteps:
    @given(r"(?P<count>\d+) DV(?:s)?")
    def define_dvs(context, count):
        """
        Define DataVolume(s) in the cluster.
        """
        table = context.table or []
        context.dvs = []
        dv_params = {
            "access_modes": context.params["dv"]["access_modes"],
            "size": context.params["dv"]["size"],
            "source": context.params["dv"]["source"],
            "url": context.params["dv"]["url"],
            "volume_mode": context.params["dv"]["volume_mode"],
        }

        for _, extra_params in zip_longest(range(int(count)), table, fillvalue={}):
            name = f"dv-{utils.generate_random_string(8)}"
            dv_params.update(extra_params.items())
            dv = DataVolume(
                name=name,
                namespace=context.ns.name,
                client=context.client,
                storage_class=context.sc.name,
                **dv_params,
            )
            dv.to_dict()
            context.dvs.append(dv)
            utils.rp_attach_json(
                context.logger.info,
                f"Defined DataVolume {dv.name} with manifest",
                f"{dv.name}.json",
                dv.res,
            )

    @when(r"I create the DV(?:s)?")
    def create_dvs(context):
        """
        Create DataVolume(s) from the defined objects.
        """
        for dv in context.dvs:
            dv.create()

    @then(r"the DV(?:s)? status should change to Succeeded")
    def dvs_should_be_succeeded(context):
        """
        Monitor the DataVolume(s) status and wait for it to reach the Succeeded state.

        Raises:
            BehaveStepError: If the DataVolume fails to reach 'Succeeded' status within timeout
        """
        for dv in context.dvs:
            try:
                dv.wait_for_dv_success()
                context.logger.info(f"DataVolume {dv.name} is ready")
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

                context.logger.error(f"DataVolume is in {dv.status} phase")
                utils.rp_attach_plain(
                    context.logger.debug,
                    f"{dv.name} importer events",
                    f"{dv.name}_events.txt",
                    "\n".join(event_messages),
                )
                if not expected_skipped:
                    raise BehaveScenarioError(context.scenario.name, "Wait until DataVolume succeeded")
                context.scenario.skip(f'DataVolume using not supported accessModes "{dv.access_modes}"')

    @when(r"I perform a deletion of the DV(?:s)?")
    def delete_dvs(context):
        """
        Remove the DataVolume(s) from the cluster and ensure deletion is finished.
        """
        for dv in context.dvs:
            dv.delete(wait=True)
            context.logger.info(f"DataVolume {dv.name} is deleted")

    @then(r"the DV(?:s)? should be completely removed")
    def dvs_should_not_exist(context):
        """
        Verify that the DataVolume(s) have been completely removed from the system.

        Raises:
            AssertionError: If the DataVolume still exists after deletion
        """
        for dv in context.dvs:
            assert not dv.exists, f"DataVolume '{dv.name}' still exists after deletion."
            context.logger.info(f'DataVolume "{dv.name}" no longer exists')
            context.dvs.remove(dv)
