import json
import hashlib
import logging
from shlex import quote
import os
import subprocess
import sys

from ray.autoscaler._private.subprocess_output_util import (
    ProcessRunnerError,
    is_output_redirected,
    run_cmd_redirected,
)


HASH_MAX_LENGTH = 10


# dd-mmm-yyyy hh:mm:ss.000
formatter = logging.Formatter(
    fmt='[%(name)s] %(asctime)s.%(msecs)03d %(levelname)s %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S')


def setup_logger(name, log_file, level=logging.INFO):
    """
    Create logger instance
    """
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(consoleHandler)

    return logger


_config = {"use_login_shells": True, "silent_rsync": True}


def is_rsync_silent():
    return _config["silent_rsync"]

def is_using_login_shells():
    return _config["use_login_shells"]


def _with_environment_variables(cmd: str, environment_variables):
    """Prepend environment variables to a shell command.

    Args:
        cmd: The base command.
        environment_variables (Dict[str, object]): The set of environment
            variables. If an environment variable value is a dict, it will
            automatically be converted to a one line yaml string.
    """

    as_strings = []
    for key, val in environment_variables.items():
        val = json.dumps(val, separators=(",", ":"))
        s = "export {}={};".format(key, quote(val))
        as_strings.append(s)
    all_vars = "".join(as_strings)
    return all_vars + cmd


def _with_interactive(cmd):
    force_interactive = (
        f"source ~/.bashrc; "
        f"export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore && ({cmd})"
    )
    return ["bash", "--login", "-c", "-i", quote(force_interactive)]


class SSHOptions:
    def __init__(self, ssh_key, control_path=None, **kwargs):
        self.ssh_key = ssh_key
        self.arg_dict = {
            # Supresses initial fingerprint verification.
            "StrictHostKeyChecking": "no",
            # SSH IP and fingerprint pairs no longer added to known_hosts.
            # This is to remove a "REMOTE HOST IDENTIFICATION HAS CHANGED"
            # warning if a new node has the same IP as a previously
            # deleted node, because the fingerprints will not match in
            # that case.
            "UserKnownHostsFile": os.devnull,
            # Try fewer extraneous key pairs.
            "IdentitiesOnly": "yes",
            # Abort if port forwarding fails (instead of just printing to
            # stderr).
            "ExitOnForwardFailure": "yes",
            # Quickly kill the connection if network connection breaks (as
            # opposed to hanging/blocking).
            "ServerAliveInterval": 5,
            "ServerAliveCountMax": 3,
        }
        if control_path:
            self.arg_dict.update(
                {
                    "ControlMaster": "auto",
                    "ControlPath": "{}/%C".format(control_path),
                    "ControlPersist": "10s",
                }
            )
        self.arg_dict.update(kwargs)

    def to_ssh_options_list(self, *, timeout=60):
        self.arg_dict["ConnectTimeout"] = "{}s".format(timeout)
        ssh_key_option = ["-i", self.ssh_key] if self.ssh_key else []
        return ssh_key_option + [
            x
            for y in (
                ["-o", "{}={}".format(k, v)]
                for k, v in self.arg_dict.items()
                if v is not None
            )
            for x in y
        ]



class SSHCommandRunner():
    def __init__(
        self,
        ip,
        logger,
        log_prefix,
        node_id,
        provider,
        auth_config,
        cluster_name,
        process_runner,
        use_internal_ip,
    ):

        ssh_control_hash = hashlib.md5(cluster_name.encode()).hexdigest()
        ssh_user_hash = hashlib.md5('weit'.encode()).hexdigest()
        ssh_control_path = "/tmp/ray_ssh_{}/{}".format(
            ssh_user_hash[:HASH_MAX_LENGTH], ssh_control_hash[:HASH_MAX_LENGTH]
        )

        self.cluster_name = cluster_name
        self.log_prefix = log_prefix
        self.logger = logger
        self.process_runner = subprocess
        self.node_id = node_id
        self.use_internal_ip = use_internal_ip
        self.provider = provider
        self.ssh_private_key = auth_config.get("ssh_private_key")
        self.ssh_user = auth_config["ssh_user"]
        self.ssh_control_path = ssh_control_path
        self.ssh_ip = ip
        self.ssh_proxy_command = auth_config.get("ssh_proxy_command", None)
        self.ssh_options = SSHOptions(
            self.ssh_private_key,
            self.ssh_control_path,
            ProxyCommand=self.ssh_proxy_command,
        )

    def _set_ssh_ip_if_required(self):
        # This should run before any SSH commands and therefore ensure that
        #   the ControlPath directory exists, allowing SSH to maintain
        #   persistent sessions later on.
        try:
            os.makedirs(self.ssh_control_path, mode=0o700, exist_ok=True)
        except OSError as e:
            self.logger.error("%s" % str(e))  # todo: msg


    def _run_helper(
        self, final_cmd, with_output=False, exit_on_fail=False, silent=False
    ):
        """Run a command that was already setup with SSH and `bash` settings.

        Args:
            cmd (List[str]):
                Full command to run. Should include SSH options and other
                processing that we do.
            with_output (bool):
                If `with_output` is `True`, command stdout will be captured and
                returned.
            exit_on_fail (bool):
                If `exit_on_fail` is `True`, the process will exit
                if the command fails (exits with a code other than 0).

        Raises:
            ProcessRunnerError if using new log style and disabled
                login shells.
            click.ClickException if using login shells.
        """
        try:
            # For now, if the output is needed we just skip the new logic.
            # In the future we could update the new logic to support
            # capturing output, but it is probably not needed.
            if not with_output:
                return run_cmd_redirected(
                    final_cmd,
                    process_runner=self.process_runner,
                    silent=silent,
                    use_login_shells=is_using_login_shells(),
                )
            else:
                return self.process_runner.check_output(final_cmd)
        except subprocess.CalledProcessError as e:
            joined_cmd = " ".join(final_cmd)
            if not is_using_login_shells():
                raise ProcessRunnerError(
                    "Command failed",
                    "ssh_command_failed",
                    code=e.returncode,
                    command=joined_cmd,
                )

            if exit_on_fail:
                raise Exception(
                    "Command failed:\n\n  {}\n".format(joined_cmd)
                ) from None
            else:
                fail_msg = "SSH command failed."
                if is_output_redirected():
                    fail_msg += " See above for the output from the failure."
                raise Exception(fail_msg) from None
        finally:
            # Do our best to flush output to terminal.
            # See https://github.com/ray-project/ray/pull/19473.
            sys.stdout.flush()
            sys.stderr.flush()

    def run(
        self,
        cmd,
        timeout=120,
        exit_on_fail=False,
        port_forward=None,
        with_output=False,
        environment_variables = None,
        run_env="auto",  # Unused argument.
        ssh_options_override_ssh_key="",
        shutdown_after_run=False,
        silent=False,
    ):
        if shutdown_after_run:
            cmd += "; sudo shutdown -h now"

        if ssh_options_override_ssh_key:
            if self.ssh_proxy_command:
                ssh_options = SSHOptions(
                    ssh_options_override_ssh_key, ProxyCommand=self.ssh_proxy_command
                )
            else:
                ssh_options = SSHOptions(ssh_options_override_ssh_key)
        else:
            ssh_options = self.ssh_options

        assert isinstance(
            ssh_options, SSHOptions
        ), "ssh_options must be of type SSHOptions, got {}".format(type(ssh_options))

        self._set_ssh_ip_if_required()

        if is_using_login_shells():
            ssh = ["ssh", "-tt"]
        else:
            ssh = ["ssh"]

        final_cmd = (
            ssh
            + ssh_options.to_ssh_options_list(timeout=timeout)
            + ["{}@{}".format(self.ssh_user, self.ssh_ip)]
        )
        if cmd:
            if environment_variables:
                cmd = _with_environment_variables(cmd, environment_variables)
            if is_using_login_shells():
                final_cmd += _with_interactive(cmd)
            else:
                final_cmd += [cmd]
        else:
            # We do this because `-o ControlMaster` causes the `-N` flag to
            # still create an interactive shell in some ssh versions.
            final_cmd.append("while true; do sleep 86400; done")

        self.logger.info("Running `%s`" % cmd)
        self.logger.debug(
            "Full command is `%s`" % " ".join(final_cmd))

        return self._run_helper(final_cmd, with_output, exit_on_fail, silent=silent)

    def _create_rsync_filter_args(self, options):
        rsync_excludes = options.get("rsync_exclude") or []
        rsync_filters = options.get("rsync_filter") or []

        exclude_args = [
            ["--exclude", rsync_exclude] for rsync_exclude in rsync_excludes
        ]
        filter_args = [
            ["--filter", "dir-merge,- {}".format(rsync_filter)]
            for rsync_filter in rsync_filters
        ]

        # Combine and flatten the two lists
        return [arg for args_list in exclude_args + filter_args for arg in args_list]

    def run_rsync_up(self, source, target, options=None):
        self._set_ssh_ip_if_required()
        options = options or {}

        command = ["rsync"]
        command += [
            "--rsh",
            subprocess.list2cmdline(
                ["ssh"] + self.ssh_options.to_ssh_options_list(timeout=120)
            ),
        ]
        command += ["-avz"]
        command += self._create_rsync_filter_args(options=options)
        command += [source, "{}@{}:{}".format(self.ssh_user, self.ssh_ip, target)]
        self.logger.info("Running `%s`" % " ".join(command))
        self._run_helper(command, silent=is_rsync_silent())

    def run_rsync_down(self, source, target, options=None):
        self._set_ssh_ip_if_required()

        command = ["rsync"]
        command += [
            "--rsh",
            subprocess.list2cmdline(
                ["ssh"] + self.ssh_options.to_ssh_options_list(timeout=120)
            ),
        ]
        command += ["-avz"]
        command += self._create_rsync_filter_args(options=options)
        command += ["{}@{}:{}".format(self.ssh_user, self.ssh_ip, source), target]
        self.logger.info("Running `%s`" % " ".join(command))
        self._run_helper(command, silent=is_rsync_silent())

    def remote_shell_command_str(self):
        if self.ssh_private_key:
            return "ssh -o IdentitiesOnly=yes -i {} {}@{}\n".format(
                self.ssh_private_key, self.ssh_user, self.ssh_ip
            )
        else:
            return "ssh -o IdentitiesOnly=yes {}@{}\n".format(
                self.ssh_user, self.ssh_ip
            )


def main():
    cli_logger = setup_logger('ssh-test', 'ssh-test.log', level=logging.DEBUG)
    auth_config = {
        'ssh_user': 'sky',
        'ssh_private_key': '~/.ssh/sky-key',
        'ssh_proxy_command': 'ssh -tt -i ~/.ssh/sky-key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o IdentitiesOnly=yes  -p 30022 -W %h:%p sky@172.31.3.2',
        'ssh_public_key': '~/.ssh/sky-key.pub'
        
    }

    common_args = {
        "logger": cli_logger,
        "ip": "10.244.1.232",
        "log_prefix": 'prefix',
        "node_id": '123',
        "provider": None,
        "auth_config": auth_config,
        "cluster_name": 'cluster',
        "process_runner": subprocess,
        "use_internal_ip": True
    }
    command_runner = SSHCommandRunner(**common_args)
    command_runner.run("uptime", timeout=10, run_env="host")
    
if __name__ == "__main__":
    main()
