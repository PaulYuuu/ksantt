from behave import given, when
from timeout_sampler import TimeoutExpiredError, TimeoutSampler


class MigrationSteps:
    @given(r"(?P<count>\d+) migratable VM(?:s)?")
    def define_migratable_vms(context, count):
        """
        Define VirtualMachine(s) in the cluster.
        """
        context.params["vm"]["access_modes"] = "ReadWriteMany"
        context.execute_steps(f"Given {count} VM{'' if int(count) == 1 else 's'}")

    @when(r"I migrate the VM(?:s)?")
    def migrate_vms(context):
        for vm in context.vms:
            vm.migrate()

    @when(r"I migrate the VM(?:s)? (?P<count>\d+) times")
    def migrate_vms_multi_times(context, count):
        for i in range(1, count + 1):
            vmims = []
            context.logger.info(f"Migrate the VMs in loop: {i}")
            for vm in context.vms:
                vmims.append(vm.migrate(wait=False))

            for vmim in vmims:
                try:
                    for sample in TimeoutSampler(
                        wait_timeout=360,
                        sleep=10,
                        func=lambda: vmim.instance.status.phase,
                    ):
                        if sample == vmim.Status.SUCCEEDED:
                            break
                except TimeoutExpiredError as exc:
                    context.logger.error(f"Migration {vmim.name} failed: {exc}")
                    raise
