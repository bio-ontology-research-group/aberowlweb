# AberOWL

Aberowl is a framework for ontology-based data access that consists of an ontology repository that can be queried through an OWL 2 EL reasoner.

# Prerequisites

You will need the following list of tools installed before we could run aberowl framework.

  - Linux debian or RHEL
  - Python 3.*.*
  - Groovy
  - PostgreSQL
  - RabbitMq
  - Redis
  - Memcached
  - Elasticsearch
  - Supervisor

# Installing Aberowl

Firstly, you will need to download aberowl from github and extract the source to opt/aberowl folder. Aberowl directory path will look like the following:

```sh
/opt/aberowl/aberowlweb
```
#### Configure Virtual environment

To install aberowl we will first setup a virtual enviroment to install framework dependencies in an isolated environment.
Run the following commands to install:

```sh
pip install virtualenv
```
After installing the virtual environment, we will create the virtual environment in application folder.

```sh
# Navigate to aberowl application folder 
cd /opt/aberowl/aberowlweb

# Create a virtual environment with name 'venv'
virtualenv venv

# Run the virtual environment
source venv/bin/activate
```
#### Install aberowl dependencies

To install aberowl dependencies, you can run simply the following command:

```sh
pip install -r .\requirements.txt
```

However sometimes pip package manager causes problem while installing *word2vec* module. It is recommeded to use *conda* package manager to install *word2vec* module in case pip does not resolve the package. After installing it with conda, run the above command again to install the other dependencies.

#### Create a database in PostgreSQL

Create a database with name *aberowlweb*.

#### Running Aberowl modules

Aberowl is currently consist of two of modules:

| Modules | Description |
| ------ | ------ |
| Aberowl Web | Web application |
| Ontology API | An API to manage ontology repository and executing queries. |

#### Running Celery

Aberowl Web module uses Celery to distribute tasks to ontology API module. Here is the command to run the celery module:

```sh
celery -A aberowlweb -l INFO worker
```
#### Running Ontology API

To run ontology API, run the following command. By default, the ontology API runs on *8080* port:
```sh
python manage.py runontapi
```

#### Running Aberowl Web

To run Aberowl web application, run the following command. By default, it runs on *8000* port:
```sh
python manage.py runserver
```
You can now use the URL: *http://localhost:8000* to access Aberowl.
