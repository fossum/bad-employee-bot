# Use an official Python runtime as a parent image.
# The -slim variant is a good choice for production as it's smaller.
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install pipenv, which is used to manage project dependencies
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock to the container.
# These are used by pipenv to install the correct versions of your dependencies.
COPY Pipfile Pipfile.lock ./

# Install project dependencies into the system's site-packages.
# --system: Installs packages to the system site-packages, standard for containers.
# --deploy: Ensures Pipfile.lock is up-to-date and fails the build if not.
# --ignore-pipfile: Ensures installation only from the lock file for deterministic builds.
RUN pipenv install --system --deploy --ignore-pipfile

# Copy the rest of your application's source code into the container
COPY . .

# The command to run your application
CMD ["python", "main.py"]
