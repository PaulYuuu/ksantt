import json


def get_disks(vm, session):
    disks = vm.cmd_output("lsblk -d -o NAME --noheadings", session).splitlines()
    return set(disks)


def get_disk_info(vm, session, disk):
    """Helper function to get the info of a disk."""
    output = vm.cmd_output(f"lsblk -d -o NAME,SERIAL -J /dev/{disk}", session)
    json_output = json.loads(output)
    return json_output["blockdevices"][0]


def get_disk_by_serial(vm, session, serial):
    """Find a disk by its serial number."""
    for disk in get_disks(vm, session):
        if get_disk_info(vm, session, disk).get("serial") == serial:
            return disk
    return None
