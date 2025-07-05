# JavaScript Files - ملفات JavaScript

هذا المجلد يحتوي على جميع ملفات JavaScript المطلوبة لتشغيل AI Translator v2.2.4 بشكل صحيح على الخوادم البعيدة.

## قائمة الملفات / File List

### 🔧 Core JavaScript Files - الملفات الأساسية

1. **server-complete-fix.js** - الإصلاح الشامل للخادم البعيد
   - حل شامل لمشكلة تبويبات الإعدادات
   - إصلاح القوائم المنسدلة والترجمات
   - يعمل بشكل مستقل ولا يحتاج ملفات إضافية

2. **tabs-fix.js** - إصلاح التبويبات الأساسي
   - الإصلاح الأصلي لنظام التبويبات
   - يعمل مع معظم حالات الاستخدام

3. **final-tabs-fix.js** - الإصلاح المتقدم للتبويبات
   - إصدار محسن مع دعم أفضل للقوائم المنسدلة
   - يتضمن إصلاحات للترجمة العربية/الإنجليزية

4. **components.js** - إدارة مكونات الواجهة
   - إدارة الشريط الجانبي والقوائم
   - دعم الأجهزة المحمولة والتصميم المتجاوب

5. **settings-enhanced.js** - تحسينات صفحة الإعدادات
   - وظائف متقدمة لإدارة الإعدادات
   - دعم الحفظ التلقائي والتحقق من الصحة

6. **gpu-management.js** - إدارة كروت الرسوميات
   - كشف وإدارة كروت NVIDIA
   - توزيع ذكي للموارد بين الخدمات

7. **file-browser.js** - متصفح الملفات
   - نافذة منبثقة لاختيار المجلدات
   - تصفح آمن للمجلدات والملفات

## 🚀 التنصيب على الخادم البعيد / Remote Server Installation

### الطريقة الأولى: الإصلاح الشامل (الموصى بها)
```html
<!-- إضافة قبل إغلاق </head> في layout.html -->
<script src="{{ url_for('static', filename='js/server-complete-fix.js') }}"></script>
```

### الطريقة الثانية: الملفات المنفصلة
```html
<!-- إضافة جميع الملفات في ترتيب معين -->
<script src="{{ url_for('static', filename='js/components.js') }}"></script>
<script src="{{ url_for('static', filename='js/tabs-fix.js') }}"></script>
<script src="{{ url_for('static', filename='js/final-tabs-fix.js') }}"></script>
<script src="{{ url_for('static', filename='js/settings-enhanced.js') }}"></script>
<script src="{{ url_for('static', filename='js/gpu-management.js') }}"></script>
<script src="{{ url_for('static', filename='js/file-browser.js') }}"></script>
```

## 🛠️ استكشاف الأخطاء / Troubleshooting

### مشكلة: التبويبات لا تعمل
```javascript
// افتح وحدة تحكم المطور (F12) وتحقق من الأخطاء
console.log('Checking for JavaScript errors...');

// تحقق من تحميل الملفات
if (typeof switchCategory === 'function') {
    console.log('✅ JavaScript files loaded correctly');
} else {
    console.log('❌ JavaScript files not loaded');
}
```

### مشكلة: القوائم المنسدلة تظهر true/false
```javascript
// تشغيل إصلاح القوائم يدوياً
if (typeof fixAllDropdownOptions === 'function') {
    fixAllDropdownOptions();
    console.log('✅ Dropdown options fixed');
}
```

## 📋 المتطلبات / Requirements

- Flask application with Jinja2 templates
- Bootstrap CSS framework (optional)
- Modern web browser with ES6 support
- Proper static file serving configuration

## 🔄 التحديثات / Updates

- **v2.2.4**: Added server-complete-fix.js for comprehensive remote server support
- **v2.2.3**: Enhanced dropdown translations and mobile responsiveness
- **v2.2.2**: Fixed GPU management interface and added file browser
- **v2.2.1**: Initial release with basic tab functionality

## 📞 الدعم / Support

إذا واجهت مشاكل في التنصيب، تأكد من:
1. رفع جميع الملفات إلى مجلد `static/js/`
2. إضافة السكريبت المطلوب في `templates/layout.html`
3. إعادة تشغيل خدمة التطبيق
4. مسح ذاكرة التخزين المؤقت للمتصفح

For installation issues, ensure:
1. Upload all files to `static/js/` directory
2. Add required script tags to `templates/layout.html`
3. Restart application service
4. Clear browser cache