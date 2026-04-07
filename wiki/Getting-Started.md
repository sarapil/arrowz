# Getting Started — دليل البدء السريع

## Prerequisites — المتطلبات المسبقة

- Frappe Bench installed — Frappe Bench مثبت
- Python 3.12+ / Node.js 20+
- MariaDB 11.8+
- Redis

## Installation — التثبيت

```bash
# Get the app — تحميل التطبيق
bench get-app arrowz https://github.com/sarapil/arrowz.git

# Install on site — التثبيت على الموقع
bench --site your-site.localhost install-app arrowz

# Run migrations — تشغيل الترحيل
bench --site your-site.localhost migrate

# Build assets — بناء الملفات
bench build --app arrowz
```

## First Steps — الخطوات الأولى

1. **Open Desk** — افتح المكتب: Navigate to `http://your-site:8001/desk`
2. **Find the App** — ابحث عن التطبيق: Look for Arrowz icon on the desk
3. **Configure Settings** — اضبط الإعدادات: Go to Arrowz Settings
4. **Create First Record** — أنشئ أول سجل: Follow the onboarding wizard

## Configuration — الإعدادات

### Required Settings — إعدادات مطلوبة
<!-- List required settings specific to the app -->

### Optional Settings — إعدادات اختيارية
<!-- List optional settings -->

## Need Help? — تحتاج مساعدة؟

- 📖 [Full Wiki](Home) — الويكي الكامل
- 🐛 [Report Bug](https://github.com/sarapil/arrowz/issues/new?template=bug_report.yml)
- ✨ [Request Feature](https://github.com/sarapil/arrowz/issues/new?template=feature_request.yml)
