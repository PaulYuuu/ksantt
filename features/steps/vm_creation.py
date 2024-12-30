from behave import given, then, when
from behave.runner import Context
from timeout_sampler import TimeoutExpiredError

import utils
from utils import rp_attach_json
from utils.vm import VM


@given("a VM specification with {cpu:d} vCPUs and {memory} memory")
def step_define_vm(context: Context, cpu: int, memory: str):
    """
    Define a new VirtualMachine object with the given configuration parameters.

    Args:
        context: Behave context containing test configuration and resources
        cpu: Number of virtual CPUs to allocate to the VirtualMachine
        memory: Amount of memory to allocate to the VirtualMachine (e.g., '2Gi', '512Mi')
    """
    vm_name = f"vm-{cpu}-{memory.lower()}"
    url = context.config.userdata["image_url"]
    size = context.config.userdata["image_size"]
    source = context.config.userdata["image_source"]
    vm_username = context.config.userdata["vm_username"]
    vm_password = context.config.userdata["vm_password"]

    vm = VM(
        name=vm_name,
        namespace=context.ns.name,
        client=context.client,
        source=source,
        storage_class=context.sc.name,
        url=url,
        size=size,
        cpu=cpu,
        memory=memory,
        inject_cloud_init=False,
        username=vm_username,
        password=vm_password,
    )
    if context.rph:
        vm.logger.addHandler(context.rph)
    vm.to_dict()
    context.vm = vm
    utils.rp_attach_json(context.log.info, "Defined VirtualMachine with manifest", "vm.json", vm.res)


@when("I create the VM")
def create_vm(context: Context):
    """
    Create a new VirtualMachine instance in the cluster using the predefined specification.

    Args:
        context: Behave context containing the VirtualMachine object to be created
    """
    context.vm.create(wait=True)


@then("the VM status should change to Running")
def vm_should_be_running(context: Context):
    """
    Monitor the VirtualMachine status and wait for it to reach the Running state.

    Args:
        context: Behave context containing the VirtualMachine to verify

    Raises:
        TimeoutExpiredError: If the VirtualMachine fails to reach 'Running' status within timeout
    """
    try:
        context.vm.start(wait=True)
        context.log.info(f"VirtualMachine {context.vm.name} is running")
    except TimeoutExpiredError:
        rp_attach_json(
            context.log.debug,
            f"VirtualMachine is in {context.vm.status} status",
            "vm.json",
            context.vm.instance.to_dict(),
        )
        raise


@when("I perform a deletion of the VM")
def delete_vm(context: Context):
    """
    Remove the VirtualMachine from the cluster and ensure deletion is finished.

    Args:
        context: Behave context containing the VirtualMachine to delete
    """
    context.vm.stop(wait=True)
    context.vm.delete(wait=True)
    context.log.info(f"VirtualMachine {context.vm.name} is deleted")


@then("the VM should be completely removed")
def vm_should_not_exist(context: Context):
    """
    Verify that the VirtualMachine has been completely removed from the system.

    Args:
        context: Behave context containing the VirtualMachine to verify

    Raises:
        AssertionError: If the VirtualMachine still exists after deletion
    """
    assert not context.vm.exists, f"VirtualMachine '{context.vm.name}' still exists after deletion."
    context.log.info(f'VirtualMachine "{context.vm.name}" no longer exists')
