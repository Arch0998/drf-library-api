from rest_framework import mixins, viewsets
from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for Payment:
    - list: GET /payments/
    - create: POST /payments/
    - retrieve: GET /payments/{id}/
    """

    queryset = Payment.objects.all().order_by("-id")
    serializer_class = PaymentSerializer
