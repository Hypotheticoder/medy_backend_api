from .customer import (
    get_customer, get_customer_by_phone, get_customers,
    create_customer, update_customer, delete_customer
)
from .pharma_shop import (
    get_pharma_shop, get_pharma_shops,
    create_pharma_shop, update_pharma_shop, delete_pharma_shop
)
from .lab import (
    get_lab, get_labs,
    create_lab, update_lab, delete_lab
)
from .medicine import (
    get_medicine, get_medicines,
    create_medicine, update_medicine, delete_medicine, create_medicines_bulk
)
from .order import (
    get_order, get_orders,
    create_order, update_order, delete_order
)
