import logging

import pexpect
from timeout_sampler import TimeoutSampler

LOGGER = logging.getLogger(__name__)


class Console(object):
    def __init__(self, vm, username=None, password=None, timeout=30, prompt=None):
        """
        Initialize a VM console connection.
        """
        self.vm = vm
        self.username = username or self.vm.login_params["username"]
        self.password = password or self.vm.login_params["password"]
        self.timeout = timeout
        self.child = None
        self.login_prompt = "login:"
        self.prompt = prompt if prompt else [r"\$"]
        self.cmd = self._generate_cmd()

    def connect(self):
        """
        Connect to the VM console.
        """
        LOGGER.info(f"Connect to {self.vm.name} console")
        self.console_eof_sampler(func=pexpect.spawn, command=self.cmd, timeout=self.timeout)

        self._connect()

        return self.child

    def _connect(self):
        """
        Handle login sequence for VM console connection.
        """
        self.child.send("\n\n")
        if self.username:
            self.child.expect(self.login_prompt, timeout=360)
            LOGGER.info(f"{self.vm.name}: Using username {self.username}")
            self.child.sendline(self.username)
            if self.password:
                self.child.expect("Password:")
                LOGGER.info(f"{self.vm.name}: Using password {self.password}")
                self.child.sendline(self.password)

        self.child.expect(self.prompt, timeout=150)
        LOGGER.info(f"{self.vm.name}: Got prompt {self.prompt}")

    def disconnect(self):
        """
        Disconnect from the VM console.
        """
        if self.child.terminated:
            self.console_eof_sampler(func=pexpect.spawn, command=self.cmd, timeout=self.timeout)

        self.child.send("\n\n")
        self.child.expect(self.prompt)
        if self.username:
            self.child.send("exit")
            self.child.send("\n\n")
            self.child.expect("login:")
        self.child.close()

    def force_disconnect(self):
        """
        Force disconnect from VM console. Workaround for RHEL 7.7.
        """
        self.console_eof_sampler(func=pexpect.spawn, command=self.cmd, timeout=self.timeout)
        self.disconnect()

    def console_eof_sampler(self, func, command, timeout):
        """
        Sample console EOF with timeout handling.
        """
        sampler = TimeoutSampler(
            wait_timeout=360,
            sleep=5,
            func=func,
            exceptions_dict={pexpect.exceptions.EOF: []},
            command=command,
            timeout=timeout,
            encoding="utf-8",
        )
        for sample in sampler:
            if sample:
                self.child = sample
                self.child.logfile = open(f"{self.base_dir}/{self.vm.name}.pexpect.log", "a")
                break

    def _generate_cmd(self):
        """
        Generate virtctl console command.
        """
        cmd = f"virtctl console {self.vm.name}"
        if self.vm.namespace:
            cmd += f" -n {self.vm.namespace}"
        return cmd

    def __enter__(self):
        """
        Connect to console on context enter.
        """
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Disconnect from console on context exit.
        """
        self.disconnect()
