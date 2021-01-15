#!/usr/bin/env python3

from aws_cdk.core import App

from cdk.cl_stack import ClStack

app = App()
ClStack(app, "cl")

app.synth()
