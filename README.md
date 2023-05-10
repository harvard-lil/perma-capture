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

### Get the database ready

Migrate the database:

    # ./manage.py migrate

Create an admin user (you will be prompted for a placeholder email address, name, and password):

    # ./manage.py createsuperuser

### Option one: run Django with pre-compiled JS and CSS

(runs faster)

Spin up the development server:

    # fab run

The first time this runs it will build the Scoop image, which may take a minute
or two. (After the first time, it should only take 1-3 seconds.)

### Option two: run Django and re-compile JS and CSS on the fly

(tighter development loop during front-end development)

Install the node dependencies:

    # cd frontend
    # yarn install
    # cd ../

Spin up the development server:

    # fab run_fullstack

The first time this runs it will build the Scoop image, which may take a minute
or two. (After the first time, it should be faster, but still takes a bit to
start up, and takes a bit again when you first load a page.)

### Log in and explore

Visit http://localhost:8000 in your browser. You should be able to log in using
the admin credentials you created earlier.

To test the API directly, first visit http://localhost:8000/user/account/ to find your API key.

Check out the User Guide at /docs/ for more info.

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
