import docker  # type: ignore
from typing import Optional


def main() -> None:
    client = docker.from_env()

    for container in client.containers.list():
        health_check(container)


def health_check(container: docker.Container) -> None:
    name = container.name
    status = get_health_status(container)

    if status is None:
        status = "no health check"

    skip_statuses = ["no health check", "healthy"]
    restart_statuses = ["unhealthy"]

    if status in skip_statuses:
        output(name, status, "skipping")
    elif status in restart_statuses:
        output(name, status, "restarting")
        container.restart()
    else:
        output(name, status, "skipping")


def get_health_status(container: docker.Container) -> Optional[str]:
    state = container.attrs["State"]

    if "Health" in state.keys():
        return str(state["Health"]["Status"])
    else:
        return None


def output(name: str, status: str, action: str) -> None:
    print(f"{name} - {status} - {action}")


if __name__ == "__main__":  # pragma no cover
    main()
