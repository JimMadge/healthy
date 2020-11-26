import docker


def main():
    client = docker.from_env()

    for container in client.containers.list():
        health_check(container)


def health_check(container):
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


def get_health_status(container):
    state = container.attrs["State"]

    if "Health" in state.keys():
        return state["Health"]["Status"]
    else:
        return None


def output(name, status, action):
    print(f"{name} - {status} - {action}")


if __name__ == "__main__":  # pragma no cover
    main()
