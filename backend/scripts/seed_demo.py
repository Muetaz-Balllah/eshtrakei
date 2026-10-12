"""Fill the local database with demo companies, people, and activity.

Safe to run more than once: if the demo client already exists, it leaves the database unchanged.
Existing accounts outside @demo.eshtrakei.local are kept.
"""

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select

from backend._core.security import hash_password
from backend.advertisements.models import Advertisement
from backend.auth.models import User
from backend.banners.models import PlatformBanner
from backend.banners.services import approve_banner, reject_banner
from backend.companies.models import Company, CompanyJoinRequest
from backend.companies.services import create_manager, stop_company
from backend.complaints.schemas import ComplaintCreate, ReplyBody
from backend.complaints.services import create_complaint, create_support, reply
from backend.config import get_settings
from backend.coupons.models import Coupon
from backend.coupons.schemas import CouponCreate
from backend.coupons.services import create_coupon
from backend.coverage.schemas import TowerBody
from backend.coverage.services import add_tower
from backend.db import SessionLocal
from backend.enums import CompanyStatus, DurationUnit, JoinRequestStatus, PaymentStatus, SubscriptionStatus, UserRole
from backend.errors import AppError
from backend.finance.services import credit_company
from backend.invoices.models import Invoice
from backend.notifications.services import push_role, run_expiry_check
from backend.packages.models import Package
from backend.packages.schemas import PackageBody
from backend.packages.services import create_package, stop_package
from backend.payments.models import Payment
from backend.scripts.seed_admin import seed_admin
from backend.settings.services import banner_price, ensure_defaults
from backend.subscriptions.models import Subscription
from backend.subscriptions.schemas import PurchaseBody, RenewBody
from backend.subscriptions.services import purchase, renew
from backend.utils import libya_today, utc_now
from backend.wallets.services import top_up

PASSWORD = "Demo1234"
MARKER = "ahmad@demo.eshtrakei.local"


def _user(db, email: str) -> User:
    row = db.scalar(select(User).where(User.email == email))
    if row is None:
        raise SystemExit(f"missing user {email}")
    return row


def _package(db, company_id: int, name: str) -> Package:
    row = db.scalar(select(Package).where(Package.company_id == company_id, Package.name == name))
    if row is None:
        raise SystemExit(f"missing package {name}")
    return row


def _company(name: str, description: str, phone: str, target: str) -> Company:
    now = utc_now()
    return Company(
        name=name,
        description=description,
        phone=phone,
        status=CompanyStatus.approved,
        created_at=now,
        updated_at=now,
        monthly_sales_target=Decimal(target),
        balance=Decimal("0.00"),
    )


def _shift(db, subscription_id: int, *, start_days_ago: int, end_in_days: int) -> None:
    today = libya_today()
    start = today - timedelta(days=start_days_ago)
    end = today + timedelta(days=end_in_days)
    paid_at = utc_now() - timedelta(days=start_days_ago)
    subscription = db.get(Subscription, subscription_id)
    if subscription is None:
        raise SystemExit(f"missing subscription {subscription_id}")
    subscription.start_date = start
    subscription.end_date = end
    subscription.status = SubscriptionStatus.expired if end < today else SubscriptionStatus.active
    subscription.created_at = paid_at
    payment = db.scalar(select(Payment).where(Payment.subscription_id == subscription_id))
    if payment is not None:
        payment.created_at = paid_at
    invoice = db.scalar(select(Invoice).where(Invoice.subscription_id == subscription_id))
    if invoice is not None:
        invoice.issued_at = paid_at
    db.commit()


def _buy(db, client_id: int, company_id: int, package_id: int, key: str, *, coupon: str | None = None, wallet: bool = False):
    result = purchase(
        db,
        client_id,
        PurchaseBody(
            company_id=company_id,
            package_id=package_id,
            coupon_code=coupon,
            idempotency_key=key,
            simulated_outcome=None if wallet else "success",
            pay_with_wallet=wallet,
        ),
    )
    if result.payment_status != "succeeded" or result.subscription is None:
        raise SystemExit(f"purchase {key} failed: {result.message}")
    return result.subscription.id


def _closed_sale(db, client: User, company: Company, package: Package, *, days_ago: int, duration_days: int) -> None:
    today = libya_today()
    start = today - timedelta(days=days_ago)
    end = start + timedelta(days=duration_days)
    if end >= today:
        raise SystemExit("closed sale must end before today")
    paid_at = utc_now() - timedelta(days=days_ago)
    subscription = Subscription(
        client_id=client.id,
        company_id=company.id,
        package_id=package.id,
        start_date=start,
        end_date=end,
        status=SubscriptionStatus.expired,
        package_name_snapshot=package.name,
        price_snapshot=package.price,
        duration_snapshot=f"{package.duration_amount} days",
        data_allowance_snapshot=f"{package.data_gb} GB",
        speed_snapshot=f"{package.speed_mbps}/{package.upload_mbps or package.speed_mbps} Mbps",
        created_at=paid_at,
    )
    db.add(subscription)
    db.flush()
    db.add(
        Payment(
            client_id=client.id,
            company_id=company.id,
            package_id=package.id,
            subscription_id=subscription.id,
            amount=package.price,
            currency=get_settings().payment_currency,
            provider="mock",
            status=PaymentStatus.succeeded,
            provider_reference=f"demo_hist_{subscription.id}",
            idempotency_key=f"demo-hist-{company.id}-{client.id}-{days_ago}",
            created_at=paid_at,
        )
    )
    db.commit()


def seed_demo() -> None:
    seed_admin()
    db = SessionLocal()
    try:
        if db.scalar(select(User.id).where(User.email == MARKER)) is not None:
            print("Demo data already exists. Nothing was changed.")
            return
        ensure_defaults(db)
        admin = _user(db, get_settings().platform_admin_email.lower())
        today = libya_today()

        specs = [
            ("libyana", "ليبيانا المنزلية", "إنترنت منزلي في طرابلس وما حولها، مع باقات يومية وشهرية.", "0912001100", "500.00", "سارة التومي", "sara@demo.eshtrakei.local", "طرابلس", "0912001101", False),
            ("madar", "مدار فايبر", "ألياف بصرية في بنغازي للمنازل والمحلات.", "0923002200", "400.00", "عمر البكوش", "omar@demo.eshtrakei.local", "بنغازي", "0923002201", False),
            ("naher", "النهر نت", "تغطية لاسلكية في مصراتة والخمس وزليتن.", "0914003300", "600.00", "هدى الشريف", "huda@demo.eshtrakei.local", "مصراتة", "0914003301", False),
            ("wahat", "واحة سبها", "شركة موقوفة للتجربة. حساب مديرها لا يستطيع تسجيل الدخول.", "0915004400", "200.00", "خالد المبروك", "khaled@demo.eshtrakei.local", "سبها", "0915004401", True),
        ]
        companies: dict[str, Company] = {}
        for key, name, description, phone, target, manager_name, manager_email, city, manager_phone, _stopped in specs:
            company = _company(name, description, phone, target)
            db.add(company)
            db.commit()
            db.refresh(company)
            create_manager(db, company.id, manager_name, manager_email, PASSWORD)
            manager = _user(db, manager_email)
            manager.city = city
            manager.phone = manager_phone
            db.commit()
            companies[key] = db.get(Company, company.id)

        catalog = {
            "libyana": [
                ("منزلي", "40", 30, 100, 20, 5, True),
                ("عائلي", "70", 30, 250, 50, 10, True),
                ("أعمال", "120", 30, 500, 100, 20, True),
                ("تجريبي متوقف", "15", 7, 20, 8, 2, False),
            ],
            "madar": [
                ("منزلي", "45", 30, 120, 30, 8, True),
                ("عائلي", "85", 30, 300, 60, 15, True),
                ("أعمال", "140", 30, 600, 120, 30, True),
            ],
            "naher": [
                ("منزلي", "35", 30, 80, 16, 4, True),
                ("عائلي", "65", 30, 200, 40, 10, True),
                ("أعمال", "110", 30, 400, 80, 20, True),
            ],
            "wahat": [
                ("منزلي", "30", 30, 60, 10, 2, True),
            ],
        }
        for key, rows in catalog.items():
            company = companies[key]
            for name, price, days, data_gb, down, up, available in rows:
                create_package(
                    db,
                    company.id,
                    PackageBody(
                        name=name,
                        price=Decimal(price),
                        duration_amount=days,
                        duration_unit=DurationUnit.days,
                        data_gb=data_gb,
                        speed_mbps=down,
                        upload_mbps=up,
                    ),
                )
                if not available:
                    package = _package(db, company.id, name)
                    stop_package(db, company.id, package.id)

        def pkg(key: str, name: str) -> Package:
            return _package(db, companies[key].id, name)

        create_coupon(db, companies["libyana"].id, CouponCreate(code="WELCOME10", discount_amount=Decimal("10"), expires_at=utc_now() + timedelta(days=90), max_total_uses=30))
        create_coupon(db, companies["libyana"].id, CouponCreate(code="ONCE5", discount_amount=Decimal("5"), expires_at=utc_now() + timedelta(days=60), max_total_uses=1))
        create_coupon(db, companies["madar"].id, CouponCreate(code="MADAR20", discount_amount=Decimal("20"), expires_at=utc_now() + timedelta(days=60), max_total_uses=10))
        create_coupon(db, companies["naher"].id, CouponCreate(code="NAHER15", discount_amount=Decimal("15"), expires_at=utc_now() + timedelta(days=45), max_total_uses=10))
        summer = create_coupon(db, companies["madar"].id, CouponCreate(code="SUMMER", discount_amount=Decimal("8"), expires_at=utc_now() + timedelta(days=10), max_total_uses=5))
        expired = db.get(Coupon, summer.id)
        expired.expires_at = utc_now() - timedelta(days=2)
        db.commit()

        towers = {
            "libyana": [("برج تاجوراء", 32.8872, 13.1913, 3500), ("برج جنزور", 32.8200, 13.0500, 2800), ("برج عين زارة", 32.8300, 13.2800, 2200)],
            "madar": [("برج الصابري", 32.1167, 20.0667, 3000), ("برج السلماني", 32.0900, 20.1000, 2400)],
            "naher": [("برج قصر أحمد", 32.3754, 15.0925, 3200), ("برج زليتن", 32.4674, 14.5687, 2600)],
            "wahat": [("برج المهدية", 27.0377, 14.4283, 2000)],
        }
        for key, rows in towers.items():
            for name, lat, lng, radius in rows:
                add_tower(db, companies[key].id, TowerBody(name=name, latitude=lat, longitude=lng, radius_meters=radius))

        ads = {
            "libyana": [("سرعة ثابتة طول الشهر", "باقة العائلة بـ 50 ميغابت تنزيل و10 ميغابت رفع."), ("تركيب خلال يومين", "الفرق الفنية تغطي طرابلس وجنزور وتاجوراء.")],
            "madar": [("فايبر بدون عقد سنوي", "ادفع شهرياً وأوقف الباقة متى شئت."), ("خصم المحلات", "استخدم MADAR20 على باقة العائلة.")],
            "naher": [("تغطية الساحل", "أبراج في مصراتة وزليتن."), ("دعم فني على الهاتف", "الرد خلال ساعات العمل.")],
        }
        for key, rows in ads.items():
            for title, body in rows:
                db.add(Advertisement(company_id=companies[key].id, title=title, body=body, created_at=utc_now()))
        db.commit()

        clients = [
            ("أحمد الزروق", "ahmad@demo.eshtrakei.local", "طرابلس", "0911111001", "200"),
            ("فاطمة بن غشير", "fatima@demo.eshtrakei.local", "بنغازي", "0922222002", "90"),
            ("سالم المصراتي", "salem@demo.eshtrakei.local", "مصراتة", "0913333003", "60"),
            ("نورا الترهوني", "nora@demo.eshtrakei.local", "بنغازي", "0924444004", "50"),
            ("يوسف الزاوي", "yousef@demo.eshtrakei.local", "الزاوية", "0915555005", "180"),
            ("مريم الخماس", "mariam@demo.eshtrakei.local", "مصراتة", "0916666006", "100"),
        ]
        people: dict[str, User] = {}
        for name, email, city, phone, wallet in clients:
            db.add(
                User(
                    full_name=name,
                    city=city,
                    phone=phone,
                    email=email,
                    password_hash=hash_password(PASSWORD),
                    role=UserRole.client,
                    is_active=True,
                    created_at=utc_now(),
                )
            )
            db.commit()
            person = _user(db, email)
            top_up(db, person.id, Decimal(wallet), "success")
            people[email] = _user(db, email)

        db.add(
            User(
                full_name="حساب موقوف",
                city="طرابلس",
                phone="0910000000",
                email="blocked@demo.eshtrakei.local",
                password_hash=hash_password(PASSWORD),
                role=UserRole.client,
                is_active=False,
                created_at=utc_now(),
            )
        )
        db.commit()

        ahmad = people["ahmad@demo.eshtrakei.local"]
        fatima = people["fatima@demo.eshtrakei.local"]
        salem = people["salem@demo.eshtrakei.local"]
        nora = people["nora@demo.eshtrakei.local"]
        mariam = people["mariam@demo.eshtrakei.local"]

        ahmad_home = _buy(db, ahmad.id, companies["libyana"].id, pkg("libyana", "منزلي").id, "demo-ahmad-libyana-home", wallet=True)
        ahmad_madar = _buy(db, ahmad.id, companies["madar"].id, pkg("madar", "عائلي").id, "demo-ahmad-madar-family")
        _shift(db, ahmad_madar, start_days_ago=29, end_in_days=1)

        fatima_naher = _buy(db, fatima.id, companies["naher"].id, pkg("naher", "عائلي").id, "demo-fatima-naher", coupon="NAHER15")
        _shift(db, fatima_naher, start_days_ago=27, end_in_days=3)

        salem_old = _buy(db, salem.id, companies["libyana"].id, pkg("libyana", "منزلي").id, "demo-salem-once", coupon="ONCE5")
        _shift(db, salem_old, start_days_ago=40, end_in_days=-10)

        failed = purchase(
            db,
            salem.id,
            PurchaseBody(
                company_id=companies["madar"].id,
                package_id=pkg("madar", "منزلي").id,
                idempotency_key="demo-salem-fail",
                simulated_outcome="failure",
            ),
        )
        if failed.payment_status != "failed":
            raise SystemExit("expected a failed demo payment")

        _buy(db, nora.id, companies["madar"].id, pkg("madar", "منزلي").id, "demo-nora-madar")
        mariam_current = _buy(db, mariam.id, companies["naher"].id, pkg("naher", "منزلي").id, "demo-mariam-naher")
        renewed = renew(
            db,
            mariam.id,
            mariam_current,
            RenewBody(idempotency_key="demo-mariam-renew", simulated_outcome="success"),
        )
        if renewed.payment_status != "succeeded":
            raise SystemExit(f"renewal failed: {renewed.message}")

        yousef = people["yousef@demo.eshtrakei.local"]
        history = [
            (ahmad, "libyana", "عائلي", 110, 30),
            (fatima, "libyana", "منزلي", 75, 30),
            (salem, "libyana", "أعمال", 6, 2),
            (nora, "madar", "أعمال", 100, 30),
            (mariam, "madar", "عائلي", 48, 20),
            (ahmad, "madar", "منزلي", 8, 3),
            (yousef, "naher", "أعمال", 90, 30),
            (fatima, "naher", "منزلي", 50, 20),
            (nora, "naher", "عائلي", 4, 1),
        ]
        for client, key, name, days_ago, duration in history:
            _closed_sale(db, client, companies[key], pkg(key, name), days_ago=days_ago, duration_days=duration)

        create_complaint(
            db,
            ahmad.id,
            ComplaintCreate(kind="complaint", target="company", company_id=companies["libyana"].id, message="السرعة تنخفض بعد العاشرة مساءً في تاجوراء."),
        )
        platform_complaint = create_complaint(
            db,
            fatima.id,
            ComplaintCreate(kind="complaint", target="platform", message="لم تصلني رسالة تأكيد الشراء على البريد."),
        )
        reply(db, platform_complaint.id, admin.id, ReplyBody(message="أعدنا إرسال الفاتورة. إذا لم تصل خلال ساعة راسلينا مرة أخرى."), None)
        madar_ticket = create_complaint(
            db,
            salem.id,
            ComplaintCreate(kind="technical_support", target="company", company_id=companies["madar"].id, message="جهاز الاستقبال يعيد التشغيل كل ساعة."),
        )
        reply(db, madar_ticket.id, _user(db, "omar@demo.eshtrakei.local").id, ReplyBody(message="حدّثنا الجهاز عن بعد. راقب الإشارة اليوم وأخبرنا إن تكرر الانقطاع."), companies["madar"].id)
        create_complaint(
            db,
            nora.id,
            ComplaintCreate(kind="complaint", target="company", company_id=companies["madar"].id, message="الفاتورة تظهر مبلغاً مختلفاً عن سعر الباقة في المتجر."),
        )
        create_support(db, _user(db, "huda@demo.eshtrakei.local").id, companies["naher"].id, "نحتاج تفعيل شحن رصيد الشركة من داخل لوحة المدير.")
        answered = create_support(db, _user(db, "sara@demo.eshtrakei.local").id, companies["libyana"].id, "هل يمكن رفع حد استخدام الكوبون WELCOME10؟")
        reply(db, answered.id, admin.id, ReplyBody(message="يمكنكم إنشاء كوبون جديد بحد أعلى من صفحة الكوبونات."), None)

        for key, amount in (("libyana", "400"), ("madar", "200"), ("naher", "80"), ("wahat", "50")):
            credit_company(db, companies[key].id, Decimal(amount), "رصيد افتتاحي تجريبي")

        price = banner_price(db)
        banner_rows = [
            ("libyana", "عرض الصيف من ليبيانا", "خصم على باقة العائلة هذا الشهر.", "pending"),
            ("madar", "فايبر بنغازي", "تركيب مجاني للمشتركين الجدد.", "pending"),
            ("naher", "تغطية زليتن", "برج جديد دخل الخدمة.", "pending"),
        ]
        created_banners = []
        for key, title, body, _status in banner_rows:
            row = PlatformBanner(
                company_id=companies[key].id,
                title=title,
                body=body,
                is_active=False,
                status="pending_approval",
                price=price,
                created_at=utc_now(),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            push_role(db, UserRole.platform_admin, f"banner_request_{row.id}", f"طلب بانر جديد من {companies[key].name}: {title}")
            db.commit()
            created_banners.append(row)
        approve_banner(db, created_banners[0].id, admin.id)
        reject_banner(db, created_banners[2].id, admin.id)

        db.add(
            CompanyJoinRequest(
                name="شركة الجبل للاتصالات",
                description="طلب انضمام جديد بانتظار مراجعة مدير المنصة. التغطية المقترحة: غريان ويفرن.",
                phone="0917777007",
                status=JoinRequestStatus.pending,
                created_at=utc_now(),
            )
        )
        db.add(
            CompanyJoinRequest(
                name="شركة الساحل",
                description="طلب مرفوض سابقاً لأن بيانات الهاتف كانت ناقصة.",
                phone="0918888008",
                status=JoinRequestStatus.rejected,
                reviewed_by=admin.id,
                reviewed_at=utc_now() - timedelta(days=12),
                created_at=utc_now() - timedelta(days=14),
            )
        )
        db.commit()

        stop_company(db, companies["wahat"].id)
        run_expiry_check(db)

        from backend.notifications.models import Notification

        notice = db.scalar(select(Notification).where(Notification.client_id == ahmad.id).order_by(Notification.id.desc()))
        if notice is not None:
            notice.is_read = True
            db.commit()

        print("Demo data created.")
        print(f"Shared password: {PASSWORD}")
        print(f"Admin: {get_settings().platform_admin_email}")
    except AppError as exc:
        db.rollback()
        raise SystemExit(f"{exc.code}: {exc.message}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
