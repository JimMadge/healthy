import contextlib
import docker
from healthy.__main__ import health_check, get_health_status, output, main
import pytest
from textwrap import dedent
from time import sleep


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


@contextlib.contextmanager
def example_container(name, dockerfile_text, path, docker_client):
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


testdata = [
    ("healthy", healthy_dockerfile, "healthy"),
    ("unhealthy", unhealthy_dockerfile, "unhealthy"),
    ("nohealth", no_health_dockerfile, None),
]


@pytest.mark.parametrize("name,dockerfile,expected_status", testdata)
def test_get_health_status(tmp_path, docker_client, name, dockerfile,
                           expected_status):
    path = tmp_path / name
    path.mkdir()

    with example_container(name, dockerfile, path, docker_client) as container:
        assert get_health_status(container) == expected_status


def test_output(capsys):
    output("name", "status", "action")
    stdout = capsys.readouterr().out

    assert stdout.strip() == "name - status - action"


def test_main(capsys, tmp_path, docker_client):
    with example_container("testa", healthy_dockerfile, tmp_path,
                           docker_client):
        with example_container("testb", unhealthy_dockerfile, tmp_path,
                               docker_client):
            with example_container("testc", no_health_dockerfile, tmp_path,
                                   docker_client):
                main()
                stdout = capsys.readouterr().out

    expected_output = dedent("""\
        testc_container - no health check - skipping
        testb_container - unhealthy - restarting
        testa_container - healthy - skipping
        """)

    assert stdout == expected_output
