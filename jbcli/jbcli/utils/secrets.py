from __future__ import print_function

import boto3

ssm = boto3.client('ssm')


def get_paramstore(param_name):
    parameter = ssm.get_parameter(Name=param_name, WithDecryption=True)
    return parameter['Parameter']['Value'].encode('ascii')
