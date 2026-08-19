"""後台報表與統計。

本模組只負責資料存取（SQL），不含商業邏輯。
商業邏輯請放在 modules/<領域>/*_services.py。
"""

from db import db_transaction
from settings import (
    BRANCH_A_TABLE,
    BRANCH_B_PRODUCTS_TABLE,
    BRANCH_C_ORDER_TABLE,
    BRANCH_C_ORDER_ITEMS_TABLE,
)


@db_transaction
def get_user_accounts_with_orders(cursor):
    """取得有過訂單(含已完成的)的所有使用者帳號清單,給管理員下拉用。"""
    cursor.execute(f"""
        SELECT DISTINCT u.user_account
        FROM `{BRANCH_A_TABLE}` u
        JOIN `{BRANCH_C_ORDER_TABLE}` o ON o.user_id = u.id
        WHERE o.status = '已完成'
        ORDER BY u.user_account
    """)
    return [row['user_account'] for row in cursor.fetchall()]


@db_transaction
def search_completed_orders(cursor, user_account=None, target_user=None,
                            month=None, min_total=None, max_total=None):
    """
    篩選「已完成」訂單。
    user_account:None=管理員模式撈全部;傳帳號=只撈該人(使用者模式)
    target_user :管理員可指定要看哪個使用者(None=全部使用者)
    month       :YYYY-MM 格式
    min_total/max_total:金額範圍
    """
    sql = f"""
        SELECT o.id, o.total, o.payment_method,
               o.note, o.status, o.created_at,
               u.user_account
        FROM `{BRANCH_C_ORDER_TABLE}` o
        JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
        WHERE o.status = '已完成'
    """
    params = []

    if user_account is not None:
        # 使用者模式:強制只看自己
        sql += " AND u.user_account = %s"
        params.append(user_account)
    elif target_user:
        # 管理員指定看某人
        sql += " AND u.user_account = %s"
        params.append(target_user)

    if month:
        sql += " AND DATE_FORMAT(o.created_at, '%%Y-%%m') = %s"
        params.append(month)

    if min_total is not None:
        sql += " AND o.total >= %s"
        params.append(min_total)

    if max_total is not None:
        sql += " AND o.total <= %s"
        params.append(max_total)

    sql += " ORDER BY o.created_at ASC"
    cursor.execute(sql, tuple(params))
    return cursor.fetchall()


@db_transaction
def get_order_items_with_user_check(cursor, order_id, user_account=None):
    """
    取得訂單明細(含商品名稱/圖片)。
    user_account=None : 管理員模式,不檢查擁有者
    user_account=帳號 : 使用者模式,訂單必須屬於該人,否則回 None
    """
    if user_account is not None:
        # 先驗證訂單屬於這個人
        cursor.execute(f"""
            SELECT 1 FROM `{BRANCH_C_ORDER_TABLE}` o
            JOIN `{BRANCH_A_TABLE}` u ON u.id = o.user_id
            WHERE o.id = %s AND u.user_account = %s AND o.status = '已完成'
        """, (order_id, user_account))
        if not cursor.fetchone():
            return None  # 不是你的訂單 / 訂單不存在 / 不是已完成
    else:
        # 管理員只要驗證訂單存在且已完成
        cursor.execute(f"""
            SELECT 1 FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE id = %s AND status = '已完成'
        """, (order_id,))
        if not cursor.fetchone():
            return None

    cursor.execute(f"""
        SELECT oi.quantity, oi.price,
               p.name AS product_name, p.product_pic
        FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` oi
        JOIN `{BRANCH_B_PRODUCTS_TABLE}` p ON p.id = oi.product_id
        WHERE oi.order_id = %s
    """, (order_id,))
    return cursor.fetchall()


@db_transaction
def get_dashboard_summary(cursor):
    """
    儀表板上方四張摘要卡片所需的彙總數字。

    回傳一個 dict,包含:
      - total_revenue   : 總營收 (已完成訂單 total 加總)
      - total_orders    : 總訂單數 (已完成)
      - avg_order_value : 平均客單價 (total_revenue / total_orders,無單則為 0)
      - total_members   : 至少下過一筆已完成訂單的不同會員數
    """
    cursor.execute(f"""
        SELECT
            COALESCE(SUM(total), 0) AS total_revenue,
            COUNT(*)                AS total_orders,
            COUNT(DISTINCT user_id) AS total_members
        FROM `{BRANCH_C_ORDER_TABLE}`
        WHERE status = '已完成'
    """)
    row = cursor.fetchone()
    total_revenue   = float(row["total_revenue"]) if row else 0.0
    total_orders    = int(row["total_orders"]) if row else 0
    total_members   = int(row["total_members"]) if row else 0
    avg_order_value = (total_revenue / total_orders) if total_orders else 0.0
    return {
        "total_revenue":   total_revenue,
        "total_orders":    total_orders,
        "avg_order_value": avg_order_value,
        "total_members":   total_members,
    }


@db_transaction
def get_revenue_trend(cursor, months=12):
    """
    取近 N 個月的營收趨勢 (預設 12 個月)。

    回傳 list of dict,每筆: { 'month': 'YYYY-MM', 'revenue': 金額 }
    依月份升冪排序,供折線圖時間軸使用。
    """
    cursor.execute(f"""
        SELECT
            DATE_FORMAT(created_at, '%%Y-%%m') AS month,
            COALESCE(SUM(total), 0)           AS revenue
        FROM `{BRANCH_C_ORDER_TABLE}`
        WHERE status = '已完成'
          AND created_at >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
        GROUP BY month
        ORDER BY month ASC
    """ % int(months))
    return [
        {"month": r["month"], "revenue": float(r["revenue"])}
        for r in cursor.fetchall()
    ]


@db_transaction
def get_orders_count_by_month(cursor, year=None):
    """
    依「月份」彙總訂單數量,固定回傳 1~12 月共 12 筆 (沒資料的月份補 0)。

    :param year: 指定年份 (例如 2026)。若為 None 則彙總所有年份。

    回傳格式:
        [
          {'month': '1月', 'month_num': 1, 'order_count': N},
          {'month': '2月', 'month_num': 2, 'order_count': N},
          ...
          {'month': '12月', 'month_num': 12, 'order_count': N},
        ]

    【設計理由】
    X 軸永遠固定為 1月~12月 (使用者偏好,不看時間軸跨年),
    透過 year 參數讓使用者切換要看哪一年的全年資料,
    或選「全部」彙總所有年份的同月份。
    """
    if year is None:
        # 不限年份:所有年份同月份加總
        cursor.execute(f"""
            SELECT
                MONTH(created_at) AS month_num,
                COUNT(*)          AS order_count
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE status = '已完成'
            GROUP BY month_num
        """)
    else:
        # 指定年份:只取該年的資料
        cursor.execute(f"""
            SELECT
                MONTH(created_at) AS month_num,
                COUNT(*)          AS order_count
            FROM `{BRANCH_C_ORDER_TABLE}`
            WHERE status = '已完成'
              AND YEAR(created_at) = %s
            GROUP BY month_num
        """ % int(year))
    # 把 SQL 結果轉成 {月份數字 -> 訂單數} 的字典,方便補齊缺月份
    counts_by_month = {
        int(r["month_num"]): int(r["order_count"])
        for r in cursor.fetchall()
    }
    # 固定回傳 1-12 月共 12 筆,沒資料的月份補 0
    return [
        {
            "month":       f"{m}月",
            "month_num":   m,
            "order_count": counts_by_month.get(m, 0),
        }
        for m in range(1, 13)
    ]


@db_transaction
def get_available_order_years(cursor):
    """
    查詢「有訂單資料」的年份清單 (供前端下拉選單使用)。

    回傳 list of int,依年份由新到舊排序。
    例如:[2026, 2025, 2024]

    若資料表沒有任何已完成訂單,回傳空 list。
    """
    cursor.execute(f"""
        SELECT DISTINCT YEAR(created_at) AS year
        FROM `{BRANCH_C_ORDER_TABLE}`
        WHERE status = '已完成'
        ORDER BY year DESC
    """)
    return [int(r["year"]) for r in cursor.fetchall()]


@db_transaction
def get_top_products(cursor, limit=10):
    """
    熱門商品排行 (依累計銷售數量排序)。

    回傳 list of dict,每筆: { 'product_name': 商品名, 'total_qty': 累計賣出數量 }
    供橫條圖使用。
    """
    cursor.execute(f"""
        SELECT
            p.name              AS product_name,
            SUM(oi.quantity)    AS total_qty
        FROM `{BRANCH_C_ORDER_ITEMS_TABLE}` oi
        JOIN `{BRANCH_C_ORDER_TABLE}`   o ON o.id = oi.order_id
        JOIN `{BRANCH_B_PRODUCTS_TABLE}` p ON p.id = oi.product_id
        WHERE o.status = '已完成'
        GROUP BY p.id, p.name
        ORDER BY total_qty DESC
        LIMIT %s
    """ % int(limit))
    return [
        {"product_name": r["product_name"], "total_qty": int(r["total_qty"])}
        for r in cursor.fetchall()
    ]


@db_transaction
def get_member_spending_distribution(cursor, limit=10):
    """
    會員消費分布 (依累計消費金額排序,前 N 名 + 其他)。

    回傳 list of dict,每筆: { 'user_account': 帳號, 'total_spent': 累計消費 }
    最後一筆 user_account = '其他' 代表名次外所有會員的消費加總。
    供圓餅圖使用。
    """
    # 先取前 N 名
    cursor.execute(f"""
        SELECT
            u.user_account            AS user_account,
            COALESCE(SUM(o.total), 0) AS total_spent
        FROM `{BRANCH_C_ORDER_TABLE}` o
        JOIN `{BRANCH_A_TABLE}`       u ON u.id = o.user_id
        WHERE o.status = '已完成'
        GROUP BY u.id, u.user_account
        ORDER BY total_spent DESC
        LIMIT %s
    """ % int(limit))
    top_rows = cursor.fetchall()
    result = [
        {"user_account": r["user_account"], "total_spent": float(r["total_spent"])}
        for r in top_rows
    ]
    # 再取「其他會員」的消費總和 (排除前 N 名)
    top_accounts = [r["user_account"] for r in result]
    if top_accounts:
        placeholders = ",".join(["%s"] * len(top_accounts))
        cursor.execute(f"""
            SELECT COALESCE(SUM(o.total), 0) AS other_total
            FROM `{BRANCH_C_ORDER_TABLE}` o
            JOIN `{BRANCH_A_TABLE}`       u ON u.id = o.user_id
            WHERE o.status = '已完成'
              AND u.user_account NOT IN ({placeholders})
        """, tuple(top_accounts))
        other_row = cursor.fetchone()
        other_total = float(other_row["other_total"]) if other_row else 0.0
        if other_total > 0:
            result.append({"user_account": "其他", "total_spent": other_total})
    return result
