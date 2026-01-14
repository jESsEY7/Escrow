from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging
from .models import ContactRequest

logger = logging.getLogger(__name__)

class ContactView(APIView):
    """
    Handle contact form submissions.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        logger.info(f"Contact Form Submission: {data}")
        
        try:
            # Map frontend camelCase to snake_case if necessary, or ensure frontend sends snake_case
            # Frontend sends: firstName, lastName, email, transactionType, transactionValue, message, phoneNumber
            contact_request = ContactRequest.objects.create(
                first_name=data.get('firstName', ''),
                last_name=data.get('lastName', ''),
                email=data.get('email', ''),
                phone_number=data.get('phoneNumber', ''),
                transaction_type=data.get('transactionType', ''),
                transaction_value=data.get('transactionValue', ''),
                message=data.get('message', '')
            )
            
            return Response({
                "message": "Thank you for contacting us. We will get back to you shortly.",
                "success": True,
                "id": str(contact_request.id)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error saving contact request: {str(e)}")
            return Response({
                "message": "An error occurred while processing your request.",
                "success": False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
