/**
 * Security audit findings -> Word documents
 * Survey NSPI UZ - Deep security test results
 */
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
        BorderStyle, WidthType, ShadingType, PageNumber, PageBreak } = require('docx');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, 'results');
fs.mkdirSync(OUT, { recursive: true });

const PAGE_W = 11906, PAGE_H = 16838, MARGIN = 1008;
const CONTENT_W = PAGE_W - MARGIN * 2;
const BLUE = "1E3A5F", DARK = "0F172A", GRAY = "64748B";
const SEV = {
  CRITICAL: { fill: "7F1D1D", text: "FFFFFF", badge: "FEE2E2", badgeText: "991B1B" },
  HIGH:     { fill: "9A3412", text: "FFFFFF", badge: "FFEDD5", badgeText: "9A3412" },
  MEDIUM:   { fill: "854D0E", text: "FFFFFF", badge: "FEF9C3", badgeText: "854D0E" },
  LOW:      { fill: "1E40AF", text: "FFFFFF", badge: "DBEAFE", badgeText: "1E40AF" },
  INFO:     { fill: "166534", text: "FFFFFF", badge: "DCFCE7", badgeText: "166534" },
  PASS:     { fill: "166534", text: "FFFFFF", badge: "DCFCE7", badgeText: "166534" },
};

const border = { style: BorderStyle.SINGLE, size: 4, color: "CBD5E1" };
const borders = { top: border, bottom: border, left: border, right: border };
const hBorder = { style: BorderStyle.SINGLE, size: 4, color: BLUE };
const hBorders = { top: hBorder, bottom: hBorder, left: hBorder, right: hBorder };

function cell(text, w, o = {}) {
  return new TableCell({
    borders: o.header ? hBorders : borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: o.fill || (o.header ? BLUE : "FFFFFF"), type: ShadingType.CLEAR },
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [new Paragraph({
      children: [new TextRun({
        text: String(text ?? ""),
        font: "Arial",
        size: o.size ?? 18,
        bold: o.header || o.bold,
        color: o.color || (o.header ? "FFFFFF" : DARK),
      })],
    })],
  });
}

function kvTable(pairs) {
  const c1 = 2800, c2 = CONTENT_W - 2800;
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [c1, c2],
    rows: pairs.map(([k, v], i) => new TableRow({
      children: [
        cell(k, c1, { bold: true, fill: i % 2 ? "F8FAFC" : "F1F5F9", size: 17 }),
        cell(v, c2, { size: 17, fill: i % 2 ? "FFFFFF" : "FAFAFA" }),
      ],
    })),
  });
}

function p(text, o = {}) {
  return new Paragraph({
    spacing: { after: o.after ?? 100, before: o.before ?? 0 },
    alignment: o.align,
    children: [new TextRun({
      text, font: "Arial", size: o.size ?? 21, bold: o.bold,
      italics: o.italics, color: o.color ?? DARK,
    })],
  });
}

function h1(t) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text: t, font: "Arial", size: 30, bold: true, color: BLUE })],
  });
}
function h2(t) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 220, after: 120 },
    children: [new TextRun({ text: t, font: "Arial", size: 24, bold: true, color: "1E40AF" })],
  });
}

function bullets(items, ref) {
  return items.map(t => new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 70 },
    children: [new TextRun({ text: t, font: "Arial", size: 20, color: DARK })],
  }));
}

function codeLines(lines) {
  return lines.map(line => new Paragraph({
    spacing: { after: 20 },
    shading: { fill: "F1F5F9", type: ShadingType.CLEAR },
    children: [new TextRun({ text: line, font: "Consolas", size: 16, color: "1E293B" })],
  }));
}

function spacer(n = 120) {
  return new Paragraph({ spacing: { after: n }, children: [] });
}

function baseNumbering(id) {
  return {
    config: [
      { reference: `b-${id}`, levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: `n-${id}`, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  };
}

function docShell(title, children, numId) {
  return new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 21 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 30, bold: true, font: "Arial", color: BLUE },
          paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, font: "Arial", color: "1E40AF" },
          paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 } },
      ],
    },
    numbering: baseNumbering(numId),
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: PAGE_H },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: BLUE, space: 6 } },
            spacing: { after: 100 },
            children: [
              new TextRun({ text: "Survey NSPI UZ · Security Audit 2026-07-31", font: "Arial", size: 15, color: GRAY }),
              new TextRun({ text: "  |  CONFIDENTIAL", font: "Arial", size: 15, bold: true, color: "B91C1C" }),
            ],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            border: { top: { style: BorderStyle.SINGLE, size: 6, color: "CBD5E1", space: 6 } },
            alignment: AlignmentType.RIGHT,
            children: [
              new TextRun({ text: `${title}  ·  `, font: "Arial", size: 14, color: GRAY }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 14, color: GRAY }),
            ],
          })],
        }),
      },
      children,
    }],
  });
}

const findings = [
  {
    id: "FIND-001",
    severity: "CRITICAL",
    cvss: "9.8",
    title: "Default admin credentials (admin / admin123) accepted",
    status: "CONFIRMED (dynamic)",
    component: "Django Admin /auth_app admin user",
    evidence: [
      "POST /admin/login/ with username=admin&password=admin123 → HTTP 302 Location: /admin/",
      "Subsequent GET /admin/ with session cookie → HTTP 200, full Jazzmin admin dashboard",
      "Staff user 'admin' present; full CRUD over Student, SurveyResponse, Message models",
    ],
    impact: "To'liq tizim boshqaruvi: talaba ma'lumotlari, so'rovnoma javoblari, xabarlar, mas'ul shaxslar. Account takeover of administrative plane.",
    steps: [
      "curl -c cookies.txt http://127.0.0.1:8010/admin/login/  (CSRF olish)",
      "POST username=admin password=admin123 + csrfmiddlewaretoken",
      "GET /admin/ — Site administration ochiladi",
    ],
    remediation: [
      "Productionda demo parolni darhol o'zgartirish / superuser recreate",
      "Admin uchun kuchli parol + 2FA (agar mumkin)",
      "Admin panelni VPN/IP allowlist orqasida tutish",
      "create_demo_data va default admin faqat dev muhitda",
    ],
    refs: ["CLAUDE.md: Admin admin/admin123", "Dynamic test 2026-07-31"],
  },
  {
    id: "FIND-002",
    severity: "CRITICAL",
    cvss: "9.1",
    title: "Redis without authentication + host port exposed; sessions readable",
    status: "CONFIRMED (dynamic)",
    component: "docker-compose redis service; SESSION_ENGINE=cache",
    evidence: [
      "redis-cli PING → PONG (no AUTH required)",
      "CONFIG GET requirepass → empty",
      "Host TCP 127.0.0.1:6380 OPEN; compose maps 6380:6379",
      "KEYS *session* returns django.contrib.sessions.cache* keys",
      "GET session key returns pickled session including _auth_user_id for admin",
    ],
    impact: "Session hijacking, admin session theft, cache poisoning. Redis session store = account takeover vector.",
    steps: [
      "docker exec survey_nspi_uz-redis-1 redis-cli PING",
      "docker run --rm --network survey_nspi_uz_default redis:7-alpine redis-cli -h redis KEYS '*session*'",
      "GET session value — _auth_user_id present",
    ],
    remediation: [
      "Redis requirepass + strong password; ACL",
      "Host bind olib tashlash yoki 127.0.0.1 only (ichki Docker network yetarli)",
      "SESSION_COOKIE va Redis tarmog'ini izolyatsiya qilish",
      "Productionda Redis faqat private network",
    ],
    refs: ["settings.py SESSION_ENGINE", "docker-compose.yml redis ports"],
  },
  {
    id: "FIND-003",
    severity: "HIGH",
    cvss: "7.4",
    title: "Open Redirect via next / login_next_url",
    status: "CONFIRMED (code + Django redirect behavior)",
    component: "auth_app/views.py login_view, _handle_student_login, _handle_employee_login, OAuth handlers",
    evidence: [
      "request.session['login_next_url'] = request.GET.get('next') — hech qanday allowlist yo'q",
      "return redirect(next_url or 'dashboard') — to'g'ridan-to'g'ri tashqi URL",
      "django.shortcuts.redirect('https://evil.example/phish') → Location: https://evil.example/phish",
      "Lines ~66-67, 73-74, 193-194, 239-240, 454-455, 497-498",
    ],
    impact: "Phishing after legitimate login (HEMIS branding trust). Token/session stealer sahifalariga yo'naltirish.",
    steps: [
      "GET /login/?next=https://evil.example/phish — next sessionga yoziladi",
      "Muvaffaqiyatli login → redirect evil.example",
      "Ham xuddi shu OAuth login oqimida login_next_url ishlatiladi",
    ],
    remediation: [
      "django.utils.http.url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=...)",
      "Faqat relative path ( '/' bilan boshlanadigan, '//' emas ) ruxsat berish",
      "Barcha redirect(next_url) joylarini bitta helper orqali o'tkazish",
    ],
    refs: ["views.py open redirect sinks"],
  },
  {
    id: "FIND-004",
    severity: "HIGH",
    cvss: "6.5",
    title: "Unauthenticated exposure of ResponsiblePerson PII on /responsibles/",
    status: "CONFIRMED (dynamic)",
    component: "ResponsiblePersonListView — no LoginRequired / decorator",
    evidence: [
      "GET /responsibles/ without session → HTTP 200",
      "Page leaks: phone tel:+998901234568, email karimova@nspi.uz, nazarov@nspi.uz, Telegram handles",
      "Class ResponsiblePersonListView(ListView) — no auth mixin",
    ],
    impact: "Staff contact data harvesting, spam, social engineering against university staff.",
    steps: [
      "curl -s http://127.0.0.1:8010/responsibles/ | findstr mailto tel t.me",
    ],
    remediation: [
      "@method_decorator(custom_login_required_with_token_refresh) yoki LoginRequiredMixin",
      "Kerak bo'lsa faqat autentifikatsiyalangan talabaga ko'rsatish",
      "Public katalog kerak bo'lsa — minimal maydonlar (ism, lavozim), telefon/email yashirish",
    ],
    refs: ["views.py ResponsiblePersonListView", "evidence/responsibles.html"],
  },
  {
    id: "FIND-005",
    severity: "HIGH",
    cvss: "8.6",
    title: "PostgreSQL default password and host port published",
    status: "CONFIRMED (dynamic + config)",
    component: "docker-compose.yml db; settings DATABASES defaults",
    evidence: [
      "POSTGRES_PASSWORD=super_secret_password in compose",
      "settings default DB_PASSWORD='super_secret_password' — runtime confirms DB_PASSWORD_DEFAULT True",
      "Host port 5433->5432 OPEN (TCP connect success)",
      "docker exec psql -U survey_user works with that password",
    ],
    impact: "To'liq DB o'qish/yozish: students, survey answers, messages. Lateral movement from shared host.",
    steps: [
      "TCP connect 127.0.0.1:5433",
      "psql -h 127.0.0.1 -p 5433 -U survey_user -d survey_prod_db",
    ],
    remediation: [
      "Kuchli unique parol .env da; defaultni olib tashlash",
      "Host ports: olib tashlash yoki 127.0.0.1:5433:5432",
      "Productionda DB faqat internal Docker network",
    ],
    refs: ["docker-compose.yml", "settings.py DATABASES"],
  },
  {
    id: "FIND-006",
    severity: "HIGH",
    cvss: "6.5",
    title: "Survey submit API missing is_open / is_active server-side checks",
    status: "CONFIRMED (code review)",
    component: "submit_survey_api_view",
    evidence: [
      "inspect.getsource(submit_survey_api_view): SUBMIT_HAS_IS_OPEN False, SUBMIT_HAS_IS_ACTIVE False",
      "survey_detail_view checks is_open, but submit endpoint does not",
      "Only checks non-anonymous duplicate participation",
    ],
    impact: "Yopiq yoki muddati o'tgan so'rovnomaga javob yuborish (UI bypass). Business logic abuse.",
    steps: [
      "Open survey in UI then close dates in admin",
      "Replay POST /api/surveys/<pk>/submit/ with valid session",
    ],
    remediation: [
      "submit da: if not survey.is_open or not survey.is_active: return 403",
      "DRF SurveySubmitView da CanRespondToSurvey is_open tekshiradi — web submit bilan bir xil qilish",
    ],
    refs: ["views.py:697-762", "permissions.py CanRespondToSurvey"],
  },
  {
    id: "FIND-007",
    severity: "HIGH",
    cvss: "5.4",
    title: "Answer choice IDs not bound to target question/survey",
    status: "CONFIRMED (code review)",
    component: "submit_survey_api_view single_choice / multiple_choice handling",
    evidence: [
      "answer.selected_choice_id = int(value) — no Choice.objects.get(id=..., question=question)",
      "selected_choices.set(choice_ids) — no filter by question",
      "Cross-survey choice pollution possible if IDs known",
    ],
    impact: "Survey integrity buzilishi; statistikani buzish; data integrity attack.",
    steps: [
      "Submit answer with choice_id from another question/survey",
    ],
    remediation: [
      "Choice.objects.get(pk=cid, question=question) yoki question.choices.filter(id__in=...)",
      "Invalid ID → 400",
    ],
    refs: ["views.py:745-751"],
  },
  {
    id: "FIND-008",
    severity: "MEDIUM",
    cvss: "6.3",
    title: "MessageReplyView: no object-level auth; uses Django LoginRequiredMixin only",
    status: "CONFIRMED (code review)",
    component: "MessageReplyView",
    evidence: [
      "LoginRequiredMixin (Django User) — not custom_login_required student session",
      "form_valid sets message_id = kwargs['pk'] without checking ownership or staff role",
      "Any authenticated Django user can reply to any message pk",
    ],
    impact: "Vertical/horizontal privilege issues; students using HEMIS session cannot properly use view; staff/users may reply to arbitrary messages.",
    steps: [
      "Authenticate as any Django user",
      "POST /messages/<other_pk>/reply/",
    ],
    remediation: [
      "Staff-only yoki responsible-only; yoki student faqat o'z xabariga",
      "get_object() + ownership check",
      "custom decorator yoki permission mixin",
    ],
    refs: ["views.py MessageReplyView"],
  },
  {
    id: "FIND-009",
    severity: "MEDIUM",
    cvss: "5.3",
    title: "Media files intended to be publicly served; no auth on MEDIA_URL",
    status: "CONFIRMED (config) / PARTIAL (runtime DEBUG=False → Django static() no-op → 404)",
    component: "external_auth_project/urls.py MEDIA routing",
    evidence: [
      "else branch still: urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)",
      "Django static() returns [] when DEBUG=False — current runtime 404 for media (lucky)",
      "Files exist on disk: media/messages_attachments/..., message_qrcodes/...",
      "If DEBUG=True or nginx serves /media/ without auth → direct object reference",
    ],
    impact: "Message attachments and QR codes world-readable when media is served. Sensitive student communications.",
    steps: [
      "Set DEBUG=True or map nginx alias /media/ → media/",
      "GET /media/messages_attachments/1/1/<uuid>.docx without auth",
    ],
    remediation: [
      "Media ni authenticated view orqali berish (django-sendfile / X-Accel-Redirect)",
      "UUID paths yetarli emas — IDOR through URL leak",
      "Nginx da auth yoki internal location",
    ],
    refs: ["urls.py:13-18", "media/ tree"],
  },
  {
    id: "FIND-010",
    severity: "MEDIUM",
    cvss: "5.4",
    title: "Stored XSS risk via mark_safe(text_answer) in admin",
    status: "CONFIRMED (code review)",
    component: "auth_app/admin.py answers_inline_display",
    evidence: [
      "answers_html += f\"...{mark_safe(answer.text_answer)}...\"",
      "User-controlled survey text answers rendered unescaped in admin HTML",
      "Also survey_data_json uses mark_safe(json.dumps(...)) — lower risk if JSON escaped correctly",
    ],
    impact: "Admin session XSS → CSRF admin actions, data theft when staff opens response.",
    steps: [
      "Submit survey text answer: <script>alert(1)</script> or <img onerror=...>",
      "Open response in admin change view",
    ],
    remediation: [
      "mark_safe olib tashlash; format_html + escape",
      "Bleach sanitize if HTML intentionally needed",
    ],
    refs: ["admin.py:357-369"],
  },
  {
    id: "FIND-011",
    severity: "MEDIUM",
    cvss: "5.3",
    title: "No application-level rate limiting on login, submit, messages",
    status: "CONFIRMED (code review)",
    component: "login_view, submit APIs, MessageCreateView",
    evidence: [
      "No django-ratelimit / DRF throttle classes in project",
      "HemisRateLimitError only when upstream HEMIS rate-limits",
      "Local brute-force against login form unbounded from app side",
    ],
    impact: "Credential stuffing, resource exhaustion, Celery QR flood via many messages.",
    steps: [
      "Burst POST /login/ with random passwords",
      "Burst message create",
    ],
    remediation: [
      "django-ratelimit yoki reverse-proxy rate limit (nginx limit_req)",
      "DRF AnonRateThrottle / UserRateThrottle",
      "Account lockout policy",
    ],
    refs: ["grep rate limit — only HEMIS client"],
  },
  {
    id: "FIND-012",
    severity: "MEDIUM",
    cvss: "4.8",
    title: "Missing CSP/HSTS; SECURE_SSL_REDIRECT=False in production profile",
    status: "CONFIRMED (dynamic headers)",
    component: "settings security middleware",
    evidence: [
      "Response headers: X-Frame-Options=DENY, X-Content-Type-Options=nosniff — GOOD",
      "Strict-Transport-Security: absent (SECURE_HSTS_SECONDS=0)",
      "Content-Security-Policy: absent",
      "SECURE_SSL_REDIRECT=False, DEBUG=False",
      "Cookies marked Secure even without forced HTTPS — can break/confuse HTTP deploys",
    ],
    impact: "MITM risk without TLS enforcement; XSS impact higher without CSP.",
    steps: [
      "curl -sI http://127.0.0.1:8010/",
    ],
    remediation: [
      "Production: HTTPS + SECURE_SSL_REDIRECT=True + HSTS",
      "CSP default-src 'self'; script-src carefully",
      "Nginx TLS termination bilan moslashtirish",
    ],
    refs: ["settings.py 83-88", "header probe"],
  },
  {
    id: "FIND-013",
    severity: "MEDIUM",
    cvss: "5.0",
    title: "Anonymous surveys allow unlimited responses (unique_together gap)",
    status: "CONFIRMED (code/model)",
    component: "SurveyResponse unique_together ('survey','student'); anonymous sets student=None",
    evidence: [
      "SurveyResponse.objects.create(..., student=student if not survey.is_anonymous else None)",
      "unique_together does not prevent multiple NULL student rows in PostgreSQL",
      "Anonymous survey id=2 active in DB",
    ],
    impact: "Ballot stuffing; statistics pollution for anonymous surveys.",
    steps: [
      "Repeatedly submit anonymous survey from multiple sessions/IPs",
    ],
    remediation: [
      "Token/cookie one-time response; IP+UA soft limit; captcha",
      "Business decision: accept or constrain anonymous volume",
    ],
    refs: ["models.py unique_together", "views submit"],
  },
  {
    id: "FIND-014",
    severity: "LOW",
    cvss: "3.7",
    title: "JWT refresh rotation/blacklist disabled",
    status: "CONFIRMED (config)",
    component: "SIMPLE_JWT settings",
    evidence: [
      "ROTATE_REFRESH_TOKENS=False",
      "BLACKLIST_AFTER_ROTATION=False",
    ],
    impact: "Stolen refresh tokens remain valid until expiry (1 day).",
    steps: ["Review settings SIMPLE_JWT"],
    remediation: ["Enable rotation + blacklist app if JWT used in production API"],
    refs: ["settings.py SIMPLE_JWT"],
  },
  {
    id: "FIND-015",
    severity: "LOW",
    cvss: "3.1",
    title: "Container runs as root; full project bind-mount in compose",
    status: "CONFIRMED (Dockerfile/compose)",
    component: "Dockerfile, docker-compose volumes",
    evidence: [
      "No USER directive in Dockerfile — process runs as root",
      "volumes: .:/app — host code/secrets writable from container",
    ],
    impact: "Container breakout impact higher; accidental overwrite of host files.",
    steps: ["docker compose exec web whoami"],
    remediation: ["Create non-root user; drop bind mounts in production; multi-stage build"],
    refs: ["Dockerfile"],
  },
  {
    id: "FIND-016",
    severity: "LOW",
    cvss: "2.8",
    title: "Duplicate XFrameOptionsMiddleware; API may leak exception text",
    status: "CONFIRMED (code)",
    component: "settings MIDDLEWARE; api_views SurveySubmitView",
    evidence: [
      "XFrameOptionsMiddleware listed twice",
      "SurveySubmitView: return error with str(e) to client on 500",
    ],
    impact: "Minor config smell; information disclosure via API error messages.",
    steps: ["Trigger exception on submit API"],
    remediation: ["Remove duplicate middleware; generic error messages in production"],
    refs: ["settings.py MIDDLEWARE", "api_views.py:99"],
  },
  {
    id: "FIND-017",
    severity: "PASS",
    cvss: "—",
    title: "OAuth state validation works (fail-closed)",
    status: "CONFIRMED (dynamic)",
    component: "oauth_callback_view",
    evidence: [
      "GET /oauth/callback/?code=x&state=y → 302 /login/ with message state invalid/expired",
      "State stored in cache with delete-after-use",
    ],
    impact: "Positive control — CSRF on OAuth callback mitigated when OAuth configured.",
    steps: ["curl -sI callback with fake state"],
    remediation: ["Keep state TTL short; bind state to session if possible"],
    refs: ["oauth_callback_view"],
  },
  {
    id: "FIND-018",
    severity: "PASS",
    cvss: "—",
    title: "Statistics API denies unauthenticated access",
    status: "CONFIRMED (dynamic)",
    component: "SurveyStatisticsAPIView",
    evidence: [
      "GET /api/surveys/1/statistics/ without auth → 403 JSON",
      "With admin session → 200 including student_info PII (expected for staff)",
    ],
    impact: "Positive for anonymous block; ensure only staff (not any authenticated student Django user).",
    steps: ["curl stats without/with cookie"],
    remediation: ["Prefer permission_classes=[IsAdminUser]; keep manual staff check"],
    refs: ["views.py SurveyStatisticsAPIView"],
  },
];

async function writeFinding(f, idx) {
  const sev = SEV[f.severity] || SEV.MEDIUM;
  const children = [
    new Paragraph({
      spacing: { after: 80 },
      children: [new TextRun({ text: f.id, font: "Arial", size: 18, bold: true, color: GRAY })],
    }),
    new Paragraph({
      spacing: { after: 160 },
      children: [new TextRun({ text: f.title, font: "Arial", size: 32, bold: true, color: BLUE })],
    }),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [CONTENT_W],
      rows: [new TableRow({
        children: [new TableCell({
          borders,
          width: { size: CONTENT_W, type: WidthType.DXA },
          shading: { fill: sev.badge, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [
              new TextRun({ text: `  ${f.severity}  `, font: "Arial", size: 20, bold: true, color: sev.badgeText }),
              new TextRun({ text: `  CVSS: ${f.cvss}   ·   ${f.status}`, font: "Arial", size: 18, color: DARK }),
            ],
          })],
        })],
      })],
    }),
    spacer(160),
    kvTable([
      ["ID", f.id],
      ["Severity", f.severity],
      ["CVSS (est.)", f.cvss],
      ["Status", f.status],
      ["Component", f.component],
      ["Date", "2026-07-31"],
      ["Environment", "Local Docker (localhost:8010), DEBUG=False"],
    ]),
    h1("Impact"),
    p(f.impact),
    h1("Evidence"),
    ...bullets(f.evidence, `b-${f.id}`),
    h1("Reproduction steps"),
    ...f.steps.map((t, i) => new Paragraph({
      numbering: { reference: `n-${f.id}`, level: 0 },
      spacing: { after: 70 },
      children: [new TextRun({ text: t, font: "Arial", size: 20, color: DARK })],
    })),
    h1("Remediation"),
    ...bullets(f.remediation, `b-${f.id}`),
    h2("References"),
    ...bullets(f.refs, `b-${f.id}`),
  ];

  const doc = docShell(f.id, children, f.id);
  const buf = await Packer.toBuffer(doc);
  const fname = `${f.id}_${f.severity}_${slug(f.title)}.docx`;
  const fp = path.join(OUT, fname);
  fs.writeFileSync(fp, buf);
  return { file: fname, ...f };
}

function slug(s) {
  return s.toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .slice(0, 50);
}

async function writeExecutive(results) {
  const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, PASS: 0, INFO: 0 };
  results.forEach(r => { counts[r.severity] = (counts[r.severity] || 0) + 1; });
  const open = results.filter(r => r.severity !== "PASS" && r.severity !== "INFO");

  const children = [
    p("SECURITY ASSESSMENT REPORT", { size: 18, color: "0EA5E9", bold: true, align: AlignmentType.CENTER }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
      children: [new TextRun({ text: "Survey NSPI UZ — Chuqurlashtirilgan sinov natijalari", font: "Arial", size: 34, bold: true, color: BLUE })],
    }),
    p("Versiya 1.0  ·  2026-07-31  ·  Method: SAST + Config + Dynamic (local Docker)", {
      align: AlignmentType.CENTER, size: 18, color: GRAY,
    }),
    spacer(200),
    h1("1. Executive summary"),
    p("Mahalliy Docker muhitida (web:8010, db:5433, redis:6380) ssenariy bo'yicha chuqurlashtirilgan xavfsizlik sinovi o'tkazildi. Test non-destructive; tashqi HEMIS tizimiga hujum qilinmadi."),
    p(`Jami yozuvlar: ${results.length}. Kamchiliklar (PASS dan tashqari): ${open.length}.`),
    spacer(100),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [2472, 2472, 2473, 2473],
      rows: [
        new TableRow({ children: [
          cell("CRITICAL", 2472, { header: true, fill: SEV.CRITICAL.fill }),
          cell("HIGH", 2472, { header: true, fill: SEV.HIGH.fill }),
          cell("MEDIUM", 2473, { header: true, fill: SEV.MEDIUM.fill }),
          cell("LOW / PASS", 2473, { header: true, fill: SEV.LOW.fill }),
        ]}),
        new TableRow({ children: [
          cell(String(counts.CRITICAL || 0), 2472, { bold: true, size: 28, align: true, color: SEV.CRITICAL.badgeText }),
          cell(String(counts.HIGH || 0), 2472, { bold: true, size: 28, color: SEV.HIGH.badgeText }),
          cell(String(counts.MEDIUM || 0), 2473, { bold: true, size: 28, color: SEV.MEDIUM.badgeText }),
          cell(`${counts.LOW || 0} / ${counts.PASS || 0}`, 2473, { bold: true, size: 28, color: SEV.LOW.badgeText }),
        ]}),
      ],
    }),
    h1("2. Scope"),
    ...bullets([
      "Target: Survey NSPI UZ (Django 4.2 + Gunicorn + Postgres 15 + Redis 7 + Celery)",
      "URL: http://127.0.0.1:8010",
      "In scope: Auth, session, OAuth callback logic, surveys, messages, admin, Docker exposure, headers",
      "Out of scope: Production Internet host, active exploitation of real HEMIS, destructive DoS",
    ], "b-exec"),
    h1("3. Methodology"),
    ...bullets([
      "Threat-model driven checklist (cyber_test plan v1)",
      "Static code review (views, models, urls, settings, forms, Dockerfile)",
      "Dynamic HTTP probes (curl), admin login test, Redis/Postgres port tests",
      "Django shell verification of redirect behavior and source flags",
    ], "b-exec"),
    h1("4. Findings index"),
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [1400, 1400, 7090],
      rows: [
        new TableRow({ children: [
          cell("ID", 1400, { header: true }),
          cell("Severity", 1400, { header: true }),
          cell("Title", 7090, { header: true }),
        ]}),
        ...results.map(r => new TableRow({
          children: [
            cell(r.id, 1400, { size: 15, bold: true }),
            cell(r.severity, 1400, {
              size: 14, bold: true,
              fill: (SEV[r.severity] || SEV.MEDIUM).badge,
              color: (SEV[r.severity] || SEV.MEDIUM).badgeText,
            }),
            cell(r.title, 7090, { size: 15 }),
          ],
        })),
      ],
    }),
    h1("5. Top risks (business)"),
    ...bullets([
      "CRITICAL: Default admin parol — to'liq admin panel",
      "CRITICAL: Redis sessiyalari parolsiz — admin/session hijack",
      "HIGH: Open redirect — login dan keyin phishing",
      "HIGH: Postgres default parol + port — DB dump",
      "HIGH: /responsibles/ public PII",
      "HIGH: Survey submit business-logic bypass (is_open)",
    ], "b-exec"),
    h1("6. Immediate actions (24–72 soat)"),
    ...[
      "admin parolini o'zgartirish; demo userlarni prod dan olib tashlash",
      "Redis AUTH + portni tashqi bind dan yopish",
      "Postgres parolini almashtirish + host portni yopish",
      "Open redirect ni url_has_allowed_host_and_scheme bilan yopish",
      "/responsibles/ ga auth qo'shish",
      "submit_survey_api_view da is_open/is_active tekshiruvi",
    ].map(t => new Paragraph({
      numbering: { reference: "n-exec", level: 0 },
      spacing: { after: 70 },
      children: [new TextRun({ text: t, font: "Arial", size: 20, color: DARK })],
    })),
    h1("7. Evidence location"),
    p("cyber_test/evidence/ — raw HTTP/HTML/JSON artifacts"),
    p("cyber_test/results/FIND-*.docx — har bir hodisa alohida"),
    p("cyber_test/results/00_Executive_Summary.docx — ushbu hujjat"),
    h1("8. Disclaimer"),
    p("CVSS ballari taxminiy (analyst estimate). Test staging/local uchun. Production retest talab etiladi. Ochiq topilmalar tuzatilgach retest qilinsin.", {
      size: 18, italics: true, color: GRAY,
    }),
  ];

  const doc = docShell("Executive Summary", children, "exec");
  // fix numbering refs for exec - need b-exec and n-exec in doc
  const doc2 = new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 21 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 30, bold: true, font: "Arial", color: BLUE },
          paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, font: "Arial", color: "1E40AF" },
          paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1 } },
      ],
    },
    numbering: {
      config: [
        { reference: "b-exec", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "n-exec", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ],
    },
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: PAGE_H },
          margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: BLUE, space: 6 } },
            children: [
              new TextRun({ text: "Survey NSPI UZ · Security Audit 2026-07-31", font: "Arial", size: 15, color: GRAY }),
              new TextRun({ text: "  |  CONFIDENTIAL", font: "Arial", size: 15, bold: true, color: "B91C1C" }),
            ],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [
              new TextRun({ text: "Executive Summary · ", font: "Arial", size: 14, color: GRAY }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 14, color: GRAY }),
            ],
          })],
        }),
      },
      children,
    }],
  });

  const buf = await Packer.toBuffer(doc2);
  fs.writeFileSync(path.join(OUT, "00_Executive_Summary.docx"), buf);
}

async function main() {
  const results = [];
  for (let i = 0; i < findings.length; i++) {
    const r = await writeFinding(findings[i], i);
    results.push(r);
    console.log("WROTE", r.file);
  }
  await writeExecutive(results);
  console.log("WROTE 00_Executive_Summary.docx");

  // Machine-readable summary for terminal
  const summary = {
    date: "2026-07-31",
    target: "http://127.0.0.1:8010",
    totals: results.reduce((a, r) => { a[r.severity] = (a[r.severity] || 0) + 1; return a; }, {}),
    findings: results.map(r => ({
      id: r.id, severity: r.severity, cvss: r.cvss, title: r.title, status: r.status, file: r.file,
    })),
  };
  fs.writeFileSync(path.join(OUT, "findings_index.json"), JSON.stringify(summary, null, 2));
  console.log("WROTE findings_index.json");
}

main().catch(e => { console.error(e); process.exit(1); });
