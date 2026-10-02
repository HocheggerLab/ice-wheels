# ice-wheels

Pre-built [ZeroC Ice](https://zeroc.com) 3.6.5 Python wheels for **CPython 3.12, 3.13 and 3.14**, for use with [omero-py](https://github.com/ome/omero-py).

omero-py requires `zeroc-ice>=3.6.5,<3.7`. PyPI only has a 3.6.5 source package, and it doesn't build on current compilers or Pythons without patches. [Glencoe Software](https://www.glencoesoftware.com/blog/2023/12/08/ice-binaries-for-omero.html) publishes patched wheels, but its released wheels stop at cp312. This repo builds the same patch series for newer Pythons until Glencoe releases its own.

| Platform | Wheel tag | 3.12 | 3.13 | 3.14 |
|---|---|:-:|:-:|:-:|
| Linux x86_64 | `manylinux_2_28_x86_64` | ✓ | ✓ | ✓ |
| Linux aarch64 | `manylinux_2_28_aarch64` | ✓ | ✓ | ✓ |
| macOS (arm64 + x86_64) | `macosx_11_0_universal2` | ✓ | ✓ | ✓ |
| Windows x86_64 | `win_amd64` | ✓ | ✓ | ✓ |

The Linux wheels bundle the OpenSSL that ships with the `manylinux_2_28` image (AlmaLinux 8).

## Using the wheels

### uv (recommended)

```toml
[[tool.uv.index]]
name = "hocheggerlab-ice"
url = "https://hocheggerlab.github.io/ice-wheels/"
format = "flat"
explicit = true

[tool.uv.sources]
zeroc-ice = { index = "hocheggerlab-ice" }
```

Then depend on `zeroc-ice==3.6.5` as usual. `explicit = true` restricts this index to `zeroc-ice`, so it can't shadow any other package.

### pip

```bash
pip install zeroc-ice==3.6.5 --only-binary zeroc-ice \
    --find-links https://hocheggerlab.github.io/ice-wheels/
pip install omero-py
```

Each GitHub Release also carries the wheels directly, plus a `SHA256SUMS` file.

## How the wheels are built

- **Source:** the PyPI sdist `zeroc-ice-3.6.5.tar.gz`, verified against a pinned SHA-256.
- **Patches:** [`glencoesoftware/zeroc-ice-py-patches`](https://github.com/glencoesoftware/zeroc-ice-py-patches), included as the `patches/` git submodule at a pinned commit. The series adds support for Python 3.11–3.13 (3.13 also covers 3.14), Visual Studio 2022 and newer GCC versions.
- **macOS:** also applies `macos/osx.patch`, vendored from [conda-forge/zeroc-ice-feedstock](https://github.com/conda-forge/zeroc-ice-feedstock) (BSD-3-Clause).
- **Build environments:** the same as Glencoe's per-platform repos:
  - Linux: `quay.io/pypa/manylinux_2_28_*` containers, run natively on x86_64 and arm64 runners, then repaired with `auditwheel`
  - macOS: `macos-14`, universal2
  - Windows: `windows-2022`

Everything lives in [`.github/workflows/build.yml`](.github/workflows/build.yml).

## Testing

Every push and PR builds all 12 wheels. A wheel only gets uploaded if it passes these checks:

1. **Smoke test** ([`tests/smoke.py`](tests/smoke.py)), on every platform and Python. It installs the wheel and omero-py into a fresh environment, checks `Ice.stringVersion() == "3.6.5"`, and constructs a communicator and an `omero.client`.
2. **Live-server test** ([`tests/integration.py`](tests/integration.py)), on Linux x86_64 for 3.12–3.14, against an `openmicroscopy/omero-server` service container. It logs in, writes random planes through `RawPixelsStore`, reads them back bit-for-bit, runs an HQL query, then deletes the image.
   - The pixel round-trip covers the code path behind a Python 3.13 segfault that Glencoe fixed in the patch series on 2026-06-25.
   - The OMERO server image is amd64-only, so the aarch64 wheels get this test by hand on an aarch64 host:
     ```bash
     uv run --no-project --isolated --python 3.14 \
         --with ./zeroc_ice-3.6.5-cp314-cp314-manylinux_2_28_aarch64.whl --with omero-py \
         tests/integration.py --host <omero-host> --user <user> --password <password>
     ```

Known upstream caveat: Glencoe reports that launching *server-side* OMERO scripts from a Python 3.13 environment fails with `ApiUsageException: Job already finished` (see [zeroc-ice-py-linux-x86_64#4](https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/issues/4)). Client-side use is unaffected.

## Releasing

1. Check that CI is green on `main`.
2. Tag `3.6.5-YYYYMMDD` and push the tag:
   ```bash
   git tag 3.6.5-20261002 && git push origin 3.6.5-20261002
   ```
3. The `release` job then:
   - checks that exactly 12 wheels were built
   - writes `SHA256SUMS`
   - creates the GitHub Release
   - regenerates the flat index ([`scripts/make_index.py`](scripts/make_index.py)) to point at that release, and deploys it to GitHub Pages

The index always lists exactly one release. All releases share the same filenames, so listing several would give resolvers duplicate candidates. Older releases stay downloadable, so existing lockfiles that pin their URLs keep working.

Dependabot opens a PR whenever the `patches` submodule or a pinned action changes upstream.

## Retirement plan

This repo is a stop-gap. When Glencoe releases cp313/cp314 wheels from its own repos:

1. Regenerate `index.html` to point at Glencoe's release assets, keeping the index URL unchanged for downstream projects.
2. Re-lock downstream projects and check that only URLs and hashes change.
3. Archive this repo.

## Licence

The build scripts and tests in this repository are MIT-licensed (see [LICENSE](LICENSE)). The wheels contain ZeroC Ice, which is licensed under the GNU GPL v2. See the [Ice licence](https://github.com/zeroc-ice/ice/blob/3.6/ICE_LICENSE).
