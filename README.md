# Eshtrakei

سوق اشتراكات الإنترنت: حساب زبون واحد، عدة شركات، موظف واحد لكل شركة، ومدير منصة واحد.

الواجهة عربية واتجاهها من اليمين إلى اليسار. هذا المستودع يجمع الواجهة والخلفية معًا.

| الجزء | التقنية | المجلد |
| --- | --- | --- |
| الواجهة | Next.js 16، React 19، Tailwind CSS 4 | `frontend/` |
| الخلفية | FastAPI، SQLAlchemy، Alembic | `backend/` |
| قاعدة التطوير | SQLite | تُنشأ محليًا ولا تُرفع |
| الجلسات | Redis | مطلوب أثناء التشغيل |
| مسودات التصميم | HTML | `UI/` |

## التشغيل المحلي

شغّل الأوامر من جذر المشروع إلا عند الدخول إلى `frontend`.

### 1. الخلفية

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend\.env.example backend\.env
```

عدّل `backend/.env` وضع قيمة لـ `JWT_SECRET` و`PLATFORM_ADMIN_PASSWORD`. ثم:

```powershell
alembic upgrade head
python -m backend.scripts.seed_admin
uvicorn backend.main:app --reload
```

الخلفية تعمل على `http://127.0.0.1:8000`. فحص الصحة: `GET /api/health`.

Redis يجب أن يعمل على `redis://localhost:6379/0`.

### 2. الواجهة

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

الواجهة تعمل على `http://localhost:3000` وتعيد توجيه طلبات `/api` إلى الخلفية.

## الاختبارات

```powershell
pytest backend/tests
```

من مجلد الواجهة:

```powershell
npm run lint
```

## ما لا يُرفع

ملفات `.env`، البيئة الافتراضية، `node_modules`، قاعدة `dev.db`، ومجلد الملفات المرفوعة تبقى على جهازك. القوالب الآمنة هي `backend/.env.example` و`frontend/.env.example`.
