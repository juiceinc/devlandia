import boto3

SSM = boto3.client("ssm")


def list_all_in_paths(paths):
    params = []
    next_token = None
    while True:
        resp = SSM.describe_parameters(
            ParameterFilters=[{"Key": "Name", "Option": "BeginsWith", "Values": paths}],
            **{"NextToken": next_token} if next_token else {},
        )
        params.extend([x["Name"] for x in resp["Parameters"]])
        next_token = resp.get("NextToken")
        if not next_token:
            return params


def get_all_from_paths(paths):
    """
    Given a SSM parameter path, get all parameters stored recursively under that path.

    Given `/PATH`, and parameters such as:

        /PATH/FOO = a, /PATH/BAR = b

    this returns {'FOO': 'a', 'BAR': 'b'}
    """
    all_parameters = list_all_in_paths(paths)

    env_vars = {}
    for name in all_parameters:
        try:
            result = SSM.get_parameter(Name=name, WithDecryption=True)
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                print("skipping parameter that we don't have access to", name)
                continue
            else:
                raise
        bare_name = result["Parameter"]["Name"].rsplit("/", 1)[-1]
        env_vars[bare_name] = result["Parameter"]["Value"].encode("ascii")

    return env_vars


def get_deployment_secrets():
    return get_all_from_paths(
        ["/jb-deployment-vars/common/", f"/jb-deployment-vars/devlandia/"]
    )
