"""Fill the local database with demo companies, people, and activity.

Safe to run more than once: if the demo client already exists, it leaves the database unchanged.
Existing accounts outside @demo.eshtrakei.local are kept.
"""

import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from backend._core.security import hash_password
from backend.auth.models import User
from backend.banners.models import PlatformBanner
from backend.banners.services import approve_banner, reject_banner
from backend.companies.models import Company, CompanyJoinRequest
from backend.companies.services import create_manager
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
MARKER = "abdelsamad@demo.eshtrakei.local"
ROOT = Path(__file__).resolve().parents[2]
PEOPLE_DIR = ROOT / "people"
AVATARS = {
    "sara@demo.eshtrakei.local": "random-person (3).jpeg",
    "omar@demo.eshtrakei.local": "random-person (1).jpeg",
    "huda@demo.eshtrakei.local": "random-person (4).jpeg",
    "khaled@demo.eshtrakei.local": "random-person (10).jpeg",
    "laila@demo.eshtrakei.local": "random-person (8).jpeg",
    "yousef.mgr@demo.eshtrakei.local": "random-person (5).jpeg",
    "mariam.mgr@demo.eshtrakei.local": "random-person (11).jpeg",
    "abdelsamad@demo.eshtrakei.local": "random-person (7).jpeg",
    "muaath@demo.eshtrakei.local": "random-person (2).jpeg",
    "salem@demo.eshtrakei.local": "random-person.jpeg",
    "yousef@demo.eshtrakei.local": "random-person (6).jpeg",
    "mariam@demo.eshtrakei.local": "random-person (9).jpeg",
}


def _user(db, email: str) -> User:
    row = db.scalar(select(User).where(User.email == email))
    if row is None:
        raise SystemExit(f"missing user {email}")
    return row


def _assign_avatars(db) -> None:
    dest_dir = ROOT / "backend" / "storage" / "avatars"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for email, filename in AVATARS.items():
        source = PEOPLE_DIR / filename
        if not source.is_file():
            raise SystemExit(f"missing portrait {source}")
        user = _user(db, email)
        dest_name = f"user-{user.id}.jpg"
        shutil.copyfile(source, dest_dir / dest_name)
        user.avatar_path = f"avatars/{dest_name}"
    db.commit()


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
            ("jeel", "جيل نت", "إنترنت منزلي في طرابلس وما حولها، مع باقات يومية وشهرية.", "0912001100", "500.00", "سارة التومي", "sara@demo.eshtrakei.local", "طرابلس", "0912001101"),
            ("awal", "أوال نت", "ألياف بصرية في بنغازي للمنازل والمحلات.", "0923002200", "400.00", "عمر البكوش", "omar@demo.eshtrakei.local", "بنغازي", "0923002201"),
            ("giga", "جيجا", "تغطية لاسلكية في مصراتة والخمس وزليتن.", "0914003300", "600.00", "هدى الشريف", "huda@demo.eshtrakei.local", "مصراتة", "0914003301"),
            ("ion", "أيون", "خدمة لاسلكية في الزاوية وصبراتة وصرمان.", "0925005500", "350.00", "خالد المبروك", "khaled@demo.eshtrakei.local", "الزاوية", "0925005501"),
            ("abraj", "أبراج ليبيا", "أبراج تغطية في طرابلس وتاجوراء وجنزور.", "0916006600", "700.00", "ليلى بن موسى", "laila@demo.eshtrakei.local", "طرابلس", "0916006601"),
            ("hadatha", "الحداثة نت", "باقات منزلية وأعمال في الخمس وزليتن.", "0917007700", "450.00", "يوسف الحداد", "yousef.mgr@demo.eshtrakei.local", "الخمس", "0917007701"),
            ("ozone", "أوزون", "إنترنت في سبها ومرزق وأوباري.", "0918008800", "250.00", "مريم السنوسي", "mariam.mgr@demo.eshtrakei.local", "سبها", "0918008801"),
        ]
        companies: dict[str, Company] = {}
        for key, name, description, phone, target, manager_name, manager_email, city, manager_phone in specs:
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
            "jeel": [
                ("منزلي", "40", 30, 100, 20, 5, True),
                ("عائلي", "70", 30, 250, 50, 10, True),
                ("أعمال", "120", 30, 500, 100, 20, True),
                ("تجريبي متوقف", "15", 7, 20, 8, 2, False),
            ],
            "awal": [
                ("منزلي", "45", 30, 120, 30, 8, True),
                ("عائلي", "85", 30, 300, 60, 15, True),
                ("أعمال", "140", 30, 600, 120, 30, True),
            ],
            "giga": [
                ("منزلي", "35", 30, 80, 16, 4, True),
                ("عائلي", "65", 30, 200, 40, 10, True),
                ("أعمال", "110", 30, 400, 80, 20, True),
            ],
            "ion": [
                ("منزلي", "38", 30, 90, 20, 5, True),
                ("عائلي", "68", 30, 220, 40, 10, True),
                ("أعمال", "115", 30, 450, 80, 20, True),
            ],
            "abraj": [
                ("منزلي", "42", 30, 110, 25, 6, True),
                ("عائلي", "78", 30, 280, 50, 12, True),
                ("أعمال", "130", 30, 550, 100, 25, True),
            ],
            "hadatha": [
                ("منزلي", "36", 30, 90, 18, 4, True),
                ("عائلي", "66", 30, 210, 40, 10, True),
                ("أعمال", "112", 30, 420, 80, 20, True),
            ],
            "ozone": [
                ("منزلي", "30", 30, 60, 10, 2, True),
                ("عائلي", "55", 30, 150, 25, 6, True),
                ("أعمال", "95", 30, 300, 50, 12, True),
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

        create_coupon(db, companies["jeel"].id, CouponCreate(code="WELCOME10", discount_amount=Decimal("10"), expires_at=utc_now() + timedelta(days=90), max_total_uses=30))
        create_coupon(db, companies["jeel"].id, CouponCreate(code="ONCE5", discount_amount=Decimal("5"), expires_at=utc_now() + timedelta(days=60), max_total_uses=1))
        create_coupon(db, companies["awal"].id, CouponCreate(code="AWAL20", discount_amount=Decimal("20"), expires_at=utc_now() + timedelta(days=60), max_total_uses=10))
        create_coupon(db, companies["giga"].id, CouponCreate(code="GIGA15", discount_amount=Decimal("15"), expires_at=utc_now() + timedelta(days=45), max_total_uses=10))
        summer = create_coupon(db, companies["awal"].id, CouponCreate(code="SUMMER", discount_amount=Decimal("8"), expires_at=utc_now() + timedelta(days=10), max_total_uses=5))
        expired = db.get(Coupon, summer.id)
        expired.expires_at = utc_now() - timedelta(days=2)
        db.commit()

        towers = {
            "jeel": [("برج تاجوراء", 32.8872, 13.1913, 3500), ("برج جنزور", 32.8200, 13.0500, 2800), ("برج عين زارة", 32.8300, 13.2800, 2200)],
            "awal": [("برج الصابري", 32.1167, 20.0667, 3000), ("برج السلماني", 32.0900, 20.1000, 2400)],
            "giga": [("برج قصر أحمد", 32.3754, 15.0925, 3200), ("برج زليتن", 32.4674, 14.5687, 2600)],
            "ion": [("برج الزاوية", 32.7522, 12.7278, 3000), ("برج صبراتة", 32.7933, 12.4885, 2400)],
            "abraj": [("برج سوق الجمعة", 32.8500, 13.2200, 2700), ("برج قرقارش", 32.8700, 13.1200, 2200)],
            "hadatha": [("برج الخمس", 32.6486, 14.2619, 2800), ("برج زليتن الوسط", 32.4674, 14.5720, 2000)],
            "ozone": [("برج سبها", 27.0377, 14.4283, 2500), ("برج أوباري", 26.5900, 12.7700, 2000)],
        }
        for key, rows in towers.items():
            for name, lat, lng, radius in rows:
                add_tower(db, companies[key].id, TowerBody(name=name, latitude=lat, longitude=lng, radius_meters=radius))

        clients = [
            ("عبد الصمد المجذوب", "abdelsamad@demo.eshtrakei.local", "طرابلس", "0911111001", "200"),
            ("معاذ ابو شوشه", "muaath@demo.eshtrakei.local", "بنغازي", "0922222002", "90"),
            ("سالم المصراتي", "salem@demo.eshtrakei.local", "مصراتة", "0913333003", "60"),
            ("يوسف الزاوي", "yousef@demo.eshtrakei.local", "الزاوية", "0915555005", "180"),
            ("مريم الخماس", "mariam@demo.eshtrakei.local", "سبها", "0916666006", "100"),
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

        abdelsamad = people["abdelsamad@demo.eshtrakei.local"]
        muaath = people["muaath@demo.eshtrakei.local"]
        salem = people["salem@demo.eshtrakei.local"]
        yousef = people["yousef@demo.eshtrakei.local"]
        mariam = people["mariam@demo.eshtrakei.local"]

        abdelsamad_home = _buy(db, abdelsamad.id, companies["jeel"].id, pkg("jeel", "منزلي").id, "demo-abdelsamad-jeel-home", wallet=True)
        abdelsamad_awal = _buy(db, abdelsamad.id, companies["awal"].id, pkg("awal", "عائلي").id, "demo-abdelsamad-awal-family")
        _shift(db, abdelsamad_awal, start_days_ago=29, end_in_days=1)

        muaath_giga = _buy(db, muaath.id, companies["giga"].id, pkg("giga", "عائلي").id, "demo-muaath-giga", coupon="GIGA15")
        _shift(db, muaath_giga, start_days_ago=27, end_in_days=3)

        salem_old = _buy(db, salem.id, companies["jeel"].id, pkg("jeel", "منزلي").id, "demo-salem-once", coupon="ONCE5")
        _shift(db, salem_old, start_days_ago=40, end_in_days=-10)

        failed = purchase(
            db,
            salem.id,
            PurchaseBody(
                company_id=companies["awal"].id,
                package_id=pkg("awal", "منزلي").id,
                idempotency_key="demo-salem-fail",
                simulated_outcome="failure",
            ),
        )
        if failed.payment_status != "failed":
            raise SystemExit("expected a failed demo payment")

        _buy(db, yousef.id, companies["ion"].id, pkg("ion", "منزلي").id, "demo-yousef-ion")
        mariam_current = _buy(db, mariam.id, companies["ozone"].id, pkg("ozone", "منزلي").id, "demo-mariam-ozone")
        renewed = renew(
            db,
            mariam.id,
            mariam_current,
            RenewBody(idempotency_key="demo-mariam-renew", simulated_outcome="success"),
        )
        if renewed.payment_status != "succeeded":
            raise SystemExit(f"renewal failed: {renewed.message}")

        history = [
            (abdelsamad, "jeel", "عائلي", 110, 30),
            (muaath, "jeel", "منزلي", 75, 30),
            (salem, "jeel", "أعمال", 6, 2),
            (yousef, "awal", "أعمال", 100, 30),
            (mariam, "awal", "عائلي", 48, 20),
            (abdelsamad, "awal", "منزلي", 8, 3),
            (yousef, "giga", "أعمال", 90, 30),
            (muaath, "giga", "منزلي", 50, 20),
            (salem, "ion", "عائلي", 20, 15),
            (abdelsamad, "abraj", "منزلي", 40, 30),
            (muaath, "hadatha", "عائلي", 35, 30),
            (mariam, "ozone", "عائلي", 60, 30),
        ]
        for client, key, name, days_ago, duration in history:
            _closed_sale(db, client, companies[key], pkg(key, name), days_ago=days_ago, duration_days=duration)

        create_complaint(
            db,
            abdelsamad.id,
            ComplaintCreate(kind="complaint", target="company", company_id=companies["jeel"].id, message="السرعة تنخفض بعد العاشرة مساءً في تاجوراء."),
        )
        platform_complaint = create_complaint(
            db,
            muaath.id,
            ComplaintCreate(kind="complaint", target="platform", message="لم تصلني رسالة تأكيد الشراء على البريد."),
        )
        reply(db, platform_complaint.id, admin.id, ReplyBody(message="أعدنا إرسال الفاتورة. إذا لم تصل خلال ساعة راسلينا مرة أخرى."), None)
        awal_ticket = create_complaint(
            db,
            salem.id,
            ComplaintCreate(kind="technical_support", target="company", company_id=companies["awal"].id, message="جهاز الاستقبال يعيد التشغيل كل ساعة."),
        )
        reply(db, awal_ticket.id, _user(db, "omar@demo.eshtrakei.local").id, ReplyBody(message="حدّثنا الجهاز عن بعد. راقب الإشارة اليوم وأخبرنا إن تكرر الانقطاع."), companies["awal"].id)
        create_complaint(
            db,
            yousef.id,
            ComplaintCreate(kind="complaint", target="company", company_id=companies["ion"].id, message="الفاتورة تظهر مبلغاً مختلفاً عن سعر الباقة في المتجر."),
        )
        create_support(db, _user(db, "huda@demo.eshtrakei.local").id, companies["giga"].id, "نحتاج تفعيل شحن رصيد الشركة من داخل لوحة المدير.")
        answered = create_support(db, _user(db, "sara@demo.eshtrakei.local").id, companies["jeel"].id, "هل يمكن رفع حد استخدام الكوبون WELCOME10؟")
        reply(db, answered.id, admin.id, ReplyBody(message="يمكنكم إنشاء كوبون جديد بحد أعلى من صفحة الكوبونات."), None)

        for key, amount in (("jeel", "400"), ("awal", "200"), ("giga", "80"), ("ion", "120"), ("abraj", "300"), ("hadatha", "90"), ("ozone", "50")):
            credit_company(db, companies[key].id, Decimal(amount), "رصيد افتتاحي تجريبي")

        price = banner_price(db)
        banner_rows = [
            ("jeel", "عرض الصيف من جيل نت", "خصم على باقة العائلة هذا الشهر.", "pending"),
            ("awal", "فايبر بنغازي", "تركيب مجاني للمشتركين الجدد.", "pending"),
            ("giga", "تغطية زليتن", "برج جديد دخل الخدمة.", "pending"),
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

        _assign_avatars(db)
        run_expiry_check(db)

        from backend.notifications.models import Notification

        notice = db.scalar(select(Notification).where(Notification.client_id == abdelsamad.id).order_by(Notification.id.desc()))
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
