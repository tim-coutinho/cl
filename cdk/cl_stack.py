import json

from aws_cdk.aws_dynamodb import Attribute, AttributeType, Table
from aws_cdk.aws_events import Rule, RuleTargetInput, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_lambda import Runtime
from aws_cdk.aws_lambda_python import PythonFunction
from aws_cdk.core import Construct, Duration, Stack


class ClStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table_name = "posts2"
        function_name = "cl2"
        email = "tmcoutinho42@gmail.com"

        table = Table(
            self,
            "cl_posts",
            table_name=table_name,
            partition_key=Attribute(name="url", type=AttributeType.STRING),
            time_to_live_attribute="ttl",
        )

        function = PythonFunction(
            self,
            "cl_function",
            function_name=function_name,
            entry="src",
            index="app.py",
            runtime=Runtime.PYTHON_3_8,
            environment={"cl_email": email, "cl_table_name": table_name},
            timeout=Duration.seconds(300),
            initial_policy=[
                PolicyStatement(
                    actions=["ses:SendEmail", "ses:VerifyEmailIdentity"],
                    resources=[f"arn:aws:ses:{self.region}:{self.account}:identity/{email}"],
                ),
                PolicyStatement(
                    actions=["dynamodb:BatchGetItem", "dynamodb:BatchWriteItem"],
                    resources=[table.table_arn],
                ),
            ],
        )

        with open("events/event.json") as f:
            event = json.load(f)

        Rule(
            self,
            "cl_schedule",
            schedule=Schedule.expression("cron(0 19 * * ? *)"),
            targets=[LambdaFunction(function, event=RuleTargetInput.from_object(event))],
        )
