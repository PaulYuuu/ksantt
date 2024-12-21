from behave import given, then, when
from behave.runner import Context
from timeout_sampler import TimeoutExpiredError

import utils
from utils import rp_attach_json
from utils.vm import VM


@given("a VM with {cpu:d} vCPUs and {memory} memory")
def step_define_vm(context: Context, cpu: int, memory: str):
    """
    Define a VirtualMachine with specified CPU and memory resources.

    Args:
        context (Context): The Behave context object containing test configuration and state
        cpu (int): Number of virtual CPUs to allocate to the VM
        memory (str): Amount of memory to allocate to the VM (e.g., '2Gi', '512Mi')

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
    context.vm = vm
    if context.rph:
        vm.logger.addHandler(context.rph)
    vm.to_dict()
    context.vm = vm
    utils.rp_attach_json(context.log.info, "Defined VirtualMachine with manifest", "vm.json", vm.res)


@when("I create a VM")
def create_vm(context: Context):
    """Test creating a VirtualMachine in the dynamically created test namespace"""
    # Create the VirtualMachine in the test namespace
    context.vm.create(wait=True)


@then("the VM should be in Running phase")
def vm_should_be_running(context: Context):
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


@when("I delete the VM")
def delete_vm(context: Context):
    """Delete the VirtualMachine."""
    context.vm.stop(wait=True)
    context.vm.delete(wait=True)
    context.log.info(f"VirtualMachine {context.vm.name} is deleted")


@then("the VM should not exist")
def vm_should_not_exist(context: Context):
    """Verify that the VirtualMachine no longer exists."""
    assert not context.vm.exists, f"VirtualMachine '{context.vm.name}' still exists after deletion."
    context.log.info(f'VirtualMachine "{context.vm.name}" no longer exists')
