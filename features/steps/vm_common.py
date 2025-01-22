from itertools import zip_longest

from behave import given, then, when
from timeout_sampler import TimeoutExpiredError

import utils
from ocp.vm import VM


class VMSteps:
    @given(r"(?P<count>\d+) VM(?:s)?")
    def define_vms(context, count):
        """
        Define VirtualMachine(s) in the cluster.
        """
        table = context.table or []
        context.vms = []
        vm_params = {
            "url": context.params["vm"]["url"],
            "size": context.params["vm"]["size"],
            "source": context.params["vm"]["source"],
            "access_modes": context.params["vm"]["access_modes"],
            "volume_mode": context.params["vm"]["volume_mode"],
            "cpu": context.params["vm"]["cpu"],
            "memory": context.params["vm"]["memory"],
            "username": context.params["vm"]["username"],
            "password": context.params["vm"]["password"],
        }
        for _, extra_params in zip_longest(range(int(count)), table, fillvalue={}):
            name = f"vm-{utils.generate_random_string(8)}"
            vm_params.update(extra_params.items())
            vm = VM(
                name=name,
                namespace=context.ns.name,
                client=context.client,
                storage_class=context.sc.name,
                inject_cloud_init=True,
                **vm_params,
            )
            vm.to_dict()
            context.vms.append(vm)
            utils.rp_attach_json(context.logger.info, f"Defined {vm.name} with manifest", f"{vm.name}.json", vm.res)

    @when("I create the VM(?:s)?")
    def create_vms(context):
        """
        Create multiple VM(s) in the cluster.
        """
        for vm in context.vms:
            vm.create(wait=True)

    @then("the VM(?:s)? status should change to Running")
    def vms_should_be_running(context):
        """
        Monitor the VirtualMachine(s) status and wait for it to reach the Running state.

        Raises:
            TimeoutExpiredError: If the VirtualMachine fails to reach 'Running' status within timeout
        """
        for vm in context.vms:
            try:
                vm.start(wait=True)
                context.logger.info(f"VirtualMachine {vm.name} is running")
            except TimeoutExpiredError:
                utils.rp_attach_json(
                    context.logger.debug,
                    f"VirtualMachine is in {vm.status} status",
                    f"{vm.name}_instance.json",
                    vm.instance.to_dict(),
                )
                raise

    @then(r"I can access the VM(?:s)?")
    def access_vm(context):
        """
        Access the VirtualMachine and verify it is running.
        """
        for vm in context.vms:
            vm.wait_for_console_login()
            vm.wait_for_ssh_login()

    @when("I perform a deletion of the VM(?:s)?")
    def delete_vms(context):
        """
        Remove the VirtualMachine(s) from the cluster and ensure deletion is finished.
        """
        for vm in context.vms:
            vm.stop(wait=True)
            vm.delete(wait=True)
            context.logger.info(f"VirtualMachine {vm.name} is deleted")

    @then("the VM(?:s)? should be completely removed")
    def vms_should_not_exist(context):
        """
        Verify that the VirtualMachine(s) have been completely removed from the system.

        Args:
            context: Behave context containing the VirtualMachine to verify

        Raises:
            AssertionError: If the VirtualMachine still exists after deletion
        """
        for vm in context.vms:
            assert not vm.exists, f"VirtualMachine '{vm.name}' still exists after deletion."
            context.logger.info(f'VirtualMachine "{vm.name}" no longer exists')
            context.vms.remove(vm)
