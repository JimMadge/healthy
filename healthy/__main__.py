import docker


def main():
    client = docker.from_env()

    for container in client.containers.list():
        health_check(container)


def health_check(container):
    name = container.name
    state = container.attrs["State"]

    if "Health" in state.keys():
        if (status := state["Health"]["Status"]) == "unhealthy":
            output(name, status, "restarting")
            container.restart()
        else:
            output(name, status, "skipping")
    else:
        output(name, "no health check", "skipping")


def output(name, status, action):
    print(f"{name} - {status} - {action}")


if __name__ == "__main__":
    main()
