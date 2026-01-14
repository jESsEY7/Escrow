"""
Core enums for the Escrow Platform.
Centralized enum definitions for type safety and consistency.
"""
from django.db import models


class UserRole(models.TextChoices):
    BUYER = 'buyer', 'Buyer'
    SELLER = 'seller', 'Seller'
    ADMIN = 'admin', 'Administrator'
    ARBITRATOR = 'arbitrator', 'Arbitrator'
    AUDITOR = 'auditor', 'Auditor'


class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    PENDING_VERIFICATION = 'pending_verification', 'Pending Verification'
    DEACTIVATED = 'deactivated', 'Deactivated'


class KYCStatus(models.TextChoices):
    NOT_STARTED = 'not_started', 'Not Started'
    PENDING = 'pending', 'Pending Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    EXPIRED = 'expired', 'Expired'


class EscrowStatus(models.TextChoices):
    CREATED = 'created', 'Created'
    FUNDED = 'funded', 'Funded'
    IN_VERIFICATION = 'in_verification', 'In Verification'
    MILESTONE_PENDING = 'milestone_pending', 'Milestone Pending'
    PARTIALLY_RELEASED = 'partially_released', 'Partially Released'
    FULLY_RELEASED = 'fully_released', 'Fully Released'
    DISPUTED = 'disputed', 'Disputed'
    RESOLVED = 'resolved', 'Resolved'
    REFUNDED = 'refunded', 'Refunded'
    CANCELLED = 'cancelled', 'Cancelled'
    CLOSED = 'closed', 'Closed'


class EscrowType(models.TextChoices):
    FREELANCE = 'freelance', 'Freelance Contract'
    ECOMMERCE = 'ecommerce', 'E-Commerce'
    REAL_ESTATE = 'real_estate', 'Real Estate'
    VEHICLE = 'vehicle', 'Vehicle Transaction'
    DIGITAL_SERVICE = 'digital_service', 'Digital Service'
    GENERAL = 'general', 'General Transaction'


class MilestoneStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    SUBMITTED = 'submitted', 'Submitted for Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    RELEASED = 'released', 'Released'


class TransactionType(models.TextChoices):
    DEPOSIT = 'deposit', 'Deposit'
    RELEASE = 'release', 'Release'
    PARTIAL_RELEASE = 'partial_release', 'Partial Release'
    REFUND = 'refund', 'Refund'
    FEE = 'fee', 'Platform Fee'
    ADJUSTMENT = 'adjustment', 'Adjustment'


class TransactionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    REVERSED = 'reversed', 'Reversed'


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    CREDIT_CARD = 'credit_card', 'Credit Card'
    DEBIT_CARD = 'debit_card', 'Debit Card'
    MPESA = 'mpesa', 'M-Pesa'
    PAYPAL = 'paypal', 'PayPal'
    CRYPTO = 'crypto', 'Cryptocurrency'
    WIRE_TRANSFER = 'wire_transfer', 'Wire Transfer'


class DisputeStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    UNDER_REVIEW = 'under_review', 'Under Review'
    AWAITING_EVIDENCE = 'awaiting_evidence', 'Awaiting Evidence'
    ARBITRATION = 'arbitration', 'In Arbitration'
    RESOLVED = 'resolved', 'Resolved'
    ESCALATED = 'escalated', 'Escalated'
    CLOSED = 'closed', 'Closed'


class DisputeReason(models.TextChoices):
    NOT_AS_DESCRIBED = 'not_as_described', 'Item Not As Described'
    NOT_RECEIVED = 'not_received', 'Item Not Received'
    QUALITY_ISSUE = 'quality_issue', 'Quality Issue'
    INCOMPLETE_WORK = 'incomplete_work', 'Incomplete Work'
    LATE_DELIVERY = 'late_delivery', 'Late Delivery'
    FRAUD = 'fraud', 'Suspected Fraud'
    OTHER = 'other', 'Other'


class RulingType(models.TextChoices):
    FAVOR_BUYER = 'favor_buyer', 'Favor Buyer (Full Refund)'
    FAVOR_SELLER = 'favor_seller', 'Favor Seller (Full Release)'
    SPLIT = 'split', 'Split Decision'
    PARTIAL_REFUND = 'partial_refund', 'Partial Refund'
    MUTUAL_CANCELLATION = 'mutual_cancellation', 'Mutual Cancellation'


class AuditAction(models.TextChoices):
    CREATE = 'create', 'Create'
    UPDATE = 'update', 'Update'
    DELETE = 'delete', 'Delete'
    LOGIN = 'login', 'Login'
    LOGOUT = 'logout', 'Logout'
    FUND = 'fund', 'Fund'
    RELEASE = 'release', 'Release'
    REFUND = 'refund', 'Refund'
    DISPUTE_RAISED = 'dispute_raised', 'Dispute Raised'
    DISPUTE_RESOLVED = 'dispute_resolved', 'Dispute Resolved'
    KYC_SUBMITTED = 'kyc_submitted', 'KYC Submitted'
    KYC_APPROVED = 'kyc_approved', 'KYC Approved'
    KYC_REJECTED = 'kyc_rejected', 'KYC Rejected'


class Currency(models.TextChoices):
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    GBP = 'GBP', 'British Pound'
    KES = 'KES', 'Kenyan Shilling'
    NGN = 'NGN', 'Nigerian Naira'
    ZAR = 'ZAR', 'South African Rand'
