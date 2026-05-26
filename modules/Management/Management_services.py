# __________________________________________內部模組_____________________________________
from flask import request,redirect,render_template,session,url_for,flash

# _______________________________________自定義模組_______________________________________
from models import (
    getUser,updateUser,
    add_product,add_log,get_product_by_id,
    get_all_products,set_product_active,
    search_orders,get_orders,update_product,
    add_product_stock,set_product_stock,
    get_log_months,get_logs_by_month,
    get_user_accounts_with_orders,
    search_completed_orders,
    get_order_items_with_user_check,
    # 後台儀表板 (圖表) 用的統計查詢
    get_dashboard_summary,get_revenue_trend,get_orders_count_by_month,
    get_top_products,get_member_spending_distribution,
    get_available_order_years,
    # 永久刪除功能已停用,連同 hard_delete_product 一起不再 import
    # hard_delete_product
)
from settings import SESSION_AUTHO,PRODUCT_FOLDER,PROFILE_FOLDER,MC_PRODUCT_ITEMS,PRODUCT_DEFAULT_PATH
from utils import get_auth,requestParsor
from cloudinary_helper import save_image
# _______________________________________初始化___________________________________________

# _______________________________________services___________________________________________

# mc_item_id 設為選填，預設 None
# 寶石類商品填入（例如 minecraft:diamond），序號類商品不填
@requestParsor
def manage_add_service(name, original_price, sale_price, description, image, product_quantity, mc_item_name, category=None):
    sale_price   = sale_price or None
    img_filename = save_image(image, PRODUCT_FOLDER, filename=name)
    if not img_filename:
        img_filename = PRODUCT_DEFAULT_PATH
    # category 和 mc_item_name 都必填
    if not category or not mc_item_name:
        flash("請選擇商品類別與MC道具", "error")
        return redirect(url_for("D.manage"))

    mc_item_id = MC_PRODUCT_ITEMS.get(category, {}).get(mc_item_name)
    if not mc_item_id:
        flash("MC道具輸入錯誤，請查閱相關文件後重新嘗試上架", "error")
        return redirect(url_for("D.manage"))

    product_id = add_product(name, original_price, sale_price, description, img_filename, mc_item_id, category)
    add_product_stock(product_id, int(product_quantity))
    add_log(session.get(SESSION_AUTHO), "上架", product_id, name)
    flash("商品已上架", "success")
    return redirect(url_for("D.manage") + "#products")

# 永久刪除功能已停用 ── 整個 function 註解保留以備將來恢復.
# 理由:
#   1. 有訂單紀錄的商品因為 order_items.product_id 外鍵約束,hard delete 會失敗
#   2. 沒訂單的商品用「下架」(soft delete) 已足夠應付實務需求
#   3. 連同 manage.html 的「✕ 刪除」按鈕、Management_routers.py 的 /manage/clear
#      路由都已停用,但程式碼保留以備將來恢復或改成軟刪除.
#
# @requestParsor
# def manage_clear_service(product_id):
#     if request.method == "GET":         # 防止誤觸或直接輸入網址,導回管理頁
#         return redirect(url_for("D.manage"))
#
#     product    = get_product_by_id(product_id)
#     hard_delete_product(product_id)
#     add_log(session.get(SESSION_AUTHO), "刪除", product_id, product["name"])
#     flash("商品已刪除", "success")
#     return redirect(url_for("D.manage"))

@requestParsor
def manage_service(mc_item_class, mc_item_name, mc_item_id):
    products = get_all_products()
    return render_template("manage.html", products=products, mc_items=MC_PRODUCT_ITEMS)

@requestParsor
def manage_remove_service(product_id):
    if request.method == "GET":         # 防止誤觸或直接輸入網址，導回管理頁
        return redirect(url_for("D.manage"))

    product    = get_product_by_id(product_id)
    set_product_active(product_id, 0)
    add_log(session.get(SESSION_AUTHO), "下架", product_id, product["name"])
    flash("商品已下架", "success")
    return redirect(url_for("D.manage"))

@requestParsor
def manage_restock_service(product_id):
    if request.method == "GET":         # 防止誤觸或直接輸入網址，導回管理頁
        return redirect(url_for("D.manage"))

    product    = get_product_by_id(product_id)
    set_product_active(product_id, 1)
    add_log(session.get(SESSION_AUTHO), "重新上架", product_id, product["name"])
    flash("商品已重新上架", "success")
    return redirect(url_for("D.manage"))

@requestParsor
def manage_edit_service(product_id, name, original_price, sale_price=None, category=None, product_quantity=None, image=None):
    if request.method == "GET":         # 防止誤觸或直接輸入網址，導回管理頁
        return redirect(url_for("D.manage"))

    sale_price = sale_price or None
    category   = category or None

    product = get_product_by_id(product_id)
    if not product:
        flash("找不到該商品", "error")
        return redirect(url_for("D.manage"))

    update_data = {
        "name": name,
        "original_price": original_price,
        "sale_price": sale_price,
        "category": category,
    }

    if image and image.filename != "":
        new_pic_path = save_image(image, PRODUCT_FOLDER, filename=name)
        update_data["product_pic"] = new_pic_path


    update_product(update_data, product_id)

    # 更新庫存(只有有送 product_quantity 才動,空值則保留原庫存)
    if product_quantity is not None and product_quantity.strip() != "":
        try:
            qty = int(product_quantity)
            if qty < 0:
                qty = 0
            set_product_stock(product_id, qty)
        except ValueError:
            flash("商品數量格式錯誤,庫存未更新", "error")

    add_log(session.get(SESSION_AUTHO), "修改", product_id, name)
    flash("商品資料已更新", "success")
    return redirect(url_for("D.manage"))

@requestParsor
def member_edit_service(profile_pic=None):
    user_account = session.get(SESSION_AUTHO)

    if request.method == "GET":
        user = getUser(
            {"user_account": user_account},
            "user_account", "user_email"
        )
        return render_template("member_edit.html",
            user=user,
            auth=get_auth(user_account)
        )

    if profile_pic and profile_pic.filename != "":
        new_pic_path = save_image(profile_pic, PROFILE_FOLDER, filename=user_account)
        updateUser({"pic_path": new_pic_path}, {"user_account": user_account})

    flash("資料更新成功", "success")
    return redirect(url_for("D.member"))

@requestParsor
def member_service(keyword=""):
    user_account = session[SESSION_AUTHO]
    keyword = keyword.strip()

    if keyword:
        orders = search_orders(user_account, keyword)
    else:
        orders = get_orders(user_account)

    user = getUser(
        {"user_account": user_account},
        "user_account", "user_email"
    )
    user.update({"level": "一般會員"})

    return render_template("member.html",
        orders=orders,
        user=user,
        auth=get_auth(user_account)
    )

def manage_logout_service():
    session.pop(SESSION_AUTHO,None)
    flash("已登出")
    return redirect(url_for("B.index"))

@requestParsor
def manage_log_service(month="", product=""):
    # 後台操作日誌:
    # - URL 帶 ?month=YYYY-MM      → 預先載入該月份(展開)
    # - URL 再加 ?product=關鍵字   → 該月只顯示商品名含關鍵字的紀錄
    selected_month   = month.strip()
    product_keyword  = product.strip()
    months = get_log_months()

    preloaded_logs = None
    product_options = []

    if selected_month and len(selected_month) == 7 and selected_month[4] == '-' \
            and selected_month[:4].isdigit() and selected_month[5:].isdigit():
        all_logs = get_logs_by_month(selected_month)

        # 該月出現過的所有商品名稱(去重、排序),供下拉選單用
        product_options = sorted({
            log["product_name"] for log in all_logs
            if log.get("product_name")
        })

        # 套用關鍵字篩選(大小寫不敏感、模糊比對)
        if product_keyword:
            kw = product_keyword.lower()
            preloaded_logs = [
                log for log in all_logs
                if log.get("product_name") and kw in log["product_name"].lower()
            ]
        else:
            preloaded_logs = all_logs
    else:
        selected_month = ""  # 格式不對就清掉,當作沒查詢

    return render_template("manage_log.html",
        months=months,
        selected_month=selected_month,
        product_keyword=product_keyword,
        product_options=product_options,
        preloaded_logs=preloaded_logs
    )


def manage_log_month_service(month):
    """AJAX partial:取得指定月份的所有後台操作紀錄。"""
    # 簡單格式檢查 YYYY-MM,避免亂塞參數
    if not month or len(month) != 7 or month[4] != '-' \
            or not month[:4].isdigit() or not month[5:].isdigit():
        return render_template("_manage_log_month.html", month=month, logs=[])

    logs = get_logs_by_month(month)
    return render_template("_manage_log_month.html", month=month, logs=logs)


# ── 信用卡管理 services ────────────────────────────────────────────────────
# ⚠️ 注意：本功能直接儲存完整卡號，僅適用於學校作業/示意用途。

# ── 已完成訂單查詢 services(管理員/使用者共用模板) ────────────────────────────

def _parse_filters_from_request():
    """從 request.args 解析篩選條件,回傳一個 dict。"""
    month       = request.args.get("month", "").strip()
    target_user = request.args.get("target_user", "").strip()
    min_total   = request.args.get("min_total", "").strip()
    max_total   = request.args.get("max_total", "").strip()

    # 月份格式驗證
    if not (len(month) == 7 and month[4] == '-'
            and month[:4].isdigit() and month[5:].isdigit()):
        month = ""

    # 金額轉數字
    try:
        min_total_val = int(min_total) if min_total else None
    except ValueError:
        min_total_val = None
    try:
        max_total_val = int(max_total) if max_total else None
    except ValueError:
        max_total_val = None

    return {
        "month": month,
        "target_user": target_user,
        "min_total": min_total_val,
        "max_total": max_total_val,
        # 給模板顯示原始字串(避免顯示 None)
        "min_total_raw": min_total,
        "max_total_raw": max_total,
    }


def manage_completed_orders_service():
    """管理員:看所有人的已完成訂單。"""
    filters = _parse_filters_from_request()
    orders = search_completed_orders(
        user_account=None,
        target_user=filters["target_user"] or None,
        month=filters["month"] or None,
        min_total=filters["min_total"],
        max_total=filters["max_total"],
    )
    user_options = get_user_accounts_with_orders()

    return render_template("orders.html",
        orders=orders,
        filters=filters,
        user_options=user_options,
        is_admin=True,
        items_url_base="/manage/orders",  # 配合下面的 partial route
        page_title="交易成功訂單(全部使用者)"
    )



def member_completed_orders_service():
    """使用者:看自己的已完成訂單。"""
    user_account = session[SESSION_AUTHO]
    filters = _parse_filters_from_request()
    orders = search_completed_orders(
        user_account=user_account,
        target_user=None,
        month=filters["month"] or None,
        min_total=filters["min_total"],
        max_total=filters["max_total"],
    )

    return render_template("orders.html",
        orders=orders,
        filters=filters,
        user_options=[],
        is_admin=False,
        items_url_base="/member/orders",
        page_title="我的交易成功訂單"
    )


def manage_order_items_service(order_id):
    """
    管理員:取單張訂單明細(AJAX partial)。

    【為什麼這裡不用 @requestParsor】
    order_id 是從 URL 路徑 /manage/orders/<int:order_id>/items 取得的位置參數,
    Flask 會直接以位置參數傳進來。若再套用 @requestParsor,它會嘗試從
    request.args / request.form 再解析一次同名參數,造成
    「got multiple values for argument 'order_id'」TypeError。
    本 service 不需要從 request 額外取參數,因此不套裝飾器。
    """
    items = get_order_items_with_user_check(order_id, user_account=None)
    if items is None:
        return render_template("_order_items.html", items=[], not_found=True)
    return render_template("_order_items.html", items=items, not_found=False)


def member_order_items_service(order_id):
    """
    使用者:取自己的訂單明細(AJAX partial)。

    【為什麼這裡不用 @requestParsor】
    order_id 是從 URL 路徑 /member/orders/<int:order_id>/items 取得的位置參數,
    Flask 會直接以位置參數傳進來。若再套用 @requestParsor,它會嘗試從
    request.args / request.form 再解析一次同名參數,造成
    「got multiple values for argument 'order_id'」TypeError。
    本 service 不需要從 request 額外取參數,因此不套裝飾器。
    """
    user_account = session[SESSION_AUTHO]
    items = get_order_items_with_user_check(order_id, user_account=user_account)
    if items is None:
        return render_template("_order_items.html", items=[], not_found=True)
    return render_template("_order_items.html", items=items, not_found=False)


# ══════════════════════════════════════════════════════════════════════════════
#   後台儀表板 (銷售統計圖表)
# ══════════════════════════════════════════════════════════════════════════════
def manage_dashboard_service():
    """
    回傳儀表板 partial HTML (不含 topbar/footer)。

    呼叫情境:
      manage.html 點擊「📈 數據圖表」分頁 → AJAX GET /manage/dashboard
        → 此 service 回傳一段 HTML 片段 → 前端塞進 #panel-container

    為什麼不再渲染完整頁:
      原本此 service 渲染整個 manage_dashboard.html (含 topbar/footer)。
      改成「嵌入式分頁」之後,整個外框 (header/nav/footer) 都由 manage.html
      提供,儀表板只需要內容區。因此改為回傳 _dashboard_panel.html partial。

    圖表資料仍由前端另外打 /manage/dashboard/data 取 JSON,此邏輯不變。
    """
    return render_template("_dashboard_panel.html")


def manage_dashboard_data_service():
    """
    儀表板資料 API,回傳 JSON 給前端 Chart.js 使用。

    支援 query string:
      ?year=2026    → 訂單數量圖只顯示 2026 年資料
      ?year=all     → 訂單數量圖彙總所有年份
      (省略)        → 預設為「最新有資料的年份」

    回傳結構:
      {
        "summary":         { ... },
        "revenue_trend":   [ ... ],
        "orders_by_month": [ ... ],   # 受 year 影響
        "top_products":    [ ... ],
        "member_dist":     [ ... ],
        "available_years": [2026, 2025, ...],  # 有資料的年份清單,給下拉選單用
        "selected_year":   2026 or None,        # 目前查詢的年份 (None 代表「全部」)
      }
    """
    from flask import jsonify, request

    # 處理 year 參數
    year_param = request.args.get("year", "").strip()
    available_years = get_available_order_years()
    if year_param == "all":
        # 使用者明確選「全部年份」
        selected_year = None
    elif year_param.isdigit():
        # 使用者選了某一年
        selected_year = int(year_param)
    else:
        # 沒指定:預設選最新有資料的年份
        selected_year = available_years[0] if available_years else None

    return jsonify({
        "summary":         get_dashboard_summary(),
        "revenue_trend":   get_revenue_trend(months=12),
        "orders_by_month": get_orders_count_by_month(year=selected_year),
        "top_products":    get_top_products(limit=10),
        "member_dist":     get_member_spending_distribution(limit=8),
        "available_years": available_years,
        "selected_year":   selected_year,
    })
