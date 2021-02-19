# Perma-Capture

[![CircleCI](https://circleci.com/gh/harvard-lil/perma-capture.svg?style=svg)](https://circleci.com/gh/harvard-lil/perma-capture)
[![codecov](https://codecov.io/gh/harvard-lil/perma-capture/branch/develop/graph/badge.svg)](https://codecov.io/gh/harvard-lil/perma-capture)

## Development

### Spin up some containers

Start up the Docker containers in the background:

    $ docker-compose up -d

The first time this runs it will build the Docker images, which
may take several minutes. (After the first time, it should only take
1-3 seconds.)

Then log into the main Docker container:

    $ docker-compose exec web bash

(Commands from here on out that start with `#` are being run in Docker.)

### Run Django

You should now have a working installation!

Migrate the database:

    # ./manage.py migrate

Spin up the development server:

    # fab run

Create a test admin user (follow the prompts, then log in using those credentials):

    # ./manage.py createsuperuser

### Optional: load some sample data

To more fully explore the UI, you may want to load some sample data.

    # fab load_sample_capture_data

See [fabfile.py](https://github.com/harvard-lil/perma-capture/blob/develop/web/fabfile.py#L71)
for a fuller discussion of options.

### Optional: wire up a capture service

To capture websites and serve archives, this application must be configured to communicate with a running [capture service](https://github.com/webrecorder/kubecaptures-backend). You can run one locally at the same time as this application using Minikube (Docker driver).

Follow the directions for the KubeCaptures "[Sample Development Flow](https://github.com/webrecorder/kubecaptures-backend#sample-development-workflow)." The capture service will be exposed to your `localhost` on a particular port by `minikube service --url browserkube`: make note of it. The minio storage service should also be available to your `localhost` on port 9000.

In this application's `settings.py`, add the following stanzas:
```
# Tell the capture service to direct its webhook callbacks to this Django app,
# using Docker's special hostname for internal routing.
CALLBACK_PREFIX = "http://host.docker.internal:8000"

# Tell this application where the capture service's WACZ files are hosted:
# if accessed by a user, via curl or their browser, minio will be at localhost;
# if accessed by the Django application, inside its container, minio will be at
# Docker's special hostname for internal routing.
OVERRIDE_ACCESS_URL_NETLOC = {'internal': 'host.docker.internal:9000', 'external': 'localhost:9000'}
```

Then, add the following, swapping in the port your capture service is exposed on ("49445" in this example):
```
BACKEND_API = "http://host.docker.internal:49445"
```

Remember, every time you start the capture service, it will be exposed on a different port, so you will have to update this setting regularly. The Django application will restart automatically when you make changes to `settings.py`.

If everything is working, you should now be able to (while logged in as your test superuser):
- request multiple captures of http://example.com
- watch the capture jobs complete in your kubernetes dashboard
- watch the capture service POST to our webhook callback; see the newly created 'Archive' objects at `http://localhost:8000/admin/main/archive/`; observe the hash of each file is different
- watch the Django application poll continuously and eventually report the capture jobs are complete
- download the WACZ files using the UI button or the API
- view playbacks of the WACZ files using the UI button

### Stop

When you are finished, spin down Docker containers by running:

    $ docker-compose down

Your database will persist and will load automatically the next time you run `docker-compose up -d`.

Or, you can clean up everything Docker-related, so you can start fresh, as with a new installation:

    $ bash docker/clean.sh


## Testing

### Test Commands

1. `pytest` runs python tests
1. `flake8` runs python lints

### Coverage

Coverage will be generated automatically for all manually-run tests.

## Migrations

We use standard Django migrations

## Contributions

Contributions to this project should be made in individual forks and then merged by pull request. Here's an outline:

1. Fork and clone the project.
1. Make a branch for your feature: `git branch feature-1`
1. Commit your changes with `git add` and `git commit`. (`git diff  --staged` is handy here!)
1. Push your branch to your fork: `git push origin feature-1`
1. Submit a pull request to the upstream develop through GitHub.

## License

This codebase is Copyright 2020 The President and Fellows of Harvard College and is licensed under the open-source AGPLv3 for public use and modification. See [LICENSE](LICENSE) for details.
