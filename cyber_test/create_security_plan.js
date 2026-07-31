const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
        BorderStyle, WidthType, ShadingType, PageNumber, PageBreak } = require('docx');
const fs = require('fs');
const path = require('path');

// A4 content width with ~0.9" margins: 11906 - 2*1296 ≈ 9314
const PAGE_W = 11906;
const PAGE_H = 16838;
const MARGIN = 1008; // 0.7 inch
const CONTENT_W = PAGE_W - MARGIN * 2; // 9890

const border = { style: BorderStyle.SINGLE, size: 4, color: "CBD5E1" };
const borders = { top: border, bottom: border, left: border, right: border };
const headerBorder = { style: BorderStyle.SINGLE, size: 4, color: "1E3A5F" };
const headerBorders = { top: headerBorder, bottom: headerBorder, left: headerBorder, right: headerBorder };

const BLUE = "1E3A5F";
const BLUE_LIGHT = "E8F0FE";
const GRAY = "64748B";
const DARK = "0F172A";
const ACCENT = "0EA5E9";
const RED_BG = "FEF2F2";
const GREEN_BG = "F0FDF4";
const YELLOW_BG = "FFFBEB";

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: opts.line },
    alignment: opts.align,
    ...opts.para,
    children: [new TextRun({
      text,
      font: "Arial",
      size: opts.size ?? 22,
      bold: opts.bold,
      italics: opts.italics,
      color: opts.color ?? DARK,
    })],
  });
}

function runs(parts, spacing = {}) {
  return new Paragraph({
    spacing: { after: 120, ...spacing },
    children: parts.map(part => new TextRun({
      text: part.text,
      font: "Arial",
      size: part.size ?? 22,
      bold: part.bold,
      italics: part.italics,
      color: part.color ?? DARK,
    })),
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: "Arial", size: 32, bold: true, color: BLUE })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, font: "Arial", size: 26, bold: true, color: "1E40AF" })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: "Arial", size: 24, bold: true, color: "334155" })],
  });
}

function bullet(text, ref = "bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 21, color: DARK })],
  });
}

function bulletBold(label, rest, ref = "bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [
      new TextRun({ text: label, font: "Arial", size: 21, bold: true, color: DARK }),
      new TextRun({ text: rest, font: "Arial", size: 21, color: DARK }),
    ],
  });
}

function num(text, ref = "numbers") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 21, color: DARK })],
  });
}

function cell(text, width, opts = {}) {
  const isHeader = opts.header;
  return new TableCell({
    borders: isHeader ? headerBorders : borders,
    width: { size: width, type: WidthType.DXA },
    shading: {
      fill: isHeader ? BLUE : (opts.fill || "FFFFFF"),
      type: ShadingType.CLEAR,
    },
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [new Paragraph({
      children: [new TextRun({
        text,
        font: "Arial",
        size: opts.size ?? 18,
        bold: isHeader || opts.bold,
        color: isHeader ? "FFFFFF" : (opts.color || DARK),
      })],
    })],
  });
}

function multiCell(paragraphs, width, opts = {}) {
  return new TableCell({
    borders: opts.header ? headerBorders : borders,
    width: { size: width, type: WidthType.DXA },
    shading: {
      fill: opts.header ? BLUE : (opts.fill || "FFFFFF"),
      type: ShadingType.CLEAR,
    },
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: paragraphs,
  });
}

function makeTable(colWidths, rows) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows,
  });
}

function spacer(after = 160) {
  return new Paragraph({ spacing: { after }, children: [] });
}

function callout(title, lines, fill = YELLOW_BG) {
  const parts = [
    new Paragraph({
      spacing: { after: 60 },
      children: [new TextRun({ text: title, font: "Arial", size: 20, bold: true, color: BLUE })],
    }),
    ...lines.map(t => new Paragraph({
      spacing: { after: 40 },
      children: [new TextRun({ text: t, font: "Arial", size: 19, color: DARK })],
    })),
  ];
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [new TableRow({
      children: [multiCell(parts, CONTENT_W, { fill })],
    })],
  });
}

function codeBlock(lines) {
  return lines.map(line => new Paragraph({
    spacing: { after: 20 },
    shading: { fill: "F1F5F9", type: ShadingType.CLEAR },
    children: [new TextRun({ text: line, font: "Consolas", size: 17, color: "1E293B" })],
  }));
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "1E40AF" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "334155" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "bullets2",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "bullets3",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "bullets4",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "bullets5",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "phases",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "priority",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "redflags",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "minimal",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
      {
        reference: "nextsteps",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
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
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 8 } },
          spacing: { after: 120 },
          children: [
            new TextRun({ text: "Survey NSPI UZ  ·  Cybersecurity Test Plan", font: "Arial", size: 16, color: GRAY }),
            new TextRun({ text: "  |  ", font: "Arial", size: 16, color: "CBD5E1" }),
            new TextRun({ text: "CONFIDENTIAL", font: "Arial", size: 16, bold: true, color: "B91C1C" }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: "CBD5E1", space: 8 } },
          spacing: { before: 80 },
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "Sahifa ", font: "Arial", size: 16, color: GRAY }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: GRAY }),
            new TextRun({ text: " / ", font: "Arial", size: 16, color: GRAY }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 16, color: GRAY }),
          ],
        })],
      }),
    },
    children: [
      // ===== COVER =====
      spacer(600),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "KIBERXAVFSIZLIK", font: "Arial", size: 28, bold: true, color: ACCENT, characterSpacing: 200 })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: "Chuqurlashtirilgan Test Rejasi", font: "Arial", size: 48, bold: true, color: BLUE })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 1 } },
        spacing: { after: 400 },
        children: [new TextRun({ text: "va Amaliy Playbook", font: "Arial", size: 36, color: "334155" })],
      }),
      spacer(200),
      p("Loyiha: Survey NSPI UZ — Django asosidagi so'rovnoma va xabar platformasi", { align: AlignmentType.CENTER, size: 22, color: GRAY }),
      p("Stack: Django 4.2 · PostgreSQL · Redis · Celery · HEMIS OAuth/API · Gunicorn/Docker", { align: AlignmentType.CENTER, size: 20, color: GRAY }),
      spacer(400),
      makeTable([3200, 6690], [
        new TableRow({ children: [
          cell("Hujjat turi", 3200, { header: true }),
          cell("Security Test Plan / Penetration Test Playbook", 6690),
        ]}),
        new TableRow({ children: [
          cell("Versiya", 3200, { header: true }),
          cell("1.0", 6690),
        ]}),
        new TableRow({ children: [
          cell("Sana", 3200, { header: true }),
          cell("2026-07-31", 6690),
        ]}),
        new TableRow({ children: [
          cell("Muhit", 3200, { header: true }),
          cell("Staging / Test (productionga to'g'ridan-to'g'ri hujum qilinmasin)", 6690),
        ]}),
        new TableRow({ children: [
          cell("Klassifikatsiya", 3200, { header: true }),
          cell("CONFIDENTIAL — faqat vakolatli xodimlar uchun", 6690, { fill: RED_BG, bold: true, color: "991B1B" }),
        ]}),
        new TableRow({ children: [
          cell("Keyingi bosqich", 3200, { header: true }),
          cell("Amaliy non-destructive audit va topilmalar hisoboti", 6690, { fill: GREEN_BG }),
        ]}),
      ]),
      spacer(400),
      p("Bu hujjat skaner hisoboti emas. U xavf modeli, hujum sirtlari, isbotlanadigan test holatlari va hisobot formatini o'z ichiga olgan to'liq metodik rejadir.", {
        align: AlignmentType.CENTER, size: 20, italics: true, color: GRAY,
      }),

      new Paragraph({ children: [new PageBreak()] }),

      // ===== 1 =====
      h1("1. Maqsad, qoida va xavf modeli"),
      h2("1.1. Maqsad"),
      bullet("Maxfiylik buzilishini oldini olish (talaba/hodim ma'lumotlari, so'rovnoma javoblari, xabarlar)"),
      bullet("Ruxsatsiz kirish va imtiyoz oshirishni (privilege escalation) topish"),
      bullet("Integrity: so'rovnoma soxtalashtirish, ovoz/javob manipulyatsiyasi"),
      bullet("Availability: DoS, login flood, resurs charchatish"),

      h2("1.2. Majburiy qoidalar"),
      makeTable([3200, 6690], [
        new TableRow({ children: [
          cell("Qoida", 3200, { header: true }),
          cell("Nima uchun", 6690, { header: true }),
        ]}),
        new TableRow({ children: [
          cell("Faqat ruxsat berilgan muhit (staging / test DB)", 3200, { bold: true, size: 17 }),
          cell("Prodni buzish va real PII oqishini oldini olish", 6690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Scope va out-of-scope yozma kelishuv", 3200, { bold: true, size: 17 }),
          cell("Masalan: HEMIS o'zi, boshqa universitet tizimlari test qamrovidan tashqari bo'lishi mumkin", 6690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Test akkauntlari (2+ talaba, 1 hodim, 1 staff, 1 superuser)", 3200, { bold: true, size: 17 }),
          cell("Horizontal/vertical IDOR va role boundary testlari uchun", 6690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Log va vaqt oynasi qayd etiladi", 3200, { bold: true, size: 17 }),
          cell("\"Bu bizning testimiz\" deb isbotlash va incident chalkashligini oldini olish", 6690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Natija: CVSS + biznes ta'sir + fix prioritet", 3200, { bold: true, size: 17 }),
          cell("Faqat critical/high emas — tushunarli tuzatish rejasi", 6690, { size: 17 }),
        ]}),
      ]),

      h2("1.3. Qimmatli aktivlar (Survey NSPI)"),
      num("Sessiya va HEMIS token (Redis/cache session)"),
      num("OAuth client_id / client_secret, DJANGO_SECRET_KEY, DB parol"),
      num("Talaba akademik profili, so'rovnoma javoblari (anonimlik da'vosi bo'lsa — alohida)"),
      num("Mas'ulga xabarlar va attachment fayllar"),
      num("Admin paneli (Jazzmin) va statistika API"),
      num("Docker tarmog'i: Postgres, Redis, Celery, host portlar"),

      // ===== 2 =====
      h1("2. Test bosqichlari (tartib)"),
      p("Oddiy skaner faqat konfiguratsiya, injection sirtini va infrastructure qatlamining tashqi qismini uradi. Eng ko'p real zarar odatda AuthN/AuthZ, business logic va IDOR matritsasida chiqadi.", { size: 21, color: GRAY }),
      spacer(80),
      makeTable([1400, 8490], [
        new TableRow({ children: [
          cell("Bosqich", 1400, { header: true }),
          cell("Tavsif", 8490, { header: true }),
        ]}),
        new TableRow({ children: [cell("0", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Kickoff / scope kelishuvi", 8490)] }),
        new TableRow({ children: [cell("1", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Recon va threat modeling", 8490)] }),
        new TableRow({ children: [cell("2", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Configuration va secrets review (SAST + config)", 8490)] }),
        new TableRow({ children: [cell("3", 1400, { bold: true, fill: YELLOW_BG }), cell("AuthN / AuthZ / session / OAuth  — YUQORI PRIORITET", 8490, { bold: true })] }),
        new TableRow({ children: [cell("4", 1400, { bold: true, fill: YELLOW_BG }), cell("Business logic (survey, messages, roles)  — YUQORI PRIORITET", 8490, { bold: true })] }),
        new TableRow({ children: [cell("5", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Input / injection / XSS / SSRF / upload", 8490)] }),
        new TableRow({ children: [cell("6", 1400, { bold: true, fill: YELLOW_BG }), cell("API va IDOR matritsa  — YUQORI PRIORITET", 8490, { bold: true })] }),
        new TableRow({ children: [cell("7", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Infrastructure (Docker, ports, headers, TLS)", 8490)] }),
        new TableRow({ children: [cell("8", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Abuse va resilience (rate limit, soft DoS)", 8490)] }),
        new TableRow({ children: [cell("9", 1400, { bold: true, fill: BLUE_LIGHT }), cell("Privacy / data minimization", 8490)] }),
        new TableRow({ children: [cell("10", 1400, { bold: true, fill: GREEN_BG }), cell("Report + retest", 8490)] }),
      ]),

      // ===== 3 =====
      h1("3. Threat model"),
      h2("3.1. Arxitektura sirtlari"),
      ...codeBlock([
        "[Talaba/Hodim brauzer]",
        "        |",
        "        v",
        "[Gunicorn web] -----> [Postgres]   (survey, student, messages)",
        "        |              [Redis]      (session + celery broker)",
        "        |              [Celery]     (QR, profile sync)",
        "        v",
        "[HEMIS / student.nspi.uz / hemis.nspi.uz]  (login, refresh, OAuth, profile)",
      ]),
      spacer(120),

      h2("3.2. Tahdid aktyorlari"),
      makeTable([2400, 7490], [
        new TableRow({ children: [
          cell("Aktyor", 2400, { header: true }),
          cell("Nima qilishi mumkin (faraz)", 7490, { header: true }),
        ]}),
        new TableRow({ children: [
          cell("Tashqi anonim", 2400, { bold: true, size: 17 }),
          cell("Login brute-force, OAuth abuse, ochiq API, port skan", 7490, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Oddiy talaba A", 2400, { bold: true, size: 17 }),
          cell("Talaba B ma'lumoti/xabari/javobini o'qish yoki o'zgartirish (IDOR)", 7490, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Hodim", 2400, { bold: true, size: 17 }),
          cell("Talaba funksiyalariga o'tish, ma'lumot oqishi, role confusion", 7490, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Ichki (compromised admin / leaked .env)", 2400, { bold: true, size: 17 }),
          cell("To'liq DB, secret, production buzilishi", 7490, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Supply-chain", 2400, { bold: true, size: 17 }),
          cell("Dependencies, base image, staticfiles, malicious package", 7490, { size: 17 }),
        ]}),
      ]),

      // ===== 4 =====
      h1("4. Konkret tekshiruvlar"),

      h2("4.A. Konfiguratsiya va maxfiy ma'lumotlar"),
      makeTable([2800, 2800, 4290], [
        new TableRow({ children: [
          cell("Tekshiruv", 2800, { header: true }),
          cell("Qanday", 2800, { header: true }),
          cell("Nima qidiraman", 4290, { header: true }),
        ]}),
        new TableRow({ children: [
          cell("Secrets leak", 2800, { size: 16 }),
          cell(".env.prod, git history, Docker layers, logs", 2800, { size: 16 }),
          cell("SECRET_KEY, HEMIS secret, DB password", 4290, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("DEBUG / ALLOWED_HOSTS", 2800, { size: 16 }),
          cell("Runtime header + error page", 2800, { size: 16 }),
          cell("Host header injection, stack trace", 4290, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Cookie flags", 2800, { size: 16 }),
          cell("DevTools + curl -I", 2800, { size: 16 }),
          cell("Secure, HttpOnly, SameSite, session age", 4290, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Security headers", 2800, { size: 16 }),
          cell("securityheaders / Burp", 2800, { size: 16 }),
          cell("HSTS, CSP, X-Frame-Options, nosniff", 4290, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("SSL redirect", 2800, { size: 16 }),
          cell("Production profil", 2800, { size: 16 }),
          cell("SECURE_SSL_REDIRECT, mixed content", 4290, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Default admin", 2800, { size: 16 }),
          cell("/admin/ admin/admin123", 2800, { size: 16 }),
          cell("Demo parol prodga chiqmaganmi", 4290, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Port exposure", 2800, { size: 16 }),
          cell("docker compose + netstat", 2800, { size: 16 }),
          cell("Postgres/Redis tashqariga ochiqmi", 4290, { size: 16 }),
        ]}),
      ]),
      spacer(100),
      callout("Shu loyihada alohida e'tibor", [
        "• Session Redis'da — Redis tarmoqda himoyasiz bo'lsa, session hijack mumkin.",
        "• Hostda 5432/6379/8000 boshqa loyihalar bilan aralashgan muhit — izolyatsiya zaifligi.",
        "• SECURE_HSTS_* va SSL default off — prod nginx orqasida bo'lmasa risk.",
      ], YELLOW_BG),

      h2("4.B. Autentifikatsiya va sessiya"),
      h3("B1. Login (username/password → HEMIS)"),
      bullet("Brute-force / credential stuffing (lokal rate limit bormi, faqat HEMIS tarafmi?)", "bullets2"),
      bullet("Timing farqi: \"user yo'q\" vs \"parol xato\"", "bullets2"),
      bullet("Error message leakage (log ID orqali ichki xato ochilishi)", "bullets2"),
      bullet("login_type=student|employee — role confusion: student credential bilan employee oqimiga o'tish mumkinmi?", "bullets2"),

      h3("B2. OAuth2 (/oauth/init/, /oauth/callback/)"),
      makeTable([4200, 5690], [
        new TableRow({ children: [
          cell("Test", 4200, { header: true }),
          cell("Kutiladigan himoya", 5690, { header: true }),
        ]}),
        new TableRow({ children: [
          cell("state yo'q / o'zgartirilgan", 4200, { size: 17 }),
          cell("Rad etiladi", 5690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("state qayta ishlatish (replay)", 4200, { size: 17 }),
          cell("Bir martalik bo'lishi kerak", 5690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("code boshqa client/redirect bilan", 4200, { size: 17 }),
          cell("Token olmasligi kerak", 5690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("redirect_uri manipulyatsiya", 4200, { size: 17 }),
          cell("Faqat ro'yxatdagi URI", 5690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Portal switch ?portal=student|employee", 4200, { size: 17 }),
          cell("Scope va token chalkashmasligi", 5690, { size: 17 }),
        ]}),
        new TableRow({ children: [
          cell("Authorization code interception (HTTP)", 4200, { size: 17 }),
          cell("Faqat HTTPS", 5690, { size: 17 }),
        ]}),
      ]),

      h3("B3. Token refresh"),
      bullet("Muddati o'tgan access + yaroqsiz refresh", "bullets3"),
      bullet("Refresh token o'g'irlansa — qancha vaqt yashaydi, revoke bormi?", "bullets3"),
      bullet("Refresh muvaffaqiyatsiz bo'lganda session to'liq flush bo'ladimi?", "bullets3"),

      h3("B4. Session"),
      bullet("Logout dan keyin session ID yaroqsizmi?", "bullets3"),
      bullet("Session fixation: login oldidan berilgan cookie login dan keyin o'zgaradimi?", "bullets3"),
      bullet("Concurrent session: bir user, 2 brauzer", "bullets3"),
      bullet("Cache backend: Redis flush / key guess", "bullets3"),

      h3("B5. Open Redirect — majburiy test (kodda sirt mavjud)"),
      p("Login dan keyin next parametri to'g'ridan-to'g'ri redirect() ga ketishi mumkin:", { size: 21 }),
      ...codeBlock([
        "?next=https://evil.example",
        "?next=//evil.example",
        "?next=/\\evil.example",
        "?next=javascript:...",
      ]),
      spacer(80),
      p("To'g'ri himoya: url_has_allowed_host_and_scheme() yoki faqat relative path allowlist.", {
        size: 20, bold: true, color: "991B1B",
      }),

      h2("4.C. Avtorizatsiya (IDOR / vertical privilege)"),
      p("Role × resurs matritsasi (har bir katakcha alohida test holati):", { size: 21 }),
      spacer(80),
      makeTable([2200, 1400, 1400, 1400, 1400, 2090], [
        new TableRow({ children: [
          cell("Resurs", 2200, { header: true, size: 15 }),
          cell("Talaba A", 1400, { header: true, size: 15 }),
          cell("Talaba B", 1400, { header: true, size: 15 }),
          cell("Hodim", 1400, { header: true, size: 15 }),
          cell("Staff", 1400, { header: true, size: 15 }),
          cell("Anonim", 2090, { header: true, size: 15 }),
        ]}),
        new TableRow({ children: [
          cell("O'z dashboard", 2200, { size: 15 }),
          cell("✓", 1400, { size: 15, fill: GREEN_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("—", 1400, { size: 15 }),
          cell("—", 1400, { size: 15 }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
        new TableRow({ children: [
          cell("Boshqa talaba profili", 2200, { size: 15 }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
        new TableRow({ children: [
          cell("Survey submit (yopiq)", 2200, { size: 15 }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
        new TableRow({ children: [
          cell("Message detail /messages/{pk}/", 2200, { size: 15 }),
          cell("faqat o'zi", 1400, { size: 14, fill: GREEN_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("✓?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
        new TableRow({ children: [
          cell("Attachment download", 2200, { size: 15 }),
          cell("faqat o'zi", 1400, { size: 14, fill: GREEN_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("?", 1400, { size: 15, fill: YELLOW_BG }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
        new TableRow({ children: [
          cell("Statistika API", 2200, { size: 15 }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✓", 1400, { size: 15, fill: GREEN_BG }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
        new TableRow({ children: [
          cell("Admin panel", 2200, { size: 15 }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✗", 1400, { size: 15, fill: RED_BG }),
          cell("✓", 1400, { size: 15, fill: GREEN_BG }),
          cell("✗", 2090, { size: 15, fill: RED_BG }),
        ]}),
      ]),
      spacer(100),
      p("Qanday tekshirish: Burp Intruder bilan pk ni 1…N yuritish; parallel ikki sessiya cookie; student_db_id session qiymatini tamper qilish.", { size: 20, italics: true, color: GRAY }),
      p("Role boundary: sessionda bir vaqtda student_db_id va employee_db_id bo'lsa nima bo'ladi? Token bitta, role chalkashuvi?", { size: 20, color: "991B1B" }),

      h2("4.D. Business logic — so'rovnoma"),
      p("Bu yerda skaner deyarli yordam bermaydi:", { size: 21 }),
      num("Muddat / is_open — UI yopiq, lekin POST /api/surveys/<id>/submit/ ochiqmi?"),
      num("Qayta ovoz — non-anonymous da DB constraint + permission ikkalasi ham turadimi?"),
      num("Anonymous survey — javobda student bog'lanishi saqlanadimi? (da'vo vs real storage)"),
      num("Savol/javob manipulyatsiyasi — boshqa survey'ning question_id / choice_id yuborish"),
      num("Majburiy savollarni o'tkazib yuborish, massiv/type confusion"),
      num("Race condition — bir vaqtda 2 parallel submit (double vote)"),
      num("Statistika — auth yo'q yoki zaif bo'lsa, qatnashuvchi soni va javoblar oqishi"),

      h2("4.E. Xabar tizimi va fayl yuklash"),
      makeTable([2800, 7090], [
        new TableRow({ children: [
          cell("Hujum", 2800, { header: true }),
          cell("Test", 7090, { header: true }),
        ]}),
        new TableRow({ children: [
          cell("Path traversal filename", 2800, { size: 16 }),
          cell("../../etc/passwd.pdf, ..\\..\\windows\\win.ini", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("MIME spoof", 2800, { size: 16 }),
          cell(".png lekin PHP/HTML/SVG+JS kontent", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Double extension", 2800, { size: 16 }),
          cell("evil.php.png, report.pdf.exe", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Oversized file", 2800, { size: 16 }),
          cell("DoS / disk to'ldirish", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Polyglot PDF/JS", 2800, { size: 16 }),
          cell("Admin yoki foydalanuvchi ochganda XSS", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Content-Disposition", 2800, { size: 16 }),
          cell("stored XSS via filename", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Unauthorized download", 2800, { size: 16 }),
          cell("To'g'ridan-to'g'ri /media/messages_attachments/... URL", 7090, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("QR / Celery abuse", 2800, { size: 16 }),
          cell("Mingta message orqali queue flood", 7090, { size: 16 }),
        ]}),
      ]),

      h2("4.F. Injection va XSS"),
      makeTable([1800, 3500, 4590], [
        new TableRow({ children: [
          cell("Tur", 1800, { header: true }),
          cell("Qayerda", 3500, { header: true }),
          cell("Usul", 4590, { header: true }),
        ]}),
        new TableRow({ children: [
          cell("SQLi", 1800, { size: 16 }),
          cell("Filter/search/API param", 3500, { size: 16 }),
          cell("Manual + sqlmap (faqat test env)", 4590, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("XSS stored", 1800, { size: 16 }),
          cell("Survey title/desc, message, reply, answer", 3500, { size: 16 }),
          cell("Payload set", 4590, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("XSS reflected", 1800, { size: 16 }),
          cell("next, error, OAuth error_description", 3500, { size: 16 }),
          cell("Brauzer + Burp", 4590, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("mark_safe", 1800, { size: 16 }),
          cell("Admin javob, survey_data_json", 3500, { size: 16 }),
          cell("HTML/JS breakout", 4590, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("SSTI", 1800, { size: 16 }),
          cell("Custom template string", 3500, { size: 16 }),
          cell("{{7*7}}", 4590, { size: 16 }),
        ]}),
        new TableRow({ children: [
          cell("Command inj.", 1800, { size: 16 }),
          cell("Upload + Celery worker", 3500, { size: 16 }),
          cell("Agar filename shell'ga ketsa", 4590, { size: 16 }),
        ]}),
      ]),

      h2("4.G. API xavfsizligi (DRF + custom JSON)"),
      bullet("JWT/Bearer vs session cookie chalkashuvi", "bullets4"),
      bullet("TokenRefreshView abuse", "bullets4"),
      bullet("CSRF: cookie session + JSON API — SameSite va CSRF exception holatlari", "bullets4"),
      bullet("Mass assignment: serializer'da keraksiz maydonlar", "bullets4"),
      bullet("Excessive data exposure: list endpoint'da ichki maydonlar", "bullets4"),
      bullet("Method tampering: GET o'rniga PUT/DELETE", "bullets4"),
      bullet("Rate limiting yo'qligi (login, submit, message create)", "bullets4"),

      h2("4.H. Infrastructure / Docker / supply chain"),
      bullet("Image: non-root user bormi? (Dockerfile da root ishlashi mumkin)", "bullets4"),
      bullet("volumes: .:/app prod'da — kod yozish / secret mount", "bullets4"),
      bullet("Network: web, db, redis bitta default network — lateral movement", "bullets4"),
      bullet("Postgres: kuchli parol, tashqi bind yo'q", "bullets4"),
      bullet("Redis: requirepass, faqat ichki tarmoq", "bullets4"),
      bullet("Dependency scan: pip-audit / safety / OSV", "bullets4"),
      bullet("Trivy/Grype image scan", "bullets4"),
      bullet("Log injection va PII/token logda saqlanmasligi", "bullets4"),

      h2("4.I. Maxfiylik (privacy)"),
      bullet("Qaysi maydonlar DB'da saqlanadi vs HEMIS'dan har safar olinadi", "bullets5"),
      bullet("Anonim so'rovnoma haqiqatanmi?", "bullets5"),
      bullet("Backup, media, logs saqlash muddati", "bullets5"),
      bullet("Admin export (CSV) kimga ochiq", "bullets5"),
      bullet("O'chirish huquqi (talaba o'chirilsa javoblar nima bo'ladi)", "bullets5"),

      // ===== 5 =====
      h1("5. Amaliy test ssenariylari (Playbook)"),

      h3("Ssenariy 1 — Talaba A boshqa talabani o'qiydi"),
      bullet("A va B login qiladi"),
      bullet("A o'z message pk=10 ni ochadi"),
      bullet("pk ni B ning messageiga almashtiradi"),
      bullet("Attachment URL ni to'g'ridan-to'g'ri so'raydi"),
      p("Kutiladi: 403/404, hech qanday body leakage", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 2 — Login open redirect → phishing"),
      bullet("/login/?next=https://evil.tld/fake-hemis"),
      bullet("Muvaffaqiyatli login"),
      p("Kutiladi: faqat same-origin relative path", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 3 — Yopiq so'rovnomaga API orqali javob"),
      bullet("UI da survey yopiq"),
      bullet("Burp da eski submit request'ni replay"),
      p("Kutiladi: 403 + DB ga yozilmasin", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 4 — Race: double submit"),
      bullet("20 parallel request bir xil survey"),
      p("Kutiladi: 1 ta SurveyResponse (unique constraint)", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 5 — OAuth state bypass"),
      bullet("state ni boshqa sessiya bilan almashtirish"),
      p("Kutiladi: fail closed", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 6 — Statistika API anonim"),
      bullet("Cookie'siz GET /api/surveys/1/statistics/"),
      p("Kutiladi: 401/403", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 7 — Malicious upload"),
      bullet("SVG/HTML/PHP polyglot attachment"),
      bullet("Boshqa user yoki admin ochadi"),
      p("Kutiladi: content-type force, no execute, CSP", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 8 — Session after logout / Redis"),
      bullet("Logout"),
      bullet("Eski session cookie replay"),
      p("Kutiladi: login page", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 9 — Horizontal admin via stats page"),
      bullet("Staff bo'lmagan user /surveys/1/statistics/"),
      p("Kutiladi: rad etish", { size: 20, bold: true, color: "166534" }),

      h3("Ssenariy 10 — Config dump"),
      bullet("Noto'g'ri Host header"),
      bullet("500 xato sahifasi"),
      p("Kutiladi: DEBUG=False, no settings leak", { size: 20, bold: true, color: "166534" }),

      // ===== 6 =====
      h1("6. Asboblar"),
      makeTable([2800, 7090], [
        new TableRow({ children: [
          cell("Qatlam", 2800, { header: true }),
          cell("Asboblar", 7090, { header: true }),
        ]}),
        new TableRow({ children: [cell("Proxy / manual", 2800, { size: 17 }), cell("Burp Suite Pro (yoki OWASP ZAP)", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("Browser", 2800, { size: 17 }), cell("2 profil + DevTools", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("Auth/session / IDOR", 2800, { size: 17 }), cell("Burp Autorize", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("SAST", 2800, { size: 17 }), cell("Bandit, Semgrep (Django rules)", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("Deps", 2800, { size: 17 }), cell("pip-audit, Trivy", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("DAST", 2800, { size: 17 }), cell("ZAP baseline/full (staging)", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("API", 2800, { size: 17 }), cell("Postman/Insomnia + ffuf", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("Secrets", 2800, { size: 17 }), cell("gitleaks, trufflehog", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("Headers/TLS", 2800, { size: 17 }), cell("testssl.sh, Mozilla Observatory", 7090, { size: 17 })] }),
        new TableRow({ children: [cell("Load/abuse", 2800, { size: 17 }), cell("k6 / Locust (yumshoq limitlar bilan)", 7090, { size: 17 })] }),
      ]),
      spacer(100),
      p("Avtomatlashtirish foydali, lekin biznes mantiq va IDOR doim qo'lda tekshiriladi.", { size: 20, italics: true, color: GRAY }),

      // ===== 7 =====
      h1("7. Natija formati (hisobot)"),
      p("Har bir topilma quyidagi maydonlarga ega bo'lishi kerak:", { size: 21 }),
      num("Title (masalan: Open Redirect in login next parameter)"),
      num("Severity (CVSS 3.1 + biznes: PII? account takeover?)"),
      num("Affected component (URL, funksiya, fayl)"),
      num("Steps to reproduce (screenshot / request)"),
      num("Impact"),
      num("Remediation (kod darajasida aniq)"),
      num("Retest status"),
      spacer(100),
      h3("Prioritetlash (shu stack uchun odatiy)"),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Auth bypass / session / OAuth", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "IDOR (messages, attachments, student data)", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Open redirect + XSS (phishing zanjiri)", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "File upload RCE/XSS", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Broken access on statistics/admin", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Misconfig (Redis/Postgres exposure, weak secrets)", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "priority", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Missing rate limit, verbose errors", font: "Arial", size: 21, color: DARK })],
      }),

      // ===== 8 =====
      h1("8. Birinchi navbatdagi qizil bayroqlar"),
      p("Kod va arxitekturaga asoslangan dastlabki e'tibor ro'yxati (hali exploit isboti emas — test rejasining bosh nuqtalari):", { size: 21, color: GRAY }),
      spacer(80),
      ...[
        "next / login_next_url → redirect() — open redirect",
        "Message/attachment object-level auth — har bir view'da egasi tekshiruvi",
        "Media URL'lar ochiqligi",
        "Survey submit server-side validation (UI emas)",
        "Anonymous survey haqiqiy anonimligi",
        "OAuth state bog'lanishi va portal chalkashuvi",
        "Statistika API auth regression",
        "Admin default creds + DEBUG/secrets prod",
        "Redis/session va Docker port exposure",
        "mark_safe + foydalanuvchi kontenti",
        "Rate limiting login/submit/message da",
        "Celery task flood (QR generate)",
      ].map(t => new Paragraph({
        numbering: { reference: "redflags", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: t, font: "Arial", size: 21, color: DARK })],
      })),

      // ===== 9 =====
      h1("9. O'xshash loyihalar uchun minimal chuqur test paketi"),
      p("Har qanday universitet/davlat Django ilovasi uchun kamida:", { size: 21 }),
      ...[
        "Threat model (1 kun)",
        "Config + secrets + dependency scan",
        "Full auth matrix (roles × endpoints)",
        "IDOR suite (barcha pk/uuid resurslar)",
        "Business logic abuse (muddat, limit, double-submit, race)",
        "Upload + media access",
        "OAuth/OIDC checklist (agar tashqi IdP bo'lsa)",
        "Headers/TLS/Docker hardening",
        "Privacy review (qaysi PII qayerda)",
        "Written report + retest",
      ].map(t => new Paragraph({
        numbering: { reference: "minimal", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: t, font: "Arial", size: 21, color: DARK })],
      })),
      spacer(100),
      callout("Vaqt bahosi", [
        "Kichik loyiha: 3–5 kun",
        "O'rta loyiha: 1–2 hafta",
        "Prod + mobile/API qo'shimcha: uzayadi",
      ], BLUE_LIGHT),

      // ===== 10 =====
      h1("10. Xulosa va keyingi bosqich"),
      p("Chuqur test = skaner ≠ pen test.", { size: 22, bold: true }),
      p("Shu tipdagi tizimda eng xavfli zanjir odatda:", { size: 21 }),
      spacer(80),
      callout("Tipik hujum zanjiri", [
        "1) Open redirect / XSS → session o'g'irlash yoki phishing",
        "2) yoki IDOR → boshqa talaba xabari/javobi",
        "3) yoki zaif session/Redis/secret → to'liq hisob egallash",
      ], RED_BG),
      spacer(160),
      h2("Keyingi bosqich (reja)"),
      new Paragraph({
        numbering: { reference: "nextsteps", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Endpoint matritsa va checklist asosida staging audit (non-destructive)", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "nextsteps", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Topilmalarni CVSS + fix prioritet bilan hisobotga yozish", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "nextsteps", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Top 10 fix (open redirect, media auth, rate limit, Redis bind…)", font: "Arial", size: 21, color: DARK })],
      }),
      new Paragraph({
        numbering: { reference: "nextsteps", level: 0 },
        spacing: { after: 80 },
        children: [new TextRun({ text: "Retest va yopilgan/yo'q topilmalar holati", font: "Arial", size: 21, color: DARK })],
      }),
      spacer(300),
      p("— Hujjat oxiri —", { align: AlignmentType.CENTER, size: 18, color: GRAY, italics: true }),
      p("Survey NSPI UZ · Cyber Test Plan v1.0 · 2026-07-31", { align: AlignmentType.CENTER, size: 16, color: "94A3B8" }),
    ],
  }],
});

const outPath = path.join(__dirname, "Survey_NSPI_Cybersecurity_Test_Plan_v1.docx");
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("OK:", outPath);
}).catch(err => {
  console.error(err);
  process.exit(1);
});
