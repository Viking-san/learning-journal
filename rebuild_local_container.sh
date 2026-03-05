#!/bin/bash
cd /home/pans/projects/learning-journal
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d --build

