#!/bin/sh

mongo $1 --eval "db.dropDatabase()"