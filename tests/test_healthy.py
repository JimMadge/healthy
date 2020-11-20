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

        HEALTHCHECK --interval=10s CMD true
    """))

    # Create 'healthy' container
    docker_client.images.build(
        path=str(d),
        rm=True,
        tag="healthy_image"
    )
    container = docker_client.containers.run(
        "healthy_image",
        command="sleep 2m",
        name="healthy_container",
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
    docker_client.images.remove("healthy_image")


@pytest.fixture
def unhealthy_container(tmp_path, docker_client):
    # Create temporary directory
    d = tmp_path / "unhealthy"
    d.mkdir()

    # Write 'unhealthy' Dockerfile
    dockerfile = d / "Dockerfile"
    dockerfile.write_text(dedent("""\
        FROM alpine:latest

        HEALTHCHECK --interval=10s CMD false
    """))

    # Create 'unhealthy' container
    docker_client.images.build(
        path=str(d),
        rm=True,
        tag="unhealthy_image"
    )
    container = docker_client.containers.run(
        "unhealthy_image",
        command="sleep 2m",
        name="unhealthy_container",
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
    docker_client.images.remove("unhealthy_image")


def test_healthy(capsys, healthy_container):
    health_check(healthy_container)

    captured = capsys.readouterr()
    assert captured.out.strip() == "healthy_container - healthy - skipping"


def test_unhealthy(capsys, unhealthy_container):
    health_check(unhealthy_container)

    captured = capsys.readouterr()
    assert (
        captured.out.strip() == "unhealthy_container - unhealthy - restarting"
    )
