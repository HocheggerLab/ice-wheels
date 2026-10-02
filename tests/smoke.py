"""Import-level check for a freshly installed zeroc-ice wheel.

Runs without an OMERO server: it proves the compiled extension loads, reports
the expected Ice version, and that omero-py can build a client and a
communicator on top of it.
"""

import platform
import sys
import sysconfig
from importlib import metadata

import Ice
import omero
import omero.gateway  # noqa: F401  (import is the test)

EXPECTED_ICE_VERSION = "3.6.5"


def main() -> int:
    """Check the Ice extension and omero-py client construction.

    Returns:
        Process exit code: 0 on success, 1 on a version or interpreter mismatch.
    """
    version = Ice.stringVersion()
    print(
        f"Python {sys.version.split()[0]} ({platform.machine()}), "
        f"Ice {version}, omero-py {metadata.version('omero-py')}"
    )
    if sysconfig.get_config_var("Py_GIL_DISABLED"):
        # Ice 3.6.5 does not support free-threaded CPython; a cp31xt wheel
        # should never have been built, so this indicates a matrix mistake.
        print("free-threaded interpreter: unsupported by Ice 3.6.5", file=sys.stderr)
        return 1
    if version != EXPECTED_ICE_VERSION:
        print(f"expected Ice {EXPECTED_ICE_VERSION}, got {version}", file=sys.stderr)
        return 1

    communicator = Ice.initialize()
    communicator.destroy()

    # Constructing a client creates a communicator but does not connect.
    client = omero.client("localhost", 4064)
    client.closeSession()
    print("smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
