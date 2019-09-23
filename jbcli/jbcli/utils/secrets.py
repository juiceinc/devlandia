from __future__ import print_function

import boto3
import six


def get_deployment_secrets():
    ssm = boto3.client('ssm')
    result = ssm.get_parameters_by_path(
        Path='/jb-deployment-vars/',
        Recursive=True, WithDecryption=True,
    )
    # These ENCODE calls need to change for python 3 support
    env = {param['Name'][len('/jb-deployment-vars/'):].encode('ascii'): param['Value'].encode('ascii') for param in result['Parameters']}
    return env

