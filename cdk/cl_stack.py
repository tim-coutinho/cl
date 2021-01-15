from aws_cdk.aws_dynamodb import Attribute, AttributeType, Table
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.core import Construct, Stack


class ClStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = Table(
            self,
            "cl_posts",
            table_name="posts",
            partition_key=Attribute(name="url", type=AttributeType.STRING),
            time_to_live_attribute="ttl",
        )

        function = Function(
            self,
            "cl_function",
            function_name="cl2",
            code=Code.from_asset("src"),
            handler="app.handler",
            runtime=Runtime.PYTHON_3_8,
            initial_policy=[
                PolicyStatement(
                    actions=["ses:SendEmail", "ses:VerifyEmailIdentity"],
                    resources=[
                        f"arn:aws:ses:{self.region}:{self.account}:identity/tmcoutinho42@gmail.com"
                    ],
                ),
                PolicyStatement(
                    actions=["dynamodb:BatchGetItem", "dynamodb:BatchWriteItem"],
                    resources=[table.table_arn],
                ),
            ],
        )

        rule = Rule(
            self,
            "cl_schedule",
            schedule=Schedule.expression("cron(0 19 * * ? *)"),
            targets=[LambdaFunction(function)],
        )
