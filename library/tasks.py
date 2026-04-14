from celery import shared_task
from django.core.management import call_command


@shared_task
def run_update_daily_totals():
    call_command('update_daily_totals')