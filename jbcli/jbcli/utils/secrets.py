import boto3


def get_all_from_path(path):
    """
    Given a SSM parameter path, get all parameters stored recursively under that path.

    Given `/PATH`, and parameters such as:

        /PATH/FOO = a, /PATH/BAR = b

    this returns {'FOO': 'a', 'BAR': 'b'}
    """
    ssm = boto3.client("ssm")
    next_token = None
    env_vars = {}
    while True:
        try:
            kwargs = {}
            if next_token is not None:
                kwargs["NextToken"] = next_token
            result = ssm.get_parameters_by_path(
                Path=path, Recursive=True, WithDecryption=True, **kwargs
            )
        except Exception as e:
            print("[WARNING] couldn't fetch parameters under path", path, e)
            return {}
        env_vars.update(
            {
                param["Name"].rsplit("/", 1)[-1]: param["Value"]
                for param in result["Parameters"]
            }
        )
        if result.get("NextToken") is None:
            break
        else:
            next_token = result["NextToken"]
    return env_vars


def get_deployment_secrets():
    env = get_all_from_path("/jb-deployment-vars/common/")
    env.update(get_all_from_path("/jb-deployment-vars/devlandia/"))
    return env
