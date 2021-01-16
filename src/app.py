import datetime
import json
import logging
import os

import boto3

import cl


def handler(event, context):
    logging.getLogger().setLevel(logging.INFO)
    argv = [
        *event.get("query"),
        "--category",
        event.get("category"),
        "--max_price",
        event.get("max_price"),
        "--min_price",
        event.get("min_price"),
        "--details",
        *event.get("details"),
    ]
    main(argv)


def main(argv):
    ses = boto3.client("ses")
    ddb = boto3.resource("dynamodb")
    table_name = os.environ["cl_table_name"]
    email = os.environ["cl_email"]

    posts = cl.main(argv)
    posts = [
        {
            "url": k,
            "ttl": int((datetime.datetime.now() + datetime.timedelta(days=30)).timestamp()),
            **v,
        }
        for k, v in posts.items()
    ]

    existing_posts = ddb.batch_get_item(
        RequestItems={table_name: {"Keys": [{"url": post["url"]} for post in posts]}}
    )["Responses"][table_name]
    new_posts = [
        post for post in posts if post["url"] not in [post["url"] for post in existing_posts]
    ]
    num_new_posts = len(new_posts)
    if num_new_posts == 0:
        return

    ddb.batch_write_item(
        RequestItems={table_name: [{"PutRequest": {"Item": post}} for post in new_posts]}
    )

    ses.send_email(
        Source=email,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": f"{len(new_posts)} new listing{'s' if len(new_posts) > 1 else ''}"},
            "Body": {"Text": {"Data": json.dumps(new_posts, indent=2)}},
        },
    )
