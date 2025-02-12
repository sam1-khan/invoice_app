from ninja import NinjaAPI
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.views.decorators.cache import cache_page
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from typing import List
from ninja.security import django_auth
from ninja.pagination import paginate
from .models import InvoiceOwner, Client, Invoice, InvoiceItem
from .schemas import (
    LoginSchema,
    InvoiceOwnerCreate,
    InvoiceOwnerUpdate,
    InvoiceOwnerOut,
    ClientCreate,
    ClientUpdate,
    ClientOut,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceOut,
    InvoiceItemCreate,
    InvoiceItemUpdate,
    InvoiceItemOut,
    ResetPasswordSchema,
    ForgotPasswordRequestSchema,
)

# Initialize API with session-based authentication (using django_auth)
api = NinjaAPI(title="Invoice Generator API", version="1.0.0", auth=django_auth)

# -------------------------
# Authentication & Rate Limiting
# -------------------------

@api.post("/auth/register/", response={201: InvoiceOwnerOut}, auth=None)
@ratelimit(key='ip', rate='100/m', block=True)  # 100 requests/minute
def register_invoice_owner(request, payload: InvoiceOwnerCreate):
    if InvoiceOwner.objects.filter(email=payload.email).exists():
        return 400, {"detail": "Email is already in use"}
    
    user = InvoiceOwner.objects.create(**payload.dict(exclude={"password"}))
    user.set_password(payload.password)
    user.save()
    return 201, user

@api.post("/auth/login/", response={200: dict, 401: dict}, auth=None)
@ratelimit(key='ip', rate='100/m', block=True)
def login(request, payload: LoginSchema):
    user = authenticate(request, email=payload.email, password=payload.password)
    if user:
        django_login(request, user)
        return 200, {"detail": "Successfully logged in."}
    return 401, {"detail": "Invalid credentials"}

@api.post("/auth/logout/", response={200: dict}, auth=django_auth)
def logout(request):
    django_logout(request)
    return 200, {"detail": "Successfully logged out."}

# -------------------------
# InvoiceOwner Endpoints
# -------------------------

@cache_page(60 * 5)  # Must be the outermost decorator!
@paginate
@api.get("/invoice-owners/", response=List[InvoiceOwnerOut], auth=django_auth)
def list_invoice_owners(request):
    if request.user.is_staff:
        return InvoiceOwner.objects.all()
    return InvoiceOwner.objects.filter(id=request.user.id)

@api.get("/invoice-owners/{id}/", response=InvoiceOwnerOut, auth=django_auth)
def get_invoice_owner(request, id: int):
    if not request.user.is_staff and id != request.user.id:
        return 403, {"detail": "You do not have permission to view this user."}
    return get_object_or_404(InvoiceOwner, id=id)

@api.patch("/invoice-owners/{id}/", response=InvoiceOwnerOut, auth=django_auth)
def partial_update_invoice_owner(request, id: int, payload: InvoiceOwnerUpdate):
    if not request.user.is_staff and id != request.user.id:
        return 403, {"detail": "You do not have permission to update this user."}
    user = get_object_or_404(InvoiceOwner, id=id)
    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(user, attr, value)
    user.save()
    return user

@api.delete("/invoice-owners/{id}/", response={204: None}, auth=django_auth)
def delete_invoice_owner(request, id: int):
    if not request.user.is_staff and id != request.user.id:
        return 403, {"detail": "You do not have permission to delete this user."}
    user = get_object_or_404(InvoiceOwner, id=id)
    user.delete()
    return 204, None

# -------------------------
# Client Endpoints
# -------------------------

@cache_page(60 * 5)
@paginate
@api.get("/clients/", response=List[ClientOut], auth=django_auth)
def list_clients(request):
    if request.user.is_staff:
        return Client.objects.all()
    return Client.objects.filter(invoice_owner_id=request.user.id)

@api.post("/clients/", response={201: ClientOut}, auth=django_auth)
def create_client(request, payload: ClientCreate):
    # For non-admins, always associate with the current user.
    client = Client.objects.create(invoice_owner=request.user, **payload.dict())
    return 201, client

@api.get("/clients/{id}/", response=ClientOut, auth=django_auth)
def get_client(request, id: int):
    if request.user.is_staff:
        return get_object_or_404(Client, id=id)
    return get_object_or_404(Client, id=id, invoice_owner_id=request.user.id)

@api.patch("/clients/{id}/", response=ClientOut, auth=django_auth)
def partial_update_client(request, id: int, payload: ClientUpdate):
    if request.user.is_staff:
        client = get_object_or_404(Client, id=id)
    else:
        client = get_object_or_404(Client, id=id, invoice_owner_id=request.user.id)
    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(client, attr, value)
    client.save()
    return client

@api.delete("/clients/{id}/", response={204: None}, auth=django_auth)
def delete_client(request, id: int):
    if request.user.is_staff:
        client = get_object_or_404(Client, id=id)
    else:
        client = get_object_or_404(Client, id=id, invoice_owner_id=request.user.id)
    client.delete()
    return 204, None

# -------------------------
# Invoice Endpoints
# -------------------------

@cache_page(60 * 5)
@paginate
@api.get("/invoices/", response=List[InvoiceOut], auth=django_auth)
def list_invoices(request):
    if request.user.is_staff:
        return Invoice.objects.all()
    return Invoice.objects.filter(invoice_owner=request.user)

@api.post("/invoices/", response={201: InvoiceOut}, auth=django_auth)
def create_invoice(request, payload: InvoiceCreate):
    invoice = Invoice.objects.create(invoice_owner=request.user, **payload.dict())
    return 201, invoice

@api.get("/invoices/{id}/", response=InvoiceOut, auth=django_auth)
def get_invoice(request, id: int):
    if request.user.is_staff:
        return get_object_or_404(Invoice, id=id)
    return get_object_or_404(Invoice, id=id, invoice_owner=request.user)

@api.patch("/invoices/{id}/", response=InvoiceOut, auth=django_auth)
def update_invoice(request, id: int, payload: InvoiceUpdate):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=id)
    else:
        invoice = get_object_or_404(Invoice, id=id, invoice_owner=request.user)
    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(invoice, attr, value)
    invoice.save()
    return invoice

@api.delete("/invoices/{id}/", response={204: None}, auth=django_auth)
def delete_invoice(request, id: int):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=id)
    else:
        invoice = get_object_or_404(Invoice, id=id, invoice_owner=request.user)
    invoice.delete()
    return 204, None

# -------------------------
# InvoiceItem Endpoints
# -------------------------

@api.get("/invoices/{invoice_id}/items/", response=List[InvoiceItemOut], auth=django_auth)
def list_invoice_items(request, invoice_id: int):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, invoice_owner=request.user)
    return InvoiceItem.objects.filter(invoice=invoice)

@api.post("/invoices/{invoice_id}/items/", response={201: InvoiceItemOut}, auth=django_auth)
def create_invoice_item(request, invoice_id: int, payload: InvoiceItemCreate):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, invoice_owner=request.user)
    item = InvoiceItem.objects.create(invoice=invoice, **payload.dict())
    return 201, item

@api.get("/invoices/{invoice_id}/items/{id}/", response=InvoiceItemOut, auth=django_auth)
def get_invoice_item(request, invoice_id: int, id: int):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, invoice_owner=request.user)
    return get_object_or_404(InvoiceItem, id=id, invoice=invoice)

@api.patch("/invoices/{invoice_id}/items/{id}/", response=InvoiceItemOut, auth=django_auth)
def update_invoice_item(request, invoice_id: int, id: int, payload: InvoiceItemUpdate):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, invoice_owner=request.user)
    item = get_object_or_404(InvoiceItem, id=id, invoice=invoice)
    data = payload.dict(exclude_unset=True)
    for attr, value in data.items():
        setattr(item, attr, value)
    item.save()
    return item

@api.delete("/invoices/{invoice_id}/items/{id}/", response={204: None}, auth=django_auth)
def delete_invoice_item(request, invoice_id: int, id: int):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, id=invoice_id)
    else:
        invoice = get_object_or_404(Invoice, id=invoice_id, invoice_owner=request.user)
    item = get_object_or_404(InvoiceItem, id=id, invoice=invoice)
    item.delete()
    return 204, None

# -------------------------
# Forgot Password Flow (public endpoints)
# -------------------------

@api.post("/auth/forgot-password/", auth=None)
@ratelimit(key='ip', rate='5/m', block=True)
def request_password_reset(request, payload: ForgotPasswordRequestSchema):
    email = payload.email.lower().strip()
    try:
        user = InvoiceOwner.objects.get(email=email)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}"
        context = {"reset_link": reset_link, "user": user}
        html_message = render_to_string("emails/password_reset_email.html", context)
        plain_message = strip_tags(html_message)
        user.email_user(subject="Password Reset Request", message=plain_message, html_message=html_message)
    except InvoiceOwner.DoesNotExist:
        pass  # Prevent email enumeration
    return 200, {"detail": "If the email exists, a password reset link has been sent."}

@api.post("/auth/reset-password/", auth=None)
@ratelimit(key='ip', rate='5/m', block=True)
def reset_password(request, payload: ResetPasswordSchema):
    try:
        user_id = force_str(urlsafe_base64_decode(payload.uidb64))
        user = InvoiceOwner.objects.get(id=user_id)
    except (InvoiceOwner.DoesNotExist, ValueError, TypeError):
        return 400, {"detail": "Invalid or expired token."}

    if not default_token_generator.check_token(user, payload.token):
        return 400, {"detail": "Invalid or expired token."}

    if payload.new_password != payload.confirm_password:
        return 400, {"detail": "Passwords do not match."}

    try:
        validate_password(payload.new_password, user)
    except ValidationError as e:
        return 400, {"detail": e.messages}

    user.set_password(payload.new_password)
    user.save()
    return 200, {"detail": "Password has been reset successfully."}