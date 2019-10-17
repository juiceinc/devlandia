from __future__ import print_function

import boto3
import six

def get_all_from_path(path):
    """
    Given a SSM parameter path, get all parameters stored recursively under that path.

    Given `/PATH`, and parameters such as:

        /PATH/FOO = a, /PATH/BAR = b

    this returns {'FOO': 'a', 'BAR': 'b'}
    """
    try:
        result = ssm.get_parameters_by_path(
            Path=path,
            Recursive=True, WithDecryption=True,
        )
    except Exception as e:
        print("[WARNING] couldn't fetch parameters under path", path, e)
        return {}
    # These ENCODE calls probably need to change for python 3 support
    return {
        param['Name'].rsplit('/', 1)[-1].encode('ascii'): param['Value'].encode('ascii')
        for param in result['Parameters']
    }


def get_deployment_secrets():
    ssm = boto3.client('ssm')
    env = get_all_from_path('/jb-deployment-vars/common/')
    env.update(get_all_from_path('/jb-deployment-vars/devlandia/'))
    return env

