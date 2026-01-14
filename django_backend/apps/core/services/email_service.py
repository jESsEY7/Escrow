"""
Email Service for the Escrow Platform.
Handles all transactional emails.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending transactional emails.
    Uses console backend in development, SMTP in production.
    """

    DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@escrow.com')

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        template_name: str = None,
        context: dict = None,
        plain_text: str = None,
        html_content: str = None,
    ):
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of template (without extension)
            context: Context for template rendering
            plain_text: Plain text content (if no template)
            html_content: HTML content (if no template)
        """
        try:
            if template_name:
                # Render from template
                html_content = cls._render_template(template_name, context or {})
                plain_text = strip_tags(html_content)
            
            if not plain_text and not html_content:
                raise ValueError("Either template_name or content must be provided")

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_text or strip_tags(html_content),
                from_email=cls.DEFAULT_FROM_EMAIL,
                to=[to_email] if isinstance(to_email, str) else to_email,
            )

            if html_content:
                email.attach_alternative(html_content, "text/html")

            email.send(fail_silently=False)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    def _render_template(cls, template_name: str, context: dict) -> str:
        """Render email template with context."""
        try:
            return render_to_string(f"email/{template_name}.html", context)
        except Exception:
            # Fallback to simple template
            return cls._simple_template(template_name, context)

    @classmethod
    def _simple_template(cls, template_name: str, context: dict) -> str:
        """Generate simple HTML if template not found."""
        title = context.get('title', 'Notification')
        message = context.get('message', '')
        action_url = context.get('action_url', '')
        action_text = context.get('action_text', 'View Details')

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #4f46e5; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Escrow Platform</h1>
                </div>
                <div class="content">
                    <h2>{title}</h2>
                    <p>{message}</p>
                    {'<a href="' + action_url + '" class="button">' + action_text + '</a>' if action_url else ''}
                </div>
                <div class="footer">
                    <p>This is an automated message from Escrow Platform.</p>
                </div>
            </div>
        </body>
        </html>
        """

    # Convenience methods for common email types

    @classmethod
    def send_escrow_created(cls, escrow):
        """Notify both parties about new escrow."""
        context = {
            'title': 'New Escrow Created',
            'message': f'A new escrow "{escrow.title}" has been created for {escrow.total_amount} {escrow.currency}.',
            'action_url': f'/escrow/{escrow.id}',
            'action_text': 'View Escrow',
            'escrow': escrow,
        }

        # Email buyer
        cls.send_email(
            to_email=escrow.buyer.email,
            subject=f'Escrow Created: {escrow.reference_code}',
            template_name='escrow_created',
            context={**context, 'recipient': escrow.buyer},
        )

        # Email seller if specified
        if escrow.seller:
            cls.send_email(
                to_email=escrow.seller.email,
                subject=f'You\'re invited to an escrow: {escrow.reference_code}',
                template_name='escrow_created',
                context={**context, 'recipient': escrow.seller},
            )

    @classmethod
    def send_escrow_funded(cls, escrow):
        """Notify seller that escrow is funded."""
        cls.send_email(
            to_email=escrow.seller.email,
            subject=f'Escrow Funded: {escrow.reference_code}',
            template_name='escrow_funded',
            context={
                'title': 'Escrow Has Been Funded!',
                'message': f'The escrow "{escrow.title}" has been funded with {escrow.total_amount} {escrow.currency}. You can now proceed with the work.',
                'escrow': escrow,
                'recipient': escrow.seller,
            },
        )

    @classmethod
    def send_milestone_completed(cls, milestone):
        """Notify buyer that milestone is submitted."""
        escrow = milestone.escrow
        cls.send_email(
            to_email=escrow.buyer.email,
            subject=f'Milestone Submitted: {milestone.title}',
            template_name='milestone_complete',
            context={
                'title': 'Milestone Submitted for Review',
                'message': f'The seller has completed milestone "{milestone.title}". Please review and approve.',
                'action_url': f'/escrow/{escrow.id}',
                'action_text': 'Review Milestone',
                'milestone': milestone,
                'escrow': escrow,
            },
        )

    @classmethod
    def send_dispute_raised(cls, dispute):
        """Notify all parties about dispute."""
        escrow = dispute.escrow
        recipients = [escrow.buyer.email, escrow.seller.email]

        for email in recipients:
            cls.send_email(
                to_email=email,
                subject=f'Dispute Raised: {escrow.reference_code}',
                template_name='dispute_raised',
                context={
                    'title': 'A Dispute Has Been Raised',
                    'message': f'A dispute has been raised on escrow "{escrow.title}". Reason: {dispute.reason}',
                    'action_url': f'/disputes/{dispute.id}',
                    'action_text': 'View Dispute',
                    'dispute': dispute,
                    'escrow': escrow,
                },
            )

    @classmethod
    def send_ruling_made(cls, decision):
        """Notify parties about arbitration ruling."""
        dispute = decision.dispute
        escrow = dispute.escrow

        for user in [escrow.buyer, escrow.seller]:
            cls.send_email(
                to_email=user.email,
                subject=f'Arbitration Ruling: {escrow.reference_code}',
                template_name='ruling_made',
                context={
                    'title': 'Arbitration Decision Made',
                    'message': f'The arbitrator has made a ruling on your dispute. Ruling: {decision.ruling}',
                    'action_url': f'/disputes/{dispute.id}',
                    'action_text': 'View Ruling',
                    'decision': decision,
                    'dispute': dispute,
                    'escrow': escrow,
                    'recipient': user,
                },
            )

    @classmethod
    def send_password_reset(cls, user, reset_url):
        """Send password reset email."""
        cls.send_email(
            to_email=user.email,
            subject='Password Reset Request',
            template_name='password_reset',
            context={
                'title': 'Reset Your Password',
                'message': 'Click the button below to reset your password. This link expires in 1 hour.',
                'action_url': reset_url,
                'action_text': 'Reset Password',
                'user': user,
            },
        )

    @classmethod
    def send_welcome(cls, user):
        """Send welcome email to new user."""
        cls.send_email(
            to_email=user.email,
            subject='Welcome to Escrow Platform',
            template_name='welcome',
            context={
                'title': 'Welcome to Escrow Platform!',
                'message': 'Your account has been created successfully. Start by creating your first escrow or completing your profile.',
                'action_url': '/dashboard',
                'action_text': 'Go to Dashboard',
                'user': user,
            },
        )


# Singleton instance
email_service = EmailService()
