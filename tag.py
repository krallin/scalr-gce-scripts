#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import os
import json
import subprocess


TAGS_ENV_VARIABLE = "GCE_TAGS"
TAGS_SEPARATOR = ","

ID_ENV_VARIABLE = "SCALR_CLOUD_SERVER_ID"

GCUTIL_CMD = ["gcutil", "--format=json"]
MAX_ATTEMPTS = 5


def check_output(*popenargs, **kwargs):
    # Python 2.6 support
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output


if __name__ == "__main__":
    tags_string = os.environ.get(TAGS_ENV_VARIABLE, "")
    tags_list = [tag.strip() for tag in tags_string.split(TAGS_SEPARATOR)]
    tags_list = [tag for tag in tags_list if tag]

    # Try in a loop to update the tags (the fingerprint is here to prevent race conditions)

    for _ in range(MAX_ATTEMPTS):
        # Start by getting the current fingerprint and tags
        server_id = os.environ[ID_ENV_VARIABLE]  # This will fail if we're not in a Scalr instance
        instance_data = json.loads(check_output(GCUTIL_CMD + ["getinstance", server_id]))

        current_fingerprint = instance_data["tags"]["fingerprint"]
        current_tags = instance_data["tags"]["items"]

        # Now, update the tags
        all_tags = set(current_tags) | set(tags_list)
        try:
            check_output(GCUTIL_CMD + [
                "setinstancetags", server_id,
                "--tags={0}".format(",".join(all_tags)),
                "--fingerprint={0}".format(current_fingerprint)
            ])
        except subprocess.CalledProcessError as e:
            print("An error occured: {0}".format(e.output))
            continue
        else:
            print("Tags set to: {0}".format(", ".join(all_tags)))
            break

