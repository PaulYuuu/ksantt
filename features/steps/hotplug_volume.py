from behave import then, when
from behave.runner import Context


@when(r"I hotplug the PVC to the running VM(?:s)?")
def hotplug_pvc(context: Context):
    pass


@then(r"the PVC should be successfully attached to the VM(?:s)?")
def check_pvc_attached(context: Context):
    pass


@then(r"the VM(?:s)? should detect the new storage device")
def check_vm_device(context: Context):
    pass


@then(r"the VM(?:s)? should be able to access the new storage device")
def check_vm_access(context: Context):
    pass
