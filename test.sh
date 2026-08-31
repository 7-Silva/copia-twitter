#!/usr/bin/bash

#Start enviromenment with docker-compose
PAMPS_DB=pamps_test docker-compose up -d

#wait 5 seconds
sleep 5

# Ensure database in clean
docker-compose exec api pamps reset-db -f
docker-compose exec api alembic stamp database

#run migrations
docker-compose exec api alembic upgrade head

#run tests
docker-compose exec api pytest -v -l --tb=short --maxfail=1 test/

#stop environment
docker-compose down