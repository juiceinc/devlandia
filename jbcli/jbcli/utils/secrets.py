from __future__ import print_function

import boto3


def get_paramstore(param_name):
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return parameter['Parameter']['Value'].encode('ascii')
