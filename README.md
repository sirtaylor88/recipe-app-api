# Recipe app

A recipe management app built with Django REST API, Docker, Unittest and Travis CI

To run

    docker-compose up


To run test

    docker-compose run --rm app sh -c "python manage.py test && flake8"

To rebuild docker container
    
    docker-compose build
