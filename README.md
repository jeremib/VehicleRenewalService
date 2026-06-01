```
export DOCKER_DEFAULT_PLATFORM=linux/amd64 && docker build -t vehicle_registration . && docker run -p 8080:80 -v "$(pwd)/app:/app" vehicle_registration`
```