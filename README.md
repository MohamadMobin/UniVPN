# UniVPN
A secure multi-layer network bridge using FRP, Xray, and Cloudflare WARP.

# 🌉 UniVPN: University Network Bypass & Remote Access

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![FRP](https://img.shields.io/badge/FRP-v0.56.0-brightgreen.svg)
![Xray](https://img.shields.io/badge/Xray-Core-purple.svg)
![WARP](https://img.shields.io/badge/WARP-Cloudflare-orange.svg)

این مخزن شامل مستندات و راهنمای جامع برای پیاده‌سازی یک معماری شبکه دوگانه است. هدف این پروژه، غلبه بر محدودیت‌های شبکه‌های داخلی (NAT/Firewall/Intranet) و مسیریابی ترافیک به سمت اینترنت آزاد از راه دور است. 

با این ساختار، شما می‌توانید اینترنت پرسرعت یک شبکه محلی (مانند دانشگاه یا سازمان) را از طریق یک تونل امن به یک سرور واسط داخلی منتقل کرده و از خانه (تنها با داشتن دسترسی به اینترانت) به آن متصل شوید.

> ⚠️ **سلب مسئولیت:** این مستندات صرفاً با اهداف آموزشی، تحقیقاتی و توسعه مهندسی شبکه تدوین شده است. مسئولیت استفاده از این راهکار و تطابق آن با قوانین IT سازمان/دانشگاه بر عهده کاربر است.

---

## 📐 معماری سیستم (System Architecture)

این سیستم از سه گره (Node) اصلی تشکیل شده است:
1. **Bridge Node (سرور ابری داخلی):** یک سرور مجازی (VPS) دارای IP عمومی در دیتاسنترهای داخلی. به عنوان پل ارتباطی عمل می‌کند.
2. **Local Node (رزبری‌پای/لپ‌تاپ در شبکه داخلی):** سرور مستقر در شبکه دانشگاه که به اینترنت جهانی دسترسی دارد اما فاقد IP عمومی است. این گره میزبان پنل `3x-ui`، هسته `Xray` و کلاینت `FRP` است.
3. **Outbound Proxy (ترافیک خروجی):** سرویس `Cloudflare WARP` روی گره محلی نصب می‌شود تا ترافیک را از تحریم‌های بین‌المللی (IP Ban) عبور دهد.

**جریان ترافیک:**
`Client (Home)` $\rightarrow$ `Intranet` $\rightarrow$ `Cloud VPS (Port $7001$)` $\rightarrow$ `[FRP Tunnel]` $\rightarrow$ `Local Node (Port $8443$)` $\rightarrow$ `Xray Core (VLESS-Reality)` $\rightarrow$ `WARP (Port $40000$)` $\rightarrow$ `Global Internet`

---

## ☁️ فاز ۱: راه‌اندازی سرور ابری (Bridge Node)
**پیش‌نیاز:** یک سرور مجازی لینوکس (Ubuntu $22.04+$) در ایران.

بلوک کد زیر را کپی کرده و در ترمینال سرور ابری اجرا کنید (مقدار `YOUR_SECURE_TOKEN` را با یک رمز عبور قوی جایگزین کنید):
```bash
# ۱. نصب پیش‌نیازها و FRP
sudo apt update && sudo apt install -y wget curl ufw
wget https://github.com/fatedier/frp/releases/download/v0.56.0/frp_0.56.0_linux_amd64.tar.gz
tar -xvf frp_0.56.0_linux_amd64.tar.gz
sudo cp frp_0.56.0_linux_amd64/frps /usr/local/bin/
sudo mkdir -p /etc/frp

# ۲. ایجاد فایل کانفیگ FRPS
sudo tee /etc/frp/frps.toml > /dev/null <<EOF
bindPort = 7000
auth.method = "token"
auth.token = "YOUR_SECURE_TOKEN"
EOF

# ۳. ایجاد سرویس خودکار و باز کردن پورت‌ها
sudo tee /etc/systemd/system/frps.service > /dev/null <<EOF
[Unit]
Description=FRP Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now frps
sudo ufw allow 7000/tcp
sudo ufw allow 7001/tcp

---

## 🏢 فاز ۲: راه‌اندازی سرور محلی (Local Node در دانشگاه)
**پیش‌نیاز:** یک مینی‌کامپیوتر (مثل Raspberry Pi) یا سیستم لینوکسی متصل به شبکه دانشگاه. *(در صورت وجود Captive Portal، ابتدا با یک اسکریپت پایتون/Curl لاگین خودکار را تنظیم کنید).*

**۱. نصب پنل 3x-ui:**
bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
> 💡 *پس از نصب، وارد پنل وب شوید و یک کانفیگ **VLESS-Reality** روی پورت `$8443$` بسازید (نکات مربوط به SNI در فاز ۴ مطالعه شود).*

**۲. نصب FRPC (کلاینت تونل) و WARP:**
*(کد زیر برای معماری ARM64 مثل رزبری‌پای است. برای سیستم‌های معمولی `arm64` را به `amd64` تغییر دهید. مقادیر IP سرور ابری و TOKEN را جایگزین کنید).*

bash
# دانلود و نصب FRP
wget https://github.com/fatedier/frp/releases/download/v0.56.0/frp_0.56.0_linux_arm64.tar.gz
tar -xvf frp_0.56.0_linux_arm64.tar.gz
sudo cp frp_0.56.0_linux_arm64/frpc /usr/local/bin/
sudo mkdir -p /etc/frp

# ایجاد کانفیگ FRPC
sudo tee /etc/frp/frpc.toml > /dev/null <<EOF
serverAddr = "IP_سرور_ابری_شما"
serverPort = 7000
auth.method = "token"
auth.token = "YOUR_SECURE_TOKEN"

[[proxies]]
name = "xray-tunnel"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8443
remotePort = 7001
EOF

# ایجاد سرویس FRPC
sudo tee /etc/systemd/system/frpc.service > /dev/null <<EOF
[Unit]
Description=FRP Client
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/frpc -c /etc/frp/frpc.toml
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now frpc

# نصب و تنظیم WARP (دور زدن تحریم‌ها)
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
sudo apt update && sudo apt install cloudflare-warp -y

warp-cli registration new
warp-cli mode proxy
warp-cli port 40000
warp-cli connect
> 💡 *در نهایت، در پنل `3x-ui` یک Outbound از نوع SOCKS با آدرس `127.0.0.1` و پورت `$40000$` ایجاد کرده و روتینگ را به آن هدایت کنید.*

---

## 📱 فاز ۳: اتصال کلاینت‌ها (از خانه)
1. نرم‌افزار کلاینت (مانند `v2rayNG` برای اندروید، `v2rayN` برای ویندوز یا `Vultr/Shadowrocket` برای iOS) را نصب کنید.
2. کانفیگ VLESS ایجاد شده در فاز ۲ را کپی و در برنامه Import کنید.
3. **گام حیاتی:** کانفیگ را ویرایش (Edit) کرده و تغییرات زیر را اعمال کنید:
   - **Address:** آی‌پی سرور ابری (VPS داخلی)
   - **Port:** `$7001$` (پورتی که در FRPC فوروارد کردید)
4. اتصال را برقرار کنید.

---

## 🕵️‍♂️ فاز ۴: نکات فوق‌امنیتی، تست و مخفی‌ماندن (DPI Evasion)

برای جلوگیری از مسدود شدن یا شناسایی توسط ادمین‌های شبکه و سیستم‌های مانیتورینگ، رعایت موارد زیر الزامی است:

### ۱. انتخاب SNI و Dest بومی (بسیار مهم)
در تنظیمات Reality پنل `3x-ui`، از دامنه‌های خارجی استفاده **نکنید**. 
از آنجا که ترافیک شما بستر داخلی دارد، سیستم مانیتورینگ باید تصور کند شما در حال بازدید از یک سایت داخلی هستید.
* **SNI / Dest:** یک سایت **داخلی پربازدید، سریع و دارای گواهی TLS 1.3/X25519** انتخاب کنید (مانند سایت‌های فروشگاهی، بانک‌ها یا سرویس‌های VOD داخلی).
* **TEST_URL:** حتماً تست کنید که سایت انتخابی در شبکه داخلی بدون مشکل باز شود.

### ۲. مانیتورینگ حجم و رفتار کاربر (Traffic Analysis)
فایروال‌ها تنها به پورت‌ها نگاه نمی‌کنند؛ بلکه رفتار شما را تحلیل می‌کنند.
* **الگوی ترافیک تونل:** اگر روزانه `$50$` گیگابایت ترافیک رمزنگاری‌شده بین یک سیستم در آزمایشگاه و یک IP ناشناس رد و بدل شود، زنگ خطر ادمین شبکه به صدا در می‌آید.
* **راه‌حل:** ترافیک خود را مدیریت کنید. از دانلودهای حجیم و بی‌رویه بپرهیزید یا محدودیت سرعت (Rate Limit) در Xray اعمال کنید تا رفتار شما شبیه یک کاربر عادی به نظر برسد.

### ۳. تست‌های سلامت سیستم (Health Checks)
برای اطمینان از عملکرد صحیح در هر مرحله:
* **تست تونل:** دستور `curl http://IP_سرور_ابری:7001` باید خروجی `Bad Request` (مربوط به Xray) بدهد که نشان‌دهنده باز بودن تونل تا رزبری‌پای است.
* **تست WARP:** دستور `curl -x socks5h://127.0.0.1:40000 ipinfo.io` در رزبری‌پای باید IP کلودفلر را برگرداند.

---

## 🤝 مشارکت (Contributing)
این پروژه نیازمند هم‌فکری است. اگر در زمینه‌های زیر تخصص دارید، لطفاً Pull Request ارسال کنید:
* بهبود اسکریپت‌های لاگین خودکار برای پورتال‌های مختلف (Captive Portals).
* راهکارهای پیشرفته برای جلوگیری از تشخیص تونل توسط فایروال‌های لایه ۷.
* اتوماسیون کامل نصب با یک فایل `bash` یکپارچه.
