# STRESS Container
Simple Alpine container that executes the stress command.

Based on community package:
-   https://pkgs.alpinelinux.org/package/edge/community/x86_64/stress-ng

# USAGE
- If you set the entrypoint as ```stress-ng```, you can use the container with the options to pass to stress command.
- If you use CMD, set the command to exec in the dockerfile

## Examples
ENTRY = STRESS
- Stress only one CPU for ten seconds - ```docker run stress-img --cpu 1 --timeout 10s```

# COMPOSE
To use the compose file you have to build the image. Example from the current folder ```docker build -t stress-img .```

