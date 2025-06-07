"""Generic queue handler for RabbitMQ or SQS with batching, retries, and flush timeout."""
import json
import time
import signal
import threading
from typing import Callable, Any

import boto3
import pika
from botocore.exceptions import BotoCoreError, NoCredentialsError
from pika.exceptions import AMQPConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential

from app import config
from app.utils.setup_logger import setup_logger

logger = setup_logger(__name__)
shutdown_event = threading.Event()


def consume_messages(callback: Callable[[list[dict[str, Any]]], None]) -> None:
    """Starts the queue listener for the configured queue type."""
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    queue_type = config.get_queue_type().lower()
    if queue_type == "rabbitmq":
        _start_rabbitmq_listener(callback)
    elif queue_type == "sqs":
        _start_sqs_listener(callback)
    else:
        raise ValueError(f"Unsupported QUEUE_TYPE: {queue_type}")


def _graceful_shutdown(signum, frame):
    logger.info("🛑 Shutdown signal received, stopping listener...")
    shutdown_event.set()


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def _start_rabbitmq_listener(callback):
    """Consume messages from RabbitMQ in batch with flush timeout."""
    credentials = pika.PlainCredentials(
        config.get_rabbitmq_user(),
        config.get_rabbitmq_password(),
    )
    parameters = pika.ConnectionParameters(
        host=config.get_rabbitmq_host(),
        port=config.get_rabbitmq_port(),
        virtual_host=config.get_rabbitmq_vhost(),
        credentials=credentials,
        blocked_connection_timeout=30,
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    queue_name = config.get_rabbitmq_queue()
    batch_size = config.get_batch_size()
    flush_timeout = config.get_flush_timeout()  # in seconds

    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=batch_size)

    message_batch = []
    last_flush_time = time.time()

    def on_message(ch, method, properties, body):
        nonlocal last_flush_time
        try:
            message = json.loads(body)
            message_batch.append((message, method.delivery_tag))
        except Exception:
            logger.exception("❌ Failed to parse RabbitMQ message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        now = time.time()
        if len(message_batch) >= batch_size or (now - last_flush_time) >= flush_timeout:
            try:
                payload = [m[0] for m in message_batch]
                callback(payload)
                for _, delivery_tag in message_batch:
                    ch.basic_ack(delivery_tag=delivery_tag)
                logger.info("✅ Processed and acknowledged %d RabbitMQ messages", len(message_batch))
            except Exception:
                logger.exception("❌ Batch processing failed, NACKing all messages")
                for _, delivery_tag in message_batch:
                    ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
            finally:
                message_batch.clear()
                last_flush_time = now

    channel.basic_consume(queue=queue_name, on_message_callback=on_message)

    logger.info("📡 Listening on RabbitMQ queue: %s", queue_name)
    try:
        while not shutdown_event.is_set():
            # ✅ Pyright-safe call
            connection.process_data_events(time_limit=1)
    finally:
        channel.stop_consuming()
        connection.close()


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def _start_sqs_listener(callback):
    """Poll SQS and process messages in batch with flush timeout."""
    queue_url = config.get_sqs_queue_url()
    region = config.get_sqs_region()
    polling_interval = config.get_polling_interval()
    batch_size = config.get_batch_size()
    flush_timeout = config.get_flush_timeout()

    try:
        sqs_client = boto3.client("sqs", region_name=region)
    except (BotoCoreError, NoCredentialsError) as e:
        logger.error("❌ Failed to initialize SQS client: %s", e)
        return

    message_batch = []
    receipt_handles = []
    last_flush_time = time.time()

    logger.info("📡 Polling SQS queue: %s", queue_url)

    while not shutdown_event.is_set():
        try:
            response = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=batch_size,
                WaitTimeSeconds=10,
            )
            messages = response.get("Messages", [])
            now = time.time()

            for msg in messages:
                try:
                    message = json.loads(msg["Body"])
                    message_batch.append(message)
                    receipt_handles.append(msg["ReceiptHandle"])
                except Exception:
                    logger.exception("❌ Failed to parse SQS message")

            if message_batch and (
                len(message_batch) >= batch_size or (now - last_flush_time) >= flush_timeout
            ):
                try:
                    callback(message_batch)
                    for handle in receipt_handles:
                        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=handle)
                    logger.info("✅ Processed and deleted %d SQS messages", len(message_batch))
                except Exception:
                    logger.exception("❌ SQS batch processing failed, messages left in queue")
                finally:
                    message_batch.clear()
                    receipt_handles.clear()
                    last_flush_time = now

        except Exception as e:
            logger.error("❌ SQS polling error: %s", e)
            time.sleep(polling_interval)
