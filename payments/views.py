import decimal
import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

from transbank.webpay.webpay_plus.transaction import Transaction

from .models import Donation

logger = logging.getLogger(__name__)
MIN_AMOUNT = decimal.Decimal(str(getattr(settings, "DONATION_MIN_CLP", 500)))
AMOUNT_STEP = decimal.Decimal("1")

try:
    from transbank.common.options import WebpayOptions as WebpayOptions
except ImportError:
    try:
        from transbank.common.options import Options as WebpayOptions
    except ImportError:  # pragma: no cover - fallback para SDK antiguos
        from transbank.common import Options as WebpayOptions  # type: ignore

try:
    from transbank.common.integration_api_keys import IntegrationApiKeys
    from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
    from transbank.common.integration_type import IntegrationType
except ImportError:  # pragma: no cover - fallback para SDK antiguos
    from transbank.common import (  # type: ignore
        IntegrationApiKeys,
        IntegrationCommerceCodes,
        IntegrationType,
    )


def _tbk_options():
    """Configura el SDK de Transbank de acuerdo al ambiente."""
    environment = getattr(settings, "TBK_ENV", "integration")
    if environment == "production":
        return WebpayOptions(
            settings.TBK_API_KEY_ID,
            settings.TBK_API_KEY_SECRET,
            IntegrationType.LIVE,
        )
    return WebpayOptions(
        IntegrationCommerceCodes.WEBPAY_PLUS,
        IntegrationApiKeys.WEBPAY,
        IntegrationType.TEST,
    )


@csrf_protect
@login_required(login_url="login")
def donation_form(request):
    """Muestra y procesa el formulario de donaciones."""
    if request.method == "GET":
        return render(
            request,
            "donations/form.html",
            {"donation_min_amount": int(MIN_AMOUNT)},
        )

    amount_raw = (request.POST.get("amount") or "").strip()
    try:
        amount = decimal.Decimal(amount_raw).quantize(AMOUNT_STEP, rounding=decimal.ROUND_HALF_UP)
    except (decimal.InvalidOperation, TypeError):
        messages.error(request, "Monto invalido.")
        return redirect("payments:crear")

    if amount < MIN_AMOUNT:
        messages.error(request, f"El monto minimo es ${int(MIN_AMOUNT)}.")
        return redirect("payments:crear")

    name = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    message = (request.POST.get("message") or "").strip()

    buy_order = f"MR-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    session_id = uuid.uuid4().hex[:12]
    cliente = getattr(request.user, "cliente", None)

    donation = Donation.objects.create(
        cliente=cliente,
        amount=amount,
        name=name,
        email=email,
        message=message,
        buy_order=buy_order,
        session_id=session_id,
    )

    try:
        transaction = Transaction(_tbk_options())
        response = transaction.create(buy_order, session_id, int(amount), settings.TBK_RETURN_URL)
    except Exception:  # pragma: no cover - dependiente de SDK externo
        logger.exception("Error iniciando transaccion Webpay.")
        donation.status = "failed"
        donation.save(update_fields=["status"])
        messages.error(request, "No pudimos iniciar el pago. Intenta mas tarde.")
        return redirect("payments:crear")

    token = response.get("token")
    url = response.get("url")
    if not token or not url:
        logger.error("Respuesta inesperada de Webpay: %s", response)
        donation.status = "failed"
        donation.response_raw = response
        donation.save(update_fields=["status", "response_raw"])
        messages.error(request, "No pudimos iniciar el pago. Intenta mas tarde.")
        return redirect("payments:crear")

    donation.token_ws = token
    donation.response_raw = response
    donation.save(update_fields=["token_ws", "response_raw"])

    return redirect(f"{url}?token_ws={token}")


def webpay_return(request):
    """Procesa el retorno desde Webpay (exitoso o abortado)."""
    token = request.POST.get("token_ws") or request.GET.get("token_ws")
    tbk_token = request.POST.get("TBK_TOKEN")
    tbk_order = request.POST.get("TBK_ORDEN_COMPRA")
    tbk_session = request.POST.get("TBK_ID_SESION")

    if tbk_token or tbk_order or tbk_session:
        if tbk_order:
            Donation.objects.filter(buy_order=tbk_order).update(status="aborted")
        return render(request, "donations/result.html", {"ok": False, "aborted": True})

    if not token:
        return HttpResponseBadRequest("Token faltante")

    donation = Donation.objects.filter(token_ws=token).first()
    if not donation:
        logger.warning("Retorno Webpay sin donacion vinculada. token=%s", token)
        return HttpResponseBadRequest("Transaccion desconocida")

    try:
        transaction = Transaction(_tbk_options())
        result = transaction.commit(token)
    except Exception:  # pragma: no cover - dependiente de SDK externo
        logger.exception("Error confirmando transaccion Webpay.")
        donation.status = "failed"
        donation.save(update_fields=["status"])
        return render(request, "donations/result.html", {"ok": False, "error": "commit_failed"})

    status_raw = (result.get("status") or "").upper()
    ok = status_raw == "AUTHORIZED"

    donation.status = "authorized" if ok else (status_raw or "failed").lower()
    donation.authorization_code = result.get("authorization_code") or ""
    donation.payment_type = result.get("payment_type_code") or ""
    donation.installments_number = result.get("installments_number")
    donation.response_raw = result
    donation.save(
        update_fields=[
            "status",
            "authorization_code",
            "payment_type",
            "installments_number",
            "response_raw",
        ]
    )

    return render(
        request,
        "donations/result.html",
        {"ok": ok, "result": result, "donation": donation},
    )


def webpay_status(request):
    """Consulta asincrona del estado de una transaccion en Webpay."""
    token = request.GET.get("token")
    if not token:
        return HttpResponseBadRequest("Falta token")

    try:
        transaction = Transaction(_tbk_options())
        data = transaction.status(token)
    except Exception as exc:  # pragma: no cover - dependiente de SDK externo
        logger.exception("Error consultando estado Webpay.")
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(data)


@login_required(login_url="login")
def donation_history(request):
    """Listado de donaciones del usuario autenticado."""
    cliente = getattr(request.user, "cliente", None)
    qs = Donation.objects.none()
    if cliente:
        qs = Donation.objects.filter(cliente=cliente).order_by("-created_at")
    return render(request, "donations/history.html", {"donations": qs})
