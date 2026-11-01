from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone

from .models import (
    Address, AuditLog, Booking, Business, BusinessAvailability,
    BusinessMembership, BusinessVerification, Category, Complaint,
    Conversation, Favorite, InventoryMovement, Message, Notification,
    Order, OrderItem, OrderReceiptDelivery, Payment, Product, Refund,
    Review, Service,
)


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'category', 'price', 'vat_category', 'stock', 'active')


class VerificationInline(admin.TabularInline):
    model = BusinessVerification
    extra = 0
    fields = ('document_type', 'document', 'status', 'reviewed_by', 'reviewed_at')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    actions = ('approve_applications', 'reject_applications', 'return_to_review', 'activate_verified_businesses', 'deactivate_businesses')
    change_form_template = 'admin/commerce/business/change_form.html'
    readonly_fields = ('verification_status',)
    inlines = (ProductInline, VerificationInline)
    list_display = ('name', 'owner', 'district', 'tax_registration', 'ebm_status', 'verification_status', 'active')
    list_filter = ('tax_registration', 'ebm_status', 'ebm_solution', 'verification_status', 'active')
    search_fields = ('name', 'slug', 'vat_tin', 'owner__username')
    fieldsets = (
        ('Business details', {'fields': ('owner', 'name', 'slug', 'description', 'category', 'district', 'sector', 'phone', 'email', 'address', 'verification_status', 'review_notes', 'active')}),
        ('Tax profile', {'fields': ('tax_registration', 'vat_tin', 'prices_include_vat'), 'description': 'Only mark VAT registration after verifying the business tax documents. The TIN is private and is not returned by public APIs.'}),
        ('RRA EBM credentials and approval', {'fields': ('ebm_status', 'ebm_solution', 'ebm_approval_reference', 'ebm_machine_code', 'ebm_sdc_id'), 'description': 'Enter these values only after RRA has approved and provisioned the taxpayer integration. Secrets and certificates must be stored in deployment secret storage, not in this form.'}),
        ('Payment methods', {'fields': ('cash_enabled', 'mobile_money_enabled')}),
    )

    def _approve_business(self, request, business):
        documents = list(business.verification_documents.values_list('document_type', 'status'))
        approved_docs = {document_type for document_type, state in documents if state == BusinessVerification.Status.APPROVED}
        pending_docs = {document_type for document_type, state in documents if state == BusinessVerification.Status.PENDING}
        rejected_docs = {document_type for document_type, state in documents if state == BusinessVerification.Status.REJECTED}
        missing = []
        registration_types = {BusinessVerification.DocumentType.RDB_REGISTRATION, BusinessVerification.DocumentType.TIN_CERTIFICATE}
        if not (registration_types & approved_docs):
            if registration_types & pending_docs:
                missing.append('RDB registration/TIN certificate is uploaded but still pending review in Business verifications')
            elif registration_types & rejected_docs:
                missing.append('RDB registration/TIN certificate was rejected; upload a replacement and review it')
            else:
                missing.append('upload an RDB registration or TIN certificate and approve it in Business verifications')
        owner_id_type = BusinessVerification.DocumentType.OWNER_ID
        if owner_id_type not in approved_docs:
            if owner_id_type in pending_docs:
                missing.append('owner ID/passport is uploaded but still pending review in Business verifications')
            elif owner_id_type in rejected_docs:
                missing.append('owner ID/passport was rejected; upload a replacement and review it')
            else:
                missing.append('upload an owner ID/passport and approve it in Business verifications')
        if business.tax_registration == Business.TaxRegistration.VAT_REGISTERED:
            if not business.vat_tin:
                missing.append('VAT TIN')
            vat_certificate_type = BusinessVerification.DocumentType.VAT_CERTIFICATE
            if vat_certificate_type not in approved_docs:
                if vat_certificate_type in pending_docs:
                    missing.append('VAT certificate is uploaded but still pending review in Business verifications')
                elif vat_certificate_type in rejected_docs:
                    missing.append('VAT certificate was rejected; upload a replacement and review it')
                else:
                    missing.append('upload a VAT certificate and approve it in Business verifications')
        if missing:
            self.message_user(request, f"{business.name}: missing {', '.join(missing)}.", messages.ERROR)
            return False
        business.verification_status = Business.Verification.VERIFIED
        business.review_notes = ''
        business.active = True
        business.save(update_fields=('verification_status', 'review_notes', 'active'))
        AuditLog.objects.create(actor=request.user, action='business_application_approved', object_type='Business', object_id=str(business.pk), detail={'business': business.name})
        self.message_user(request, f'{business.name} was approved and is now active.', messages.SUCCESS)
        return True

    @admin.action(description='Approve selected applications (requires approved documents)')
    def approve_applications(self, request, queryset):
        for business in queryset:
            self._approve_business(request, business)

    @admin.action(description='Reject selected applications (add review notes first)')
    def reject_applications(self, request, queryset):
        rejected_count = 0
        for business in queryset:
            if not business.review_notes.strip():
                self.message_user(request, f'{business.name}: add a review note before rejecting.', messages.ERROR)
                continue
            business.verification_status = Business.Verification.REJECTED
            business.active = False
            business.save(update_fields=('verification_status', 'active'))
            AuditLog.objects.create(actor=request.user, action='business_application_rejected', object_type='Business', object_id=str(business.pk), detail={'business': business.name, 'review_notes': business.review_notes})
            rejected_count += 1
        if rejected_count:
            self.message_user(request, f'{rejected_count} business application(s) rejected.', messages.SUCCESS)

    @admin.action(description='Return selected businesses to pending review (add review notes first)')
    def return_to_review(self, request, queryset):
        count = 0
        for business in queryset:
            if not business.review_notes.strip():
                self.message_user(request, f'{business.name}: add a review note before returning it to review.', messages.ERROR)
                continue
            business.verification_status = Business.Verification.PENDING
            business.active = False
            business.save(update_fields=('verification_status', 'active'))
            AuditLog.objects.create(actor=request.user, action='business_returned_to_review', object_type='Business', object_id=str(business.pk), detail={'business': business.name, 'review_notes': business.review_notes})
            count += 1
        if count:
            self.message_user(request, f'{count} business(es) returned to pending review and deactivated.', messages.SUCCESS)

    @admin.action(description='Activate selected verified businesses')
    def activate_verified_businesses(self, request, queryset):
        count = 0
        for business in queryset:
            if business.verification_status != Business.Verification.VERIFIED:
                self.message_user(request, f'{business.name}: approve verification before activation.', messages.ERROR)
                continue
            if not business.active:
                business.active = True
                business.save(update_fields=('active',))
                AuditLog.objects.create(actor=request.user, action='business_activated', object_type='Business', object_id=str(business.pk), detail={'business': business.name})
            count += 1
        if count:
            self.message_user(request, f'{count} verified business(es) activated.', messages.SUCCESS)

    @admin.action(description='Deactivate selected businesses')
    def deactivate_businesses(self, request, queryset):
        count = 0
        for business in queryset:
            if business.active:
                business.active = False
                business.save(update_fields=('active',))
                AuditLog.objects.create(actor=request.user, action='business_deactivated', object_type='Business', object_id=str(business.pk), detail={'business': business.name})
            count += 1
        if count:
            self.message_user(request, f'{count} business(es) deactivated. Verification status was left unchanged.', messages.SUCCESS)

    def response_change(self, request, obj):
        if '_approve_application' in request.POST:
            self._approve_business(request, obj)
            return HttpResponseRedirect(reverse('admin:commerce_business_change', args=(obj.pk,)))
        if '_reject_application' in request.POST:
            if obj.review_notes.strip():
                obj.verification_status = Business.Verification.REJECTED
                obj.active = False
                obj.save(update_fields=('verification_status', 'active'))
                AuditLog.objects.create(actor=request.user, action='business_application_rejected', object_type='Business', object_id=str(obj.pk), detail={'business': obj.name, 'review_notes': obj.review_notes})
                self.message_user(request, f'{obj.name} was rejected.', messages.SUCCESS)
            else:
                self.message_user(request, 'Add an administrator review note before rejecting this application.', messages.ERROR)
            return HttpResponseRedirect(reverse('admin:commerce_business_change', args=(obj.pk,)))
        return super().response_change(request, obj)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'price', 'vat_category', 'stock', 'active')
    list_filter = ('vat_category', 'active', 'category')
    search_fields = ('name', 'business__name')
    fieldsets = (
        ('Product details', {'fields': ('business', 'category', 'name', 'description', 'price', 'stock', 'image_url', 'active')}),
        ('Tax classification', {'fields': ('vat_category',), 'description': 'Choose the classification supported by the seller’s tax records. Do not assume all goods are standard rated.'}),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'price', 'vat_category', 'capacity', 'active')
    list_filter = ('vat_category', 'active')
    search_fields = ('name', 'business__name')
    fieldsets = (
        ('Service details', {'fields': ('business', 'name', 'description', 'price', 'capacity', 'active')}),
        ('Tax classification', {'fields': ('vat_category',)}),
    )


@admin.register(BusinessVerification)
class BusinessVerificationAdmin(admin.ModelAdmin):
    list_display = ('business', 'document_type', 'status', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'document_type')
    search_fields = ('business__name', 'document_type')
    actions = ('approve_documents', 'reject_documents')
    readonly_fields = ('status', 'reviewed_by', 'reviewed_at')

    def save_model(self, request, obj, form, change):
        if change:
            previous = BusinessVerification.objects.get(pk=obj.pk)
            if previous.document != obj.document or previous.document_type != obj.document_type:
                obj.status = BusinessVerification.Status.PENDING
                obj.reviewed_by = None
                obj.reviewed_at = None
                obj.business.verification_status = Business.Verification.PENDING
                obj.business.active = False
                obj.business.save(update_fields=('verification_status', 'active'))
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None): return False

    @admin.action(description='Mark selected documents approved')
    def approve_documents(self, request, queryset):
        queryset.update(status=BusinessVerification.Status.APPROVED, reviewed_by=request.user, reviewed_at=timezone.now())

    @admin.action(description='Mark selected documents rejected')
    def reject_documents(self, request, queryset):
        queryset.update(status=BusinessVerification.Status.REJECTED, reviewed_by=request.user, reviewed_at=timezone.now())


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'status', 'payment_method', 'subtotal', 'tax_total', 'total', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('reference', 'guest_name', 'guest_email', 'guest_phone')
    readonly_fields = ('reference', 'customer', 'guest_name', 'guest_email', 'guest_phone', 'status', 'payment_method', 'subtotal', 'tax_total', 'delivery_fee', 'total', 'delivery_address', 'created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'business', 'product_name', 'quantity', 'unit_price', 'vat_category', 'vat_rate', 'vat_amount', 'line_total')
    list_filter = ('vat_category', 'vat_rate')
    search_fields = ('order__reference', 'product_name', 'business__name')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


for model in [
    Category, BusinessMembership, InventoryMovement, Address, OrderReceiptDelivery,
    Payment, Refund, BusinessAvailability, Review, Favorite,
    Notification, Conversation, Message, Complaint, AuditLog,
]:
    admin.site.register(model)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('reference', 'service', 'party_size', 'subtotal', 'vat_amount', 'total', 'status', 'starts_at')
    list_filter = ('status', 'vat_category', 'starts_at')
    search_fields = ('reference', 'guest_name', 'guest_phone', 'service__name')
    readonly_fields = ('reference', 'service', 'customer', 'guest_name', 'guest_phone', 'starts_at', 'ends_at', 'party_size', 'unit_price', 'subtotal', 'vat_category', 'vat_rate', 'vat_amount', 'vat_included', 'total', 'notes', 'created_at')
