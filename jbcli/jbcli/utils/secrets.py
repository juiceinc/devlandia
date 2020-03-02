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
    ssm = boto3.client('ssm')
    try:
        result = ssm.get_parameters_by_path(
            Path=path,
            Recursive=True, WithDecryption=True,
        )
    except Exception as e:
        print("[WARNING] couldn't fetch parameters under path", path, e)
        return {}
    return {
        param['Name'].rsplit('/', 1)[-1]: param['Value']
        for param in result['Parameters']
    }


def get_deployment_secrets():
    env = get_all_from_path('/jb-deployment-vars/common/')
    env.update(get_all_from_path('/jb-deployment-vars/devlandia/'))
    return env

