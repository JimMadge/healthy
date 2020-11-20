import docker
from healthy.__main__ import health_check
import pytest
from textwrap import dedent
from time import sleep


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


@pytest.fixture
def healthy_container(tmp_path, docker_client):
    # Create temporary directory
    d = tmp_path / "healthy"
    d.mkdir()

    # Write 'healthy' Dockerfile
    dockerfile = d / "Dockerfile"
    dockerfile.write_text(dedent("""\
        FROM alpine:latest

        RUN apk add --no-cache curl

        HEALTHCHECK --interval=10s CMD curl -f https://archlinux.org
    """))

    # Create 'healthy' container
    docker_client.images.build(
        path=str(d),
        rm=True,
        tag="healthy"
    )
    container = docker_client.containers.run(
        "healthy",
        command="sleep 2m",
        name="healthy",
        detach=True,
        auto_remove=True
    )

    # Wait for container to start
    container.reload()
    while container.attrs["State"]["Health"]["Status"] == "starting":
        sleep(1)
        container.reload()

    yield container

    # Stop container and remove image
    container.stop()
    docker_client.images.remove("healthy")


def test_healthy(capsys, healthy_container):
    health_check(healthy_container)

    captured = capsys.readouterr()
    assert captured.out.strip() == "healthy - healthy - skipping"
