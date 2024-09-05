from attr import validate
import boto3
import json


# @todo wrapper has callback
def task(self, name, payload, **kwargs):
    region = kwargs.get("region", "us-west-2")
    response = boto3.client("sts").get_caller_identity()
    user_id = response.get("UserId").split(":").pop()

    ecs = boto3.client("ecs")
    env_data = {}
    env_data["PY_ENV"] = "production"
    env_pairs = [{"name": k, "value": env_data[k]} for k in env_data]
    role_arn = None
    task_definition_arn = None
    subnets = ["subnet-05a5xxxxxxxxxxx", "subnet-0bc46xxxxxxxxxx"]
    response = ecs.run_task(
        cluster=ecs_cluster,
        count=1,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": [],
                "assignPublicIp": "DISABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": "app",
                    "command": ["run.py", "--execute=" + task_name],
                    "environment": env_pairs,
                    "memory": 8192,
                },
            ],
            "taskRoleArn": role_arn,
        },
        startedBy="api@%s" % user_id,
        taskDefinition=task_definition_arn,
    )

    started_tasks = response.get("tasks")
    if started_tasks:
        print("[i] Started %s tasks" % len(started_tasks))
        for task in started_tasks:
            task_id = task["taskArn"].split("/")[-1]
            cluster = task["clusterArn"].split("/")[-1]
            print(
                "[i] Task https://{region}.console.aws.amazon.com/ecs/home?region={region}#/clusters/{cluster}/tasks/{task_id}/details".format(
                    **{
                        "task_id": task_id,
                        "cluster": cluster,
                        "region": region,
                    }
                )
            )


def configure():
    pass


def install(env):
    pass


def teardown(env):
    pass
