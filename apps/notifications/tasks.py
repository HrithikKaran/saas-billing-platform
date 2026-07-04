from celery import shared_task


@shared_task
def send_invitation_email(
    email,
    token,
):
    print(f"Sending invitation " f"to {email}")

    print(f"Invitation token: {token}")

    return True
