from functools import wraps
from typing import Any, Callable

import paramiko
import yaml
from ocp_resources.constants import TIMEOUT_10MINUTES
from ocp_resources.datavolume import DataVolume
from ocp_resources.virtual_machine import VirtualMachine
from ocp_resources.virtual_machine_instance_migration import VirtualMachineInstanceMigration
from timeout_sampler import TimeoutExpiredError, TimeoutSampler


class VM(VirtualMachine):
    """
    Class representing a Virtual Machine (VM) with various configurations for storage,
    CPU, memory, network, and cloud-init data. Inherits from the `VirtualMachine` class.
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

        Args:
            name (str): The name of the VM.
            namespace (str): The namespace for the VM.
            source (str): The source for the data volume.
            storage_class (str): The storage class for the PVC.
            url (str): The URL for the storage source.
            access_modes (str): The access modes for the data volume.
            disk_type (str): The disk type (e.g., virtio).
            image_pull_policy (str): The image pull policy.
            size (str): The size of the data volume.
            volume_mode (str): The volume mode for the PVC.
            cpu (int): The number of CPUs to allocate.
            cpu_sockets (int): The number of CPU sockets.
            cpu_cores (int): The number of CPU cores.
            cpu_threads (int): The number of CPU threads.
            cpu_model (str): The CPU model.
            cpu_placement (bool): Whether to enable CPU placement.
            memory (str): The memory size for the VM.
            memory_guest (str): The guest memory size.
            network_model (str): The network model (e.g., virtio).
            eviction_strategy (str): The eviction strategy for the VM.
            client (object): The Kubernetes client.
            privileged_client (object): The privileged client.
            inject_cloud_init (bool): Whether to inject cloud-init data.
            username (str): The SSH username.
            password (str): The SSH password.
            ssh (bool): Whether to enable SSH for the VM.
            pvc (list): A list of PVCs to attach to the VM.
            teardown (bool): Whether to tear down the VM when done.
            run_strategy (str): The run strategy for the VM.
            dry_run (bool): Whether to perform a dry run.
            node_selector (dict): The node selector for scheduling.
            node_selector_labels (dict): The labels for node selection.
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
        self.data_volume = self._data_volume()
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

    def __cloudinit_data(self):
        """
        Generate the cloud-init configuration for the VM.

        Returns:
            dict: Cloud-init user data including SSH and user credentials.
        """
        data = {
            "ssh_pwauth": self.ssh,
            "user": self.username,
            "password": self.password,
            "chpasswd": {"expire": False},
        }
        user_data = "#cloud-config\n" + yaml.dump(data, width=1000)
        return {"userData": user_data}

    def to_dict(self):
        """
        Convert the VM object to a dictionary representation for Kubernetes deployment.

        Returns:
            dict: The Kubernetes deployment definition of the VM.
        """
        super().to_dict()
        self.res["spec"]["runStrategy"] = self.run_strategy
        self.res["spec"]["dataVolumeTemplates"] = [self.data_volume.res]

        template_spec = self.res["spec"].setdefault("template", {}).setdefault("spec", {})
        resources_spec = template_spec.setdefault("domain", {}).setdefault("resources", {})
        if self.eviction_strategy:
            template_spec["evictionStrategy"] = self.eviction_strategy

        # CPU specifications
        cpu_spec = template_spec.setdefault("domain", {}).setdefault("cpu", {})
        if self.cpu:
            resources_spec.setdefault("requests", {})["cpu"] = self.cpu
        else:
            cpu_spec["sockets"] = self.cpu_sockets
            cpu_spec["cores"] = self.cpu_cores
            cpu_spec["threads"] = self.cpu_threads
        if self.cpu_model:
            cpu_spec["model"] = self.cpu_model
        if self.cpu_placement:
            cpu_spec["dedicatedCpuPlacement"] = True

        # Memory specifications
        memory_spec = template_spec.setdefault("domain", {}).setdefault("memory", {})
        if self.memory:
            resources_spec.setdefault("requests", {})["memory"] = self.memory
        else:
            memory_spec["guest"] = self.memory_guest

        # Disk and volume specifications
        devices_spec = template_spec.setdefault("domain", {}).setdefault("devices", {})
        volumes_spec = template_spec.setdefault("volumes", [])
        disks_spec = devices_spec.setdefault("disks", [])
        disks_spec.append(
            {
                "disk": {"bus": self.disk_type},
                "name": "rootdisk",
            }
        )
        volumes_spec.append(
            {
                "name": "rootdisk",
                "dataVolume": {"name": self.data_volume.name},
            }
        )
        if self.inject_cloud_init:
            disks_spec.append(
                {
                    "disk": {"bus": self.disk_type},
                    "name": "cloudinitdisk",
                }
            )
            volumes_spec.append(
                {
                    "name": "cloudinitdisk",
                    "cloudInitNoCloud": self.__cloudinit_data(),
                }
            )
        for pvc in self.pvc:
            disks_spec.append(
                {
                    "disk": {"bus": self.disk_type},
                    "name": pvc.name,
                }
            )
            volumes_spec.append(
                {
                    "name": pvc.name,
                    "persistentVolumeClaim": {"claimName": pvc.name},
                }
            )

        # Network specifications
        interfaces_spec = devices_spec.setdefault("interfaces", [])
        interfaces_spec.append({"model": self.network_model, "name": "default", "masquerade": {}})
        networks_spec = template_spec.setdefault("networks", [])
        networks_spec.append({"name": "default", "pod": {}})

    def _data_volume(self):
        """
        Create a DataVolume object for the VM's disk.

        Returns:
            DataVolume: The created DataVolume object.
        """
        dv = DataVolume(
            name=self.name,
            namespace=self.namespace,
            client=self.client,
            source=self.source,
            url=self.url,
            storage_class=self.storage_class,
            access_modes=self.access_modes,
            volume_mode=self.volume_mode,
            size=self.size,
        )
        dv.to_dict()
        dv.res["spec"]["imagePullPolicy"] = self.image_pull_policy
        return dv

    def proxy_command(func: Callable[..., Any]):
        """
        Decorator to add ProxyCommand functionality for SSH connections.

        Args:
            func: The function to wrap with ProxyCommand.

        Returns:
            function: The wrapped function with ProxyCommand injected.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            proxy_cmd = f"virtctl port-forward --stdio=true {self.name}.{self.namespace} 22"
            kwargs.setdefault("proxy_command", paramiko.ProxyCommand(proxy_cmd))
            return func(self, *args, **kwargs)

        return wrapper

    @proxy_command
    def cmd(self, command, proxy_command=None):
        """
        Execute a command on the VM using SSH with ProxyCommand.

        Args:
            command (str): The command to execute on the VM.
            proxy_command (paramiko.ProxyCommand): The ProxyCommand to use for SSH.

        Returns:
            tuple: A tuple containing the return code, standard output, and standard error.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        with ssh:
            ssh.connect(
                hostname=self.name,
                username=self.username,
                password=self.password,
                sock=proxy_command,
            )
            _, stdout, stderr = ssh.exec_command(command)
            return_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode().strip()
            stderr_str = stderr.read().decode().strip()
            return return_code, stdout_str, stderr_str

    def cmd_status(self, command):
        """
        Execute a command on the VM and return only the return code.

        Args:
            command (str): The command to execute.

        Returns:
            int: The return code from the command execution.
        """
        return self.cmd(command)[0]

    def cmd_output(self, command):
        """
        Execute a command on the VM and return the standard output.

        Args:
            command (str): The command to execute.

        Returns:
            str: The standard output from the command execution.
        """
        return self.cmd(command)[1]

    def migrate(self, wait=True, timeout=TIMEOUT_10MINUTES):
        """
        Migrate the VM to another node.

        Args:
            wait (bool): Whether to wait for the migration to complete.
            timeout (int): Timeout for the migration process.

        Returns:
            VirtualMachineInstanceMigration: The migration object if `wait` is False, otherwise None.
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
