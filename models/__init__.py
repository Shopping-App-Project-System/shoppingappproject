"""資料存取層（Data Access Layer）。

原本是單一 989 行的 models.py，依領域拆分成多個模組以便維護。
此處 re-export 全部函式，因此既有的 `from models import xxx` 完全不需修改。

模組分工：
    user.py      使用者帳號與登入狀態（7 個函式）
    product.py   商品查詢、上架與庫存（17 個函式）
    cart.py      購物車（7 個函式）
    order.py     訂單與金流狀態（13 個函式）
    delivery.py  Minecraft 待發道具佇列（3 個函式）
    manage_log.py 後台操作日誌（4 個函式）
    analytics.py 後台報表與統計（9 個函式）
"""

from db import db_transaction

from .user import (
    createUser,
    updateUser,
    getUser,
    getUserList,
    updateSessionToken,
    clearSessionToken,
    get_user_minecraft_name,
)

from .product import (
    index,
    search_categories,
    get_product_by_id,
    get_product_stock,
    get_product_pics,
    get_product,
    deduct_product_stock,
    restore_product_stock,
    hard_delete_product,
    add_product,
    add_product_stock,
    set_product_stock,
    set_product_active,
    update_product,
    get_all_products,
    soft_delete_product,
    restore_product,
)

from .cart import (
    get_cart_items,
    find_cart_item,
    update_cart_qty,
    upsert_cart,
    remove_cart_item,
    clear_cart,
    get_cart_item_stock,
)

from .order import (
    insert_order,
    get_order_by_ecpay_trade_no,
    update_order_payment_status,
    get_order_status,
    get_user_order_seq,
    insert_order_item,
    get_order_items,
    get_order_items_detail,
    get_all_orders,
    get_orders,
    search_orders,
    get_order,
    cancel_order,
)

from .delivery import (
    add_pending_delivery,
    get_all_pending_deliveries,
    delete_pending_delivery,
)

from .manage_log import (
    add_log,
    get_logs,
    get_log_months,
    get_logs_by_month,
)

from .analytics import (
    get_user_accounts_with_orders,
    search_completed_orders,
    get_order_items_with_user_check,
    get_dashboard_summary,
    get_revenue_trend,
    get_orders_count_by_month,
    get_available_order_years,
    get_top_products,
    get_member_spending_distribution,
)

__all__ = [
    "db_transaction",
    "createUser",
    "updateUser",
    "getUser",
    "getUserList",
    "updateSessionToken",
    "clearSessionToken",
    "get_user_minecraft_name",
    "index",
    "search_categories",
    "get_product_by_id",
    "get_product_stock",
    "get_product_pics",
    "get_product",
    "deduct_product_stock",
    "restore_product_stock",
    "hard_delete_product",
    "add_product",
    "add_product_stock",
    "set_product_stock",
    "set_product_active",
    "update_product",
    "get_all_products",
    "soft_delete_product",
    "restore_product",
    "get_cart_items",
    "find_cart_item",
    "update_cart_qty",
    "upsert_cart",
    "remove_cart_item",
    "clear_cart",
    "get_cart_item_stock",
    "insert_order",
    "get_order_by_ecpay_trade_no",
    "update_order_payment_status",
    "get_order_status",
    "get_user_order_seq",
    "insert_order_item",
    "get_order_items",
    "get_order_items_detail",
    "get_all_orders",
    "get_orders",
    "search_orders",
    "get_order",
    "cancel_order",
    "add_pending_delivery",
    "get_all_pending_deliveries",
    "delete_pending_delivery",
    "add_log",
    "get_logs",
    "get_log_months",
    "get_logs_by_month",
    "get_user_accounts_with_orders",
    "search_completed_orders",
    "get_order_items_with_user_check",
    "get_dashboard_summary",
    "get_revenue_trend",
    "get_orders_count_by_month",
    "get_available_order_years",
    "get_top_products",
    "get_member_spending_distribution",
]
