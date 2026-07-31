# Cyber Test — Survey NSPI UZ

## Hujjatlar

| Fayl | Tavsif |
|------|--------|
| `Survey_NSPI_Cybersecurity_Test_Plan_v1.docx` | Chuqurlashtirilgan kiberxavfsizlik test rejasi va playbook (v1.0) |
| `create_security_plan.js` | Word hujjatini qayta generatsiya qilish skripti |

## Qayta yaratish

```bash
cd cyber_test
npm install
node create_security_plan.js
```

## Keyingi bosqich

1. Stagingda non-destructive audit
2. Topilmalar hisoboti (CVSS + fix prioritet)
3. Top-10 tuzatish va retest
