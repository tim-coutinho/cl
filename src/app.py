import json
import logging

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
    table_name = "posts"

    posts = cl.main(argv)
    posts = [{"url": k, **v} for k, v in posts.items()]

    existing_posts = ddb.batch_get_item(
        RequestItems={table_name: {"Keys": [{"url": post["url"]} for post in posts]}}
    )["Responses"][table_name]
    new_posts = len(posts) - len(existing_posts)

    ddb.batch_write_item(
        RequestItems={table_name: [{"PutRequest": {"Item": post}} for post in posts]}
    )

    ses.send_email(
        Source="tmcoutinho42@gmail.com",
        Destination={"ToAddresses": ["tmcoutinho42@gmail.com"]},
        Message={
            "Subject": {"Data": f"{len(posts)} posts, {new_posts} new"},
            "Body": {"Text": {"Data": json.dumps(posts, indent=2)}},
        },
    )
