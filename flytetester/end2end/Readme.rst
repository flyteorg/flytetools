End-to-end Testing Notes
=============================

#############
Iteration
#############

For use with local Docker for Mac.  This is the easiest iteration cycle I've found in writing these end-to-end tests.

#. Setup all the port-forwards for all the services (Admin, minio, & psql).  Just to make life easier.
#. Truncate all tables in your local Admin Postgres database.
#. Make changes to this repo.  Commit them, and build an updated docker image. Note that because you're running things locally, and because the ``PullPolicy`` is set to ``IfNotPresent``, you don't need to push the new image anywhere.
#. Update the ``endtoend.yaml``  with your new SHA.
#. Alternate between ``kf create -f end2end/tests/endtoend.yaml`` and ``kf delete -f end2end/tests/endtoend.yaml`` and look at the logs for that pod.

Also helpful is to have an iPython window up, with clients connected to the Docker for mac Admin (port-forwarded), so you can run requests against it and see what the responses should be.
