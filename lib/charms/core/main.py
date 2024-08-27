import subprocess
import shutil
from pydantic import ValidationError

import os
import ops


# These use the raw hook tools because by the time we catch the
# exit we don't have the model or backend around any more. We
# could force people to pass the event and charm instance into the
# parse functions instead.
def _exit_with_blocked_status(e):
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "check": True,
        "encoding": "utf-8",
    }
    which_cmd = shutil.which("status-set")
    args = (which_cmd, "--application=False", "blocked", str(e))
    subprocess.run(args, **kwargs)


def _exit_with_failed_action(e):
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "check": True,
        "encoding": "utf-8",
    }
    which_cmd = shutil.which("action-fail")
    args = (which_cmd, str(e))
    subprocess.run(args, **kwargs)


# An alternative to this would be to have the error handling in the various
# parse functions, and then do a sys.exit(0) afterwards, if we confirm that
# there's nothing else that needs to be tidied up. Obviously, if this was in
# ops itself we could do it much more cleanly.
def main(*args, **kwargs):
    # Note: it would be nicer if ops had some sort of built-in support for this.
    try:
        ops.main(*args, **kwargs)
    except ValidationError as e:
        # TODO: There might be other cleanup that should still be done.
        if "JUJU_ACTION_NAME" in os.environ:
            # Don't put the unit into error state, but set the action as failed.
            _exit_with_failed_action(e)
        else:
            # Don't put the unit into error state, but set a blocked status.
            _exit_with_blocked_status(e)