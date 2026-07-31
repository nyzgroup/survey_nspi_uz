from celery import shared_task
from django.conf import settings
from django.utils import timezone
import logging
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from .services.hemis_api_service import HemisAPIClient, APIClientException
from .models import Student
from .utils import map_api_data_to_student_model_defaults, update_student_instance_with_defaults

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='auth_app.tasks.sync_student_profile_from_api', max_retries=3, default_retry_delay=60 * 5)
def sync_student_profile_from_api(self, student_id, api_token=None):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        logger.error(f"Student with ID {student_id} not found in Celery task. Task will not retry.")
        return f"Student ID {student_id} not found."
    
    effective_api_token = api_token
    api_source_description = f"provided token for student {student.username}"

    if not effective_api_token:
        if hasattr(settings, 'HEMIS_SYSTEM_API_TOKEN') and settings.HEMIS_SYSTEM_API_TOKEN:
             effective_api_token = settings.HEMIS_SYSTEM_API_TOKEN
             api_source_description = f"system token for student {student.username} (ID: {student.student_id_number or student.username})"
             logger.warning(f"Using HEMIS_SYSTEM_API_TOKEN for task, but get_account_me() might fetch system user's data, not student's, unless API is specifically designed for it or client uses student_id_number with this token.")
        else:
            logger.error(f"No API token provided for student ID {student_id} (username: {student.username}) in Celery task, and no system token configured.")
            return f"API token required for student ID {student_id}."
    
    try:
        client = HemisAPIClient(api_token=effective_api_token)
        student_info_from_api = client.get_account_me()

        if student_info_from_api and isinstance(student_info_from_api, dict):
            defaults = map_api_data_to_student_model_defaults(
                student_info_from_api, 
                student.username
            )
            if defaults:
                update_student_instance_with_defaults(student, defaults)
                logger.info(f"Successfully updated profile using {api_source_description} via Celery task.")
                return f"Student ID {student_id} updated."
            else:
                logger.warning(f"Could not map API data for student ID {student_id} in Celery task. API data: {str(student_info_from_api)[:200]}")
                return f"Failed to map API data for student ID {student_id}."
        elif not student_info_from_api:
            logger.warning(f"No data received from API for student ID {student_id} (username: {student.username}) using {api_source_description} in Celery task.")
            return f"No API data for student ID {student_id}."
        else:
            logger.warning(f"Received non-dict data from API for student ID {student_id} using {api_source_description} in Celery task: {str(student_info_from_api)[:100]}")
            return f"Invalid API data type for student ID {student_id}."
    except APIClientException as e:
        logger.error(f"APIClientException for student ID {student_id} (username: {student.username}) using {api_source_description} in Celery task: {e.args[0]} (Status: {e.status_code})", exc_info=True)
        try:
            if e.status_code in [401, 403]:
                logger.warning(f"Token-related API error ({e.status_code}) for student {student.username}. Not retrying.")
                return f"Token error for student {student.username}."
            raise self.retry(exc=e, countdown=int(self.default_retry_delay * (2 ** self.request.retries)))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for student ID {student_id} (username: {student.username}) in Celery task after APIClientException.")
            return f"Max retries for student {student.username} (APIClientException)."
    except Exception as e:
        logger.error(f"Unexpected error updating student ID {student_id} (username: {student.username}) using {api_source_description} in Celery task: {e}", exc_info=True)
        try:
            raise self.retry(exc=e, countdown=int(self.default_retry_delay * (2 ** self.request.retries)))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for student ID {student_id} (username: {student.username}) in Celery task after unexpected error.")
            return f"Max retries for student {student.username} (unexpected error)."


@shared_task(bind=True, name='auth_app.tasks.generate_message_qr_code', max_retries=3, default_retry_delay=30)
def generate_message_qr_code(self, object_id, object_type):
    """
    MessageToResponsible yoki MessageReply uchun QR kod rasmini asinxron yaratadi.
    object_type: 'message' yoki 'reply'
    """
    from .models import MessageToResponsible, MessageReply

    try:
        if object_type == 'message':
            obj = MessageToResponsible.objects.get(pk=object_id)
            code_value = obj.unique_code
            file_prefix = f"message_{object_id}"
            field_name = 'qr_code_image'
        elif object_type == 'reply':
            obj = MessageReply.objects.get(pk=object_id)
            code_value = obj.unique_code
            file_prefix = f"reply_{object_id}"
            field_name = 'qr_code_image'
        else:
            logger.error(f"Unknown object_type '{object_type}' in generate_message_qr_code task.")
            return f"Unknown object_type: {object_type}"

        if getattr(obj, field_name):
            return f"QR code already exists for {object_type} ID {object_id}."

        qr = qrcode.make(code_value)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        file_name = f"{file_prefix}_qr.png"
        getattr(obj, field_name).save(file_name, ContentFile(buffer.getvalue()), save=True)
        logger.info(f"QR code generated for {object_type} ID {object_id}.")
        return f"QR code generated for {object_type} ID {object_id}."

    except (MessageToResponsible.DoesNotExist, MessageReply.DoesNotExist):
        logger.error(f"{object_type} ID {object_id} not found for QR code generation.")
        return f"{object_type} ID {object_id} not found."
    except Exception as e:
        logger.error(f"Error generating QR code for {object_type} ID {object_id}: {e}", exc_info=True)
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for QR code generation of {object_type} ID {object_id}.")
            return f"Max retries for QR code {object_type} ID {object_id}."