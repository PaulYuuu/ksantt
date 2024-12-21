from functools import wraps

import paramiko
import yaml
from ocp_resources.constants import TIMEOUT_10MINUTES
from ocp_resources.datavolume import DataVolume
from ocp_resources.virtual_machine import VirtualMachine
from ocp_resources.virtual_machine_instance_migration import VirtualMachineInstanceMigration
from timeout_sampler import TimeoutExpiredError, TimeoutSampler


class VM(VirtualMachine):
    def __init__(
        self,
        name,
        namespace,
        # Storage
        source,
        storage_class,
        url,
        access_modes=DataVolume.AccessMode.RWX,
        disk_type="virtio",
        image_pull_policy="IfNotPresent",
        size="20Gi",
        volume_mode=DataVolume.VolumeMode.BLOCK,
        # CPU
        cpu_flags=None,
        cpu_sockets=None,
        cpu_cores=None,
        cpu_threads=None,
        cpu_model=None,
        cpu_max_sockets=None,
        cpu_placement=None,
        # memory
        memory_guest=None,
        # network
        network_model="virtio",
        # misc
        eviction_strategy=None,
        client=None,
        node_selector=None,
        privileged_client=None,
        # cloud-init
        inject_cloud_init=False,
        username=None,
        password=None,
        ssh=True,
        pvc=None,
        teardown=True,
        run_strategy=VirtualMachine.RunStrategy.ALWAYS,
        dry_run=None,
        node_selector_labels=None,
    ):
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
        self.source = source
        self.url = url
        self.access_modes = access_modes
        self.volume_mode = volume_mode
        self.size = size
        self.storage_class = storage_class
        self.data_volume = self._data_volume()
        self.disk_type = disk_type
        self.cpu_flags = cpu_flags
        self.cpu_sockets = cpu_sockets
        self.cpu_cores = cpu_cores
        self.cpu_threads = cpu_threads
        self.cpu_model = cpu_model
        self.cpu_max_sockets = cpu_max_sockets
        self.cpu_placement = cpu_placement
        self.eviction_strategy = eviction_strategy
        # memory
        self.memory_guest = memory_guest
        # cloud-init
        self.inject_cloud_init = inject_cloud_init
        self.ssh = ssh
        self.network_model = network_model
        self.pvc = pvc
        self.run_strategy = run_strategy
        self.username = username
        self.password = password

    def __cloudinit_data(self):
        data = {
            "ssh_pwauth": self.ssh,
            "user": self.username,
            "password": self.password,
            "chpasswd": {"expire": False},
        }
        user_data = "#cloud-config\n" + yaml.dump(data, width=1000)
        return {"userData": user_data}

    def to_dict(self):
        super().to_dict()
        self.res["spec"]["runStrategy"] = self.run_strategy
        self.res["spec"]["dataVolumeTemplates"] = [self.data_volume.res]

        template_spec = self.res["spec"]["template"]["spec"]
        if self.eviction_strategy:
            template_spec["evictionStrategy"] = self.eviction_strategy
        # CPU
        cpu_spec = template_spec.setdefault("domain", {}).setdefault("cpu", {})
        if self.cpu_flags:
            cpu_spec["model"] = self.cpu_flags
        if self.cpu_sockets:
            cpu_spec["sockets"] = self.cpu_sockets
        if self.cpu_cores:
            cpu_spec["cores"] = self.cpu_cores
        if self.cpu_threads:
            cpu_spec["threads"] = self.cpu_threads
        if self.cpu_model:
            cpu_spec["model"] = self.cpu_model
        if self.cpu_max_sockets:
            cpu_spec["maxSockets"] = self.cpu_max_sockets
        if self.cpu_placement:
            cpu_spec["dedicatedCpuPlacement"] = True
        # Memory
        memory_spec = template_spec.setdefault("domain", {}).setdefault("memory", {})
        if self.memory_guest:
            memory_spec["guest"] = self.memory_guest
        # Devices
        devices_spec = template_spec.setdefault("domain", {}).setdefault("devices", {})
        volumes_spec = template_spec.setdefault("volumes", [])
        # Disks
        disks_spec = devices_spec.setdefault("disks", [])
        disks_spec.append({
            "disk": {"bus": self.disk_type},
            "name": "rootdisk",
        })
        volumes_spec.append({
            "name": "rootdisk",
            "dataVolume": {"name": self.data_volume.name},
        })
        if self.inject_cloud_init:
            disks_spec.append({
                "disk": {"bus": self.disk_type},
                "name": "cloudinitdisk",
            })
            volumes_spec.append({
                "name": "cloudinitdisk",
                "cloudInitNoCloud": self.__cloudinit_data(),
            })
        # Network
        interfaces_spec = devices_spec.setdefault("interfaces", [])
        interfaces_spec.append({"model": self.network_model, "name": "default", "masquerade": {}})
        networks_spec = template_spec.setdefault("networks", [])
        networks_spec.append({"name": "default", "pod": {}})

    def _data_volume(self):
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
        return dv

    def proxy_command(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            proxy_cmd = f"virtctl port-forward --stdio=true {self.name}.{self.namespace} 22"
            kwargs["proxy_command"] = paramiko.ProxyCommand(proxy_cmd)
            return func(self, *args, **kwargs)
        return wrapper

    @proxy_command
    def cmd(self, command, proxy_command=None):
        """Execute command on the VM using SSH with ProxyCommand.

        Args:
            command: Command to execute
            proxy_command: ProxyCommand instance (injected by decorator)

        Returns:
            tuple: (return_code, stdout, stderr)
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
        return self.cmd(command)[0]

    def cmd_output(self, command):
        return self.cmd(command)[1]

    def migrate(self, wait=True, timeout=TIMEOUT_10MINUTES):
        """Migrate the VM to another node.

        Args:
            wait: Wait for migration to complete
            timeout: Timeout for migration completion

        Returns:
            VMIMigration object if wait=False, None otherwise
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
