FROM alpine:latest

RUN apk update --no-cache && \
    apk add --no-cache stress-ng

# ENTRYPOINT ["stress-ng"]

CMD ["stress-ng", "--cpu", "1", "--timeout", "10m"]