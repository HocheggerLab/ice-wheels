"""Round-trip test of a zeroc-ice wheel against a live OMERO server.

Exercises the paths omero-screen depends on: login, an HQL query, and a pixel
write/read through RawPixelsStore. The pixel round-trip is the code path behind
the Python 3.13 segfault that Glencoe fixed in zeroc-ice-py-patches on
2026-06-25, so it is the most important check here.

Usage:
    python tests/integration.py --host localhost --port 4064 --user root --password omero
"""

import argparse
import sys
import time

import Ice
import numpy as np
from omero.gateway import BlitzGateway
from omero.rtypes import rlong
from omero.sys import Parameters

PLANE_SHAPE = (64, 48)
N_PLANES = 3


def connect_with_retry(
    host: str, port: int, user: str, password: str, timeout_s: float
) -> BlitzGateway:
    """Connect to OMERO, retrying while the server finishes starting.

    Args:
        host: OMERO server hostname.
        port: OMERO server port.
        user: Username.
        password: Password.
        timeout_s: Give up after this many seconds.

    Returns:
        A connected gateway.

    Raises:
        ConnectionError: If no connection succeeds before the timeout.
    """
    deadline = time.monotonic() + timeout_s
    while True:
        conn = BlitzGateway(user, password, host=host, port=port, secure=True)
        try:
            if conn.connect():
                return conn
            reason = "login refused"
        except Ice.LocalException as exc:
            # A server that is still starting drops or refuses the connection
            # (ConnectionLostException, ConnectionRefusedException, ...).
            reason = type(exc).__name__
        conn.close()
        if time.monotonic() > deadline:
            raise ConnectionError(
                f"could not log in to {host}:{port} within {timeout_s:.0f} s ({reason})"
            )
        print(f"server not ready ({reason}), retrying in 10 s")
        time.sleep(10)


def pixel_round_trip(conn: BlitzGateway) -> None:
    """Write random planes to a new image, read them back, then delete it.

    Args:
        conn: A connected gateway.

    Raises:
        AssertionError: If any plane read back differs from what was written.
    """
    rng = np.random.default_rng(seed=3_6_5)
    planes = [rng.integers(0, 2**16, PLANE_SHAPE, dtype=np.uint16) for _ in range(N_PLANES)]
    image = conn.createImageFromNumpySeq(
        iter(planes), "ice-wheels round-trip", sizeZ=N_PLANES, sizeC=1, sizeT=1
    )
    image_id = image.getId()
    try:
        reloaded = conn.getObject("Image", image_id)
        pixels = reloaded.getPrimaryPixels()
        for z, expected in enumerate(planes):
            actual = pixels.getPlane(z, 0, 0)
            assert np.array_equal(actual, expected), f"plane z={z} differs after round-trip"
        print(f"pixel round-trip ok: Image:{image_id}, {N_PLANES} planes of {PLANE_SHAPE}")

        params = Parameters()
        params.map = {"id": rlong(image_id)}
        found = conn.getQueryService().findAllByQuery(
            "select i from Image i where i.id = :id", params, conn.SERVICE_OPTS
        )
        assert len(found) == 1, "HQL query did not return the new image"
        print("HQL query ok")
    finally:
        conn.deleteObjects("Image", [image_id], deleteChildren=True, wait=True)


def main() -> int:
    """Run the integration checks.

    Returns:
        Process exit code: 0 on success.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=4064)
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="omero")
    parser.add_argument("--timeout", type=float, default=300.0, help="login retry window (s)")
    args = parser.parse_args()

    conn = connect_with_retry(args.host, args.port, args.user, args.password, args.timeout)
    try:
        server = conn.getConfigService().getVersion()
        print(f"logged in as {conn.getUser().getName()} (server {server})")
        pixel_round_trip(conn)
    finally:
        conn.close()
    print("integration test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
