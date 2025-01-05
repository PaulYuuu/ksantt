from functools import wraps
from typing import Any, Callable

import paramiko
import yaml
from ocp_resources.datavolume import DataVolume
from ocp_resources.utils.constants import TIMEOUT_10MINUTES
from ocp_resources.virtual_machine import VirtualMachine
from ocp_resources.virtual_machine_instance_migration import VirtualMachineInstanceMigration
from pyhelper_utils.shell import run_command
from timeout_sampler import TimeoutExpiredError, TimeoutSampler

from utils.console import Console


class VM(VirtualMachine):
    """
    Class representing a Virtual Machine with various configurations.
    """

    def __init__(
        self,
        name,
        namespace,
        source,
        storage_class,
        url,
        access_modes=DataVolume.AccessMode.RWX,
        disk_type="virtio",
        image_pull_policy="IfNotPresent",
        size="20Gi",
        volume_mode=DataVolume.VolumeMode.BLOCK,
        cpu=1,
        cpu_sockets=None,
        cpu_cores=None,
        cpu_threads=None,
        cpu_model=None,
        cpu_placement=None,
        memory="4Gi",
        memory_guest=None,
        network_model="virtio",
        eviction_strategy=None,
        client=None,
        privileged_client=None,
        inject_cloud_init=True,
        username=None,
        password=None,
        ssh=True,
        pvc=[],
        teardown=True,
        run_strategy=VirtualMachine.RunStrategy.MANUAL,
        dry_run=None,
        node_selector=None,
        node_selector_labels=None,
    ):
        """
        Initialize the VM object with various configurations for the virtual machine.
        """
        self.name = name
        super().__init__(
            name=self.name,
            namespace=namespace,
            client=client,
            body=None,
            teardown=teardown,
            privileged_client=privileged_client,
            dry_run=dry_run,
            node_selector=node_selector,
            node_selector_labels=node_selector_labels,
        )

        # Assign additional properties here
        self.source = source
        self.url = url
        self.access_modes = access_modes
        self.volume_mode = volume_mode
        self.size = size
        self.storage_class = storage_class
        self.image_pull_policy = image_pull_policy
        self.dv = self._data_volume()
        self.disk_type = disk_type
        self.cpu = cpu
        self.cpu_sockets = cpu_sockets
        self.cpu_cores = cpu_cores
        self.cpu_threads = cpu_threads
        self.cpu_model = cpu_model
        self.cpu_placement = cpu_placement
        self.eviction_strategy = eviction_strategy
        self.memory = memory
        self.memory_guest = memory_guest
        self.inject_cloud_init = inject_cloud_init
        self.ssh = ssh
        self.network_model = network_model
        self.pvc = pvc
        self.run_strategy = run_strategy
        self.username = username
        self.password = password
        self.console = None
        if "cirros" in self.url:
            self.inject_cloud_init = False
            self.username = "cirros"
            self.password = "gocubsgo"

    def __cloudinit_data(self):
        """
        Generate the cloud-init configuration for the VM.
        """
        data = {
            "ssh_pwauth": self.ssh,
            "user": self.username,
            "password": self.password,
            "chpasswd": {"expire": False},
        }
        user_data = "#cloud-config\n" + yaml.dump(data, width=1000)
        return {"userData": user_data}

    def _data_volume(self):
        """
        Create a DataVolume object for the VM's disk.
        """
        dv = DataVolume(
            name=self.name,
            namespace=self.namespace,
            client=self.client,
            source=self.source,
            url=self.url,
            storage_class=self.storage_class,
            size=self.size,
            access_modes=self.access_modes,
            volume_mode=self.volume_mode,
        )
        dv.to_dict()
        dv.res["spec"]["imagePullPolicy"] = self.image_pull_policy
        return dv

    def to_dict(self):
        """
        Convert the VM object to a Kubernetes deployment definition.
        """
        super().to_dict()
        self.res["spec"]["runStrategy"] = self.run_strategy
        self.res["spec"]["dataVolumeTemplates"] = [self.dv.res]

        template_spec = self.res["spec"].setdefault("template", {}).setdefault("spec", {})
        domain_spec = template_spec.setdefault("domain", {})
        resources_spec = domain_spec.setdefault("resources", {})

        # Configure CPU
        cpu_spec = domain_spec.setdefault("cpu", {})
        if self.cpu:
            resources_spec.setdefault("requests", {})["cpu"] = self.cpu
        else:
            cpu_spec["sockets"] = self.cpu_sockets or 1
            cpu_spec["cores"] = self.cpu_cores or 1
            cpu_spec["threads"] = self.cpu_threads or 1
        if self.cpu_model:
            cpu_spec["model"] = self.cpu_model
        if self.cpu_placement:
            cpu_spec["dedicatedCpuPlacement"] = True

        # Configure memory
        resources_spec["requests"]["memory"] = self.memory
        if self.memory_guest:
            domain_spec["memory"] = {"guest": self.memory_guest}

        # Configure eviction strategy
        if self.eviction_strategy:
            template_spec["evictionStrategy"] = self.eviction_strategy

        # Configure devices
        devices_spec = domain_spec.setdefault("devices", {})

        # Configure disks
        disks_spec = devices_spec.setdefault("disks", [])
        volumes_spec = template_spec.setdefault("volumes", [])

        disks_spec.append(
            {
                "disk": {"bus": self.disk_type},
                "name": "rootdisk",
            }
        )
        volumes_spec.append(
            {
                "dataVolume": {"name": self.dv.name},
                "name": "rootdisk",
            }
        )
        # Configure cloud-init
        if self.inject_cloud_init:
            disks_spec.append(
                {
                    "disk": {"bus": self.disk_type},
                    "name": "cloudinitdisk",
                }
            )
            volumes_spec.append({"name": "cloudinitdisk", "cloudInitNoCloud": self.__cloudinit_data()})

        if self.pvc:
            for pvc in self.pvc:
                disks_spec.append(
                    {
                        "disk": {"bus": self.disk_type},
                        "name": pvc.name,
                    }
                )
                volumes_spec.append(
                    {
                        "persistentVolumeClaim": {"claimName": pvc.name},
                        "name": pvc.name,
                    }
                )

        # Configure network
        interfaces_spec = devices_spec.setdefault("interfaces", [])
        interfaces_spec.append({"model": self.network_model, "name": "default", "masquerade": {}})
        networks_spec = template_spec.setdefault("networks", [])
        networks_spec.append({"name": "default", "pod": {}})

    def virtctl_proxy(func: Callable[..., Any]):
        """
        Decorator to add ProxyCommand functionality for SSH connections.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            proxy_cmd = f"virtctl port-forward --stdio=true {self.name}.{self.namespace} 22"
            kwargs.setdefault("proxy_command", paramiko.ProxyCommand(proxy_cmd))
            return func(self, *args, **kwargs)

        return wrapper

    def wait_for_login(self, timeout=TIMEOUT_10MINUTES):
        """
        Wait for the VM to be ready for SSH login.
        """
        self.logger.info(f"Waiting for {self.name} to be ready for console login")
        self.console = Console(self, timeout=timeout)
        self.console.connect()

    @virtctl_proxy
    def create_session(self, proxy_command=None):
        """
        Create an SSH session for the VM.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.name,
            username=self.username,
            password=self.password,
            sock=proxy_command,
        )
        return ssh

    def cmd(self, command, session):
        """
        Execute a command on the VM using SSH.
        """
        self.logger.info(f"Execute {command} on {self.name}")
        _, stdout, stderr = session.exec_command(command)
        return_code = stdout.channel.recv_exit_status()
        stdout_str = stdout.read().decode().strip()
        stderr_str = stderr.read().decode().strip()
        return return_code, stdout_str, stderr_str

    def cmd_status(self, command, session):
        """
        Execute a command on the VM and return only the return code.
        """
        return self.cmd(command, session)[0]

    def cmd_output(self, command, session):
        """
        Execute a command on the VM and return the standard output.
        """
        return self.cmd(command, session)[1]

    def hotplug_volume(
        self,
        volume,
        disk_type=None,
        cache=None,
        serial=None,
        persist=None,
    ):
        # XXX: Define a resource dict + self.update() instead of virtctl?
        """
        Hotplug a volume to the VM.

        :param volume: The volume to hotplug.
        :param disk_type: The type of disk to use.
        :param cache: The cache mode to use.
        :param serial: The serial number to use.
        :param persist: Whether to persist the volume.
        """
        virtctl_cmd = [
            "virtctl",
            "addvolume",
            self.vmi.name,
            f"--volume-name={volume.name}",
        ]
        if cache:
            virtctl_cmd.append(f"--cache={cache}")
        if disk_type:
            virtctl_cmd.append(f"--disk-type={disk_type}")
        if serial:
            virtctl_cmd.append(f"--serial={serial}")
        if persist:
            virtctl_cmd.append("--persist")
        run_command(virtctl_cmd)

    def hotunplug_volume(self, volume, persist=None):
        # XXX: Define a resource dict + self.update_replace() instead of virtctl?
        """
        Hotunplug a volume from the VM.

        :param volume: The volume to hotunplug.
        :param persist: Whether to persist the volume.
        """
        virtctl_cmd = ["virtctl", "removevolume", self.vmi.name, f"--volume-name={volume.name}"]
        if persist:
            virtctl_cmd.append("--persist")
        run_command(virtctl_cmd)

    def migrate(self, wait=True, timeout=TIMEOUT_10MINUTES):
        """
        Migrate the VM to another node.
        """
        migration_name = f"kubevirt-migrate-{self.name}"
        with VirtualMachineInstanceMigration(
            name=migration_name,
            namespace=self.namespace,
            vmi_name=self.vmi.name,
            teardown=wait,
        ) as vmim:
            if not wait:
                return vmim

            try:
                for sample in TimeoutSampler(
                    wait_timeout=timeout,
                    sleep=5,
                    func=lambda: vmim.instance.status.phase,
                ):
                    if sample == vmim.Status.SUCCEEDED:
                        break
            except TimeoutExpiredError as exc:
                print(f"Migration failed: {exc}")
