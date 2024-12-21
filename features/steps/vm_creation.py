from behave import given, then, when
from behave.runner import Context
from timeout_sampler import TimeoutExpiredError

import utils
from utils.exceptions import BehaveStepError
from utils.vm import VM


@given("a VM with {cpu} vCPUs and {memory} memory")
def step_define_vm(context: Context, cpu: str, memory: str):
    vm_name = f"vm-{cpu}-{memory}"
    vm = VM(
        name=vm_name,
        namespace=context.ns.name,
        client=context.client,
        cpu=cpu,
        memory=memory,
    )
    context.vm = vm
