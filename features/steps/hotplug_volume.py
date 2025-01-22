from itertools import zip_longest

from behave import then, when
from timeout_sampler import TimeoutSampler

from utils import storage


@when(r"I hotplug (?P<count>\d+) (?P<volume_type>PVC|DV)(?:s)? to the running VM(?:s)?")
def hotplug_volume(context, count, volume_type):
    volume_type = f"{volume_type.lower()}s"
    context.hotplugged_volumes = []
    for vm in context.vms:
        vm.wait_for_console_login()
        session = vm.wait_for_ssh_login()
        disks = storage.get_disks(vm, session)
        for _ in range(int(count)):
            volume = getattr(context, volume_type).pop()
            vm.hotplug_volume(volume)

        for new_disks in TimeoutSampler(
            wait_timeout=60,
            sleep=5,
            func=storage.get_disks,
            vm=vm,
            session=session,
        ):
            if len(new_disks) == (int(count) + len(disks)):
                vm.logger.info(f"Expected {len(new_disks)} disks")
                context.hotplugged_volumes.append(new_disks - disks)
                break
        session.close()


@when(r"I hotunplug (?P<count>\d+) (?P<volume_type>PVC|DV)(?:s)? from the running VM(?:s)?")
def hotunplug_volume(context, count, volume_type):
    volume_type = f"{volume_type.lower()}s"
    context.hotplugged_volumes = []
    for vm in context.vms:
        vm.wait_for_console_login()
        session = vm.wait_for_ssh_login()
        disks = storage.get_disks(vm, session)
        for _ in range(int(count)):
            volume = getattr(context, volume_type).pop()
            vm.hotunplug_volume(volume)

        for new_disks in TimeoutSampler(
            wait_timeout=60,
            sleep=5,
            func=storage.get_disks,
            vm=vm,
            session=session,
        ):
            if len(new_disks) == (int(count) + len(disks)):
                vm.logger.info(f"Expected {len(new_disks)} disks")
                context.hotplugged_volumes.append(new_disks - disks)
                break
        session.close()


@then(r"the VM(?:s)? should be able to access the new (?:PVC|DV)(?:s)?")
def check_disks_access(context):
    for vm, disks in zip_longest(context.vms, context.hotplugged_volumes, fillvalue=set()):
        session = vm.wait_for_ssh_login()
        for disk in disks:
            vm.cmd(f"dd if=/dev/{disk} of=/dev/null bs=1M count=10", session)
        session.close()
