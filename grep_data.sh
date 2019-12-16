#! /bin/sh
grep 'python' Posts.xml > Posts.python.xml
grep 'PostTypeId=\"2\"' Posts.xml >  Posts.answers.xml
