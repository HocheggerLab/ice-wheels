# manylinux_2_28 build image for the Linux wheels (x86_64 and aarch64).
# ARCH matches the runner: the aarch64 image runs natively on ubuntu-24.04-arm.
ARG ARCH=x86_64
FROM quay.io/pypa/manylinux_2_28_${ARCH}

RUN yum install -y -q bzip2-devel openssl-devel
RUN for v in cp312-cp312 cp313-cp313 cp314-cp314; do \
        /opt/python/${v}/bin/python -m pip install --upgrade pip setuptools wheel; \
    done
