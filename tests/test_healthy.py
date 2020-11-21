import contextlib
import docker
from healthy.__main__ import health_check
import pytest
from textwrap import dedent
from time import sleep


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


@contextlib.contextmanager
def example_container(name, dockerfile_text, path, docker_client):
    # print(name)
    # print(dockerfile)
    # print(type(dockerfile))
    # print(path)
    # Write Dockerfile
    dockerfile = path / "Dockerfile"
    dockerfile.write_text(dockerfile_text)

    # Create  container
    docker_client.images.build(
        path=str(path),
        rm=True,
        tag=f"{name}_image"
    )
    container = docker_client.containers.run(
        f"{name}_image",
        command="sleep 2m",
        name=f"{name}_container",
        detach=True,
        auto_remove=True
    )

    # Wait for container to start
    container.reload()
    if "Health" in container.attrs["State"].keys():
        while container.attrs["State"]["Health"]["Status"] == "starting":
            sleep(1)
            container.reload()

    try:
        yield container
    finally:
        # Stop container and remove image
        container.stop()
        docker_client.images.remove(
            f"{name}_image",
            force=True
        )


healthy_dockerfile = dedent("""\
    FROM alpine:latest

    HEALTHCHECK --interval=10s CMD true
    """)

unhealthy_dockerfile = dedent("""\
    FROM alpine:latest

    HEALTHCHECK --interval=10s CMD false
    """)

no_health_dockerfile = dedent("""\
    FROM alpine:latest
    """)


testdata = [
    ("healthy", healthy_dockerfile, "healthy", "skipping"),
    ("unhealthy", unhealthy_dockerfile, "unhealthy", "restarting"),
    ("nohealth", no_health_dockerfile, "no health check", "skipping"),
]


@pytest.mark.parametrize("name,dockerfile,expected_status,expected_action",
                         testdata)
def test_health_check(capsys, tmp_path, docker_client, name, dockerfile,
                      expected_status, expected_action):
    path = tmp_path / name
    path.mkdir()

    with example_container(name, dockerfile, path, docker_client) as container:
        health_check(container)

        stdout = capsys.readouterr().out
        expected = f"{name}_container - {expected_status} - {expected_action}"
        assert stdout.strip() == expected

        if expected_action == "restarting":
            container.reload()
            assert container.attrs["State"]["Health"]["Status"] == "starting"
