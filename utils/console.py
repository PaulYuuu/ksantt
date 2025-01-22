import pexpect
from timeout_sampler import TimeoutSampler


class Console(object):
    def __init__(self, vm, username=None, password=None, timeout=30, prompt=None):
        """
        Initialize a VM console connection.
        """
        self.vm = vm
        self.username = username or self.vm.username
        self.password = password or self.vm.password
        self.timeout = timeout
        self.child = None
        self.login_prompt = "login:"
        self.prompt = prompt if prompt else [r"\$"]
        self.cmd = self._generate_cmd()

    def connect(self):
        """
        Connect to the VM console.
        """
        self.vm.logger.info(f"Connect to {self.vm.name} console")
        self.console_eof_sampler(func=pexpect.spawn, command=self.cmd, timeout=self.timeout)

        self._connect()

        return self.child

    def _connect(self):
        """
        Handle login sequence for VM console connection.
        Note: cirros and alpine have some problem with password prompt.
        """
        self.child.send("\n\n")
        self.child.expect(self.login_prompt, timeout=360)
        self.vm.logger.info(f"{self.vm.name}: Using username {self.username}")
        self.child.sendline(self.username)
        if self.password:
            self.vm.logger.info(f"{self.vm.name}: Using password {self.password}")
            self.child.sendline(self.password)

        self.child.expect(self.prompt, timeout=150)
        self.vm.logger.info(f"{self.vm.name}: Got prompt {self.prompt}")

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

    def console_eof_sampler(self, func, command, timeout):
        """
        Sample console EOF with timeout handling.
        """
        sampler = TimeoutSampler(
            wait_timeout=360,
            sleep=10,
            func=func,
            exceptions_dict={
                pexpect.exceptions.EOF: [],
                UnicodeDecodeError: [],
            },
            command=command,
            timeout=timeout,
            encoding="utf-8",
        )
        for sample in sampler:
            if sample:
                self.child = sample
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
