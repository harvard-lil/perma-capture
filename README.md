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

Spin up the development server:

    # fab run

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


## Design Notes

### JSON Keys

The [Kubecaptures capture service](https://github.com/webrecorder/kubecaptures-backend) returns JSON data with keys formatted in [camel case](https://en.wikipedia.org/wiki/Camel_case). Since this application is primarily a wrapper for the capture service, we too return camel case keys, even though the Python convention is to use [snake case](https://en.wikipedia.org/wiki/Snake_case).

That requires a bit of acrobatics.

We treat the conversion like that between strings and bytes: we work exclusively with snake case keys within the application and convert to and from camel case at the application boundaries, only when communicating with the capture service API or when serializing our own API responses.

Utilities should, for the most part, keep developers from having to think about this much: Django REST Framework will handle the conversion during serialization/deserialization of standard Django requests/responses; our [utility function]() will handle the conversion when we interact with the capture API inside a view function. But, developers should be aware this is occurring and may occasionally become relevant (for instance, during [signature validation]()).

Please keep this in mind when updating docs: JSON should be in camel case, even though the corresponding Python dictionary of data will be in snake case.


## License

This codebase is Copyright 2020 The President and Fellows of Harvard College and is licensed under the open-source AGPLv3 for public use and modification. See [LICENSE](LICENSE) for details.
