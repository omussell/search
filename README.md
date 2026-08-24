
# crossref search

This is a fork of the Crossref Search application from https://gitlab.com/crossref/search. I am using AI models to convert this app from Python/Flask to Go. The Go code exists in the `go` directory.

## Deployment

Update the configuration in config/.env file

Change the volumes in the 'docker-compose.yml' file if required.

From the root directory, execute the command `docker-compose up -d` to bring up the containers.

By default log files are generated under logs directory

