# دليل تثبيت نماذج Ollama

هذا الدليل يشرح كيفية تثبيت واستخدام نماذج Ollama في تطبيق AI Translator.

## المتطلبات الأساسية

1. تثبيت برنامج Ollama من [الموقع الرسمي](https://ollama.ai/download) حسب نظام التشغيل الخاص بك (Windows، macOS، Linux).
2. تشغيل خدمة Ollama في الخلفية.

## حل مشكلة "No matching distribution found for ollama-llama3"

إذا واجهت خطأ عند محاولة تثبيت نماذج Ollama مثل:

```
Failed to install ollama-llama3: ERROR: Could not find a version that satisfies the requirement ollama-llama3 (from versions: none) ERROR: No matching distribution found for ollama-llama3
```

فهذا يعني أن التطبيق يحاول تثبيت النموذج باستخدام pip، ولكن حزمة ollama-llama3 غير موجودة في PyPI.

### الحل:

1. تأكد من تثبيت برنامج Ollama من [الموقع الرسمي](https://ollama.ai/download).
2. تأكد من تشغيل خدمة Ollama في الخلفية.
3. استخدم الأمر التالي في سطر الأوامر لتثبيت النموذج مباشرة:

```bash
# في Windows
cmd /c ollama pull llama3

# في macOS أو Linux
ollama pull llama3
```

## النماذج المدعومة

يمكنك تثبيت أي نموذج متاح في Ollama، بما في ذلك:

- llama3
- mistral
- gemma
- phi
- codellama
- llama2
- vicuna
- orca-mini

للحصول على قائمة كاملة بالنماذج المتاحة، قم بزيارة [مكتبة نماذج Ollama](https://ollama.ai/library).

## استكشاف الأخطاء وإصلاحها

### خدمة Ollama لا تعمل

إذا كان برنامج Ollama مثبتًا ولكن الخدمة لا تعمل، ستظهر حالة النموذج كـ "installed_not_running". في هذه الحالة:

1. افتح سطر الأوامر.
2. قم بتشغيل خدمة Ollama باستخدام الأمر:

```bash
ollama serve
```

### مشاكل أخرى

إذا واجهت مشاكل أخرى في تثبيت أو استخدام نماذج Ollama:

1. تأكد من أن لديك أحدث إصدار من Ollama.
2. تحقق من متطلبات النظام للنموذج الذي تحاول تثبيته.
3. تأكد من وجود مساحة كافية على القرص الصلب (بعض النماذج كبيرة الحجم).
4. راجع [وثائق Ollama الرسمية](https://github.com/ollama/ollama/blob/main/README.md) للحصول على مزيد من المعلومات.