#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json, urllib.request, urllib.parse, datetime, calendar, os, hashlib, re, math
from xml.sax.saxutils import escape

PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://tool.beaver1376.top')
SHARE_DIR = os.environ.get('SHARE_DIR', '/opt/vps_jsq/share')
MAX_REQUEST_BYTES = 16 * 1024
MAX_SHARE_FILES = 2000
MAX_RATE = 1_000_000
MAX_RENEW_MONEY = 1_000_000_000

CURRENCIES = ['CNY','USD','GBP','EUR','JPY','KRW','HKD','TWD','CAD','SGD','AUD']
CYCLE_MONTHS = {
    'monthly': 1,
    'quarterly': 3,
    'semiannually': 6,
    'annually': 12,
    'biennially': 24,
    'triennially': 36,
    'quinquennially': 60,
}
CYCLE_CN = {
    'monthly': '月', 'quarterly': '季', 'semiannually': '半年', 'annually': '年',
    'biennially': '两年', 'triennially': '三年', 'quinquennially': '五年'
}
_cache = {'ts': None, 'data': None}

def add_months(d, months):
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return datetime.date(y, m, day)

def get_rates():
    now = datetime.datetime.utcnow()
    if _cache['data'] and _cache['ts'] and (now - _cache['ts']).total_seconds() < 6*3600:
        return _cache['data']
    try:
        with urllib.request.urlopen('https://api.exchangerate-api.com/v4/latest/USD', timeout=10) as r:
            raw = json.load(r)
        rates = raw.get('rates', {})
        cny_per_usd = float(rates['CNY'])
        out = []
        for cur in CURRENCIES:
            if cur == 'CNY':
                val = 1.0
            elif cur == 'USD':
                val = cny_per_usd
            else:
                val = cny_per_usd / float(rates[cur])
            out.append({'currency_code': cur, 'rate': f'{val:.3f}'})
        data = {'status':'success','data':{'last_update_date': datetime.date.today().strftime('%Y/%m/%d'), 'rates': out}}
        _cache.update(ts=now, data=data)
        return data
    except Exception as e:
        # Fallback values so the page still works if upstream is temporarily unreachable.
        fallback = {'CNY':1.0,'USD':7.2,'GBP':9.1,'EUR':7.8,'JPY':0.05,'KRW':0.0052,'HKD':0.92,'TWD':0.22,'CAD':5.3,'SGD':5.6,'AUD':4.7}
        return {'status':'success','data':{'last_update_date': datetime.date.today().strftime('%Y/%m/%d'), 'rates':[{'currency_code':k,'rate':f'{v:.3f}'} for k,v in fallback.items()]}}

def make_share_svg(data):
    """White share card: larger type, blue residual value, rows spaced so text never hits lines."""
    rows = [
        ('交易日期', data['trade_date'], 'normal'),
        ('外币汇率', data['exchange_rate'], 'normal'),
        ('续费价格', data['renewal'], 'normal'),
        ('剩余天数', f"{data['remain_days']} 天", 'success'),
        ('到期时间', data['expiry_date'], 'normal'),
        ('剩余价值', f"{data['remain_value']} 元", 'accent'),
        ('周期价格', f"{data['total_value']} 元", 'normal'),
    ]
    if data.get('custom_exchange_rate') and data.get('custom_exchange_rate') != data.get('exchange_rate'):
        rows.append(('自定义汇率', data['custom_exchange_rate'], 'normal'))
        rows.append(('自定义估值', f"{data['custom_remain_value']} 元", 'accent'))

    width = 720
    card_x = 24
    card_y = 20
    card_w = width - card_x * 2
    # title
    title_y = card_y + 46
    rule_y = title_y + 20
    # row geometry: baseline to baseline 42px; separator sits mid-gap (~21px above next baseline)
    # 20–24px text stays clear of lines (glyph top ~ baseline-0.8*size)
    row_h = 42
    first_row_y = rule_y + 36
    table_x = card_x + 30
    table_w = card_w - 60

    row_svg = []
    for idx, (label, value, kind) in enumerate(rows):
        y = first_row_y + idx * row_h
        if idx > 0:
            sep_y = y - row_h // 2
            row_svg.append(
                f'<line x1="{table_x}" y1="{sep_y}" x2="{table_x + table_w}" y2="{sep_y}" class="separator"/>'
            )
        if kind == 'accent':
            cls = 'value accent'
        elif kind == 'success':
            cls = 'value success'
        else:
            cls = 'value'
        row_svg.append(f'<text x="{table_x}" y="{y}" class="label">{escape(label)}</text>')
        row_svg.append(f'<text x="{table_x + table_w}" y="{y}" class="{cls}" text-anchor="end">{escape(value)}</text>')

    last_y = first_row_y + (len(rows) - 1) * row_h
    footer_y = last_y + 34
    card_h = footer_y + 20 - card_y
    height = card_y + card_h + 20

    public_host = urllib.parse.urlparse(PUBLIC_BASE_URL).netloc or 'VPS 剩余价值计算器'
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="22" fill="#ffffff" stroke="#D2D2D7" stroke-width="1"/>

  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif; }}
    .title {{ font-size: 32px; font-weight: 780; fill: #1D1D1F; letter-spacing: -0.6px; }}
    .label {{ font-size: 20px; font-weight: 600; fill: rgba(60,60,67,.70); }}
    .value {{ font-size: 20px; font-weight: 720; fill: #1D1D1F; }}
    .accent {{ fill: #007AFF; font-size: 22px; font-weight: 800; }}
    .success {{ fill: #34C759; font-weight: 750; }}
    .separator {{ stroke: rgba(60,60,67,.14); stroke-width: 1; }}
    .foot {{ font-size: 13px; font-weight: 520; fill: rgba(60,60,67,.42); }}
  </style>

  <text x="{width/2}" y="{title_y}" class="title" text-anchor="middle">VPS 剩余价值计算器</text>
  <line x1="{table_x}" y1="{rule_y}" x2="{table_x + table_w}" y2="{rule_y}" class="separator"/>

  {''.join(row_svg)}

  <text x="{width/2}" y="{footer_y}" class="foot" text-anchor="middle">{escape(public_host)}</text>
</svg>"""
    return svg


def make_share_pic(data):
    """Write the SVG to disk and return a public HTTPS URL suitable for Markdown."""
    svg = make_share_svg(data)
    os.makedirs(SHARE_DIR, exist_ok=True)
    digest_src = json.dumps(data, ensure_ascii=False, sort_keys=True) + svg
    name = hashlib.sha256(digest_src.encode('utf-8')).hexdigest()[:20] + '.svg'
    path = os.path.join(SHARE_DIR, name)
    if not os.path.exists(path):
        files = sorted(
            (entry for entry in os.scandir(SHARE_DIR)
             if entry.is_file() and re.fullmatch(r'[a-f0-9]{20}\.svg', entry.name)),
            key=lambda entry: entry.stat().st_mtime,
        )
        for entry in files[:max(0, len(files) - MAX_SHARE_FILES + 1)]:
            try:
                os.unlink(entry.path)
            except FileNotFoundError:
                pass
        temp_path = path + f'.tmp.{os.getpid()}.{hashlib.sha256(os.urandom(16)).hexdigest()[:8]}'
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(svg)
        os.replace(temp_path, path)
    return PUBLIC_BASE_URL.rstrip('/') + '/share/' + name


def calc(body):
    if not isinstance(body, dict):
        raise ValueError('请求内容必须是 JSON 对象')

    required = ('exchange_rate', 'renew_money', 'cycle', 'expiry_date', 'trade_date')
    if any(body.get(key) in (None, '') for key in required):
        raise ValueError('汇率、续费金额、付款周期和日期不能为空')

    reference_rate = float(body['exchange_rate'])
    custom_rate = float(body.get('custom_exchange_rate') or reference_rate)
    renew = float(body['renew_money'])
    cycle = body['cycle']
    if not math.isfinite(reference_rate) or reference_rate <= 0:
        raise ValueError('参考汇率必须是大于 0 的有限数字')
    if reference_rate > MAX_RATE:
        raise ValueError('参考汇率超过允许范围')
    if not math.isfinite(custom_rate) or custom_rate <= 0:
        raise ValueError('外币汇率必须是大于 0 的有限数字')
    if custom_rate > MAX_RATE:
        raise ValueError('外币汇率超过允许范围')
    if not math.isfinite(renew) or renew < 0:
        raise ValueError('续费金额必须是大于或等于 0 的有限数字')
    if renew > MAX_RENEW_MONEY:
        raise ValueError('续费金额超过允许范围')
    if cycle not in CYCLE_MONTHS:
        raise ValueError('不支持的付款周期')

    expiry_text = body.get('expiry_date')
    trade_text = body.get('trade_date')
    if not isinstance(expiry_text, str) or not isinstance(trade_text, str):
        raise ValueError('到期时间和交易日期不能为空')
    try:
        expiry = datetime.date.fromisoformat(expiry_text)
        trade = datetime.date.fromisoformat(trade_text)
    except ValueError as exc:
        raise ValueError('日期格式必须为 YYYY-MM-DD') from exc
    months = CYCLE_MONTHS.get(cycle, 12)
    start = add_months(expiry, -months)
    total_days = max((expiry - start).days, 1)
    remain_days = max((expiry - trade).days, 0)
    total_value = renew * reference_rate
    custom_total_value = renew * custom_rate
    remain_value = total_value * remain_days / total_days
    custom_remain_value = custom_total_value * remain_days / total_days
    # renewal 按所选付款周期显示，不做年化折算（renew 即该周期金额）
    per_cycle_value = renew * reference_rate
    if not all(math.isfinite(value) for value in (
        total_value, custom_total_value, remain_value,
        custom_remain_value, per_cycle_value,
    )):
        raise ValueError('计算结果超过允许范围')
    cycle_unit = CYCLE_CN.get(cycle, '年')
    data = {
        'trade_date': trade.isoformat(),
        'exchange_rate': f'{reference_rate:.3f}',
        'custom_exchange_rate': f'{custom_rate:.3f}',
        'renewal': f'{per_cycle_value:.2f} 人民币/{cycle_unit}',
        'remain_days': str(remain_days),
        'expiry_date': expiry.isoformat(),
        'remain_value': f'{remain_value:.3f}',
        'custom_remain_value': f'{custom_remain_value:.3f}',
        'total_value': f'{total_value:.3f}',
    }
    data['share_pic'] = make_share_pic(data)
    return {'status': 'success', 'data': data}

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b=json.dumps(obj, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Content-Length',str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self._send(200, {'ok': True})
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/healthz':
            self._send(200, {'ok': True})
        elif path == '/api/vps/rates':
            self._send(200, get_rates())
        elif path.startswith('/share/'):
            name = os.path.basename(urllib.parse.urlparse(self.path).path)
            if not re.fullmatch(r'[a-f0-9]{20}\.svg', name or ''):
                self.send_error(404)
                return
            path = os.path.join(SHARE_DIR, name)
            if not os.path.isfile(path):
                self.send_error(404)
                return
            try:
                with open(path, 'rb') as f:
                    b = f.read()
            except FileNotFoundError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml; charset=utf-8')
            self.send_header('Cache-Control', 'public, max-age=2592000, immutable')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        else:
            self._send(404, {'status':'error','message':'not found'})
    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/api/vps/jsq':
            try:
                if self.headers.get_content_type() != 'application/json':
                    self._send(415, {'status':'error','message':'请求格式必须是 application/json'})
                    return
                n=int(self.headers.get('Content-Length','0'))
                if n <= 0 or n > MAX_REQUEST_BYTES:
                    self._send(413, {'status':'error','message':'请求内容过大或为空'})
                    return
                body=json.loads(self.rfile.read(n) or b'{}')
                self._send(200, calc(body))
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                self._send(400, {'status':'error','message':str(e)})
            except Exception:
                self._send(500, {'status':'error','message':'服务器处理请求失败'})
        else: self._send(404, {'status':'error','message':'not found'})
    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt%args), flush=True)

if __name__ == '__main__':
    port=int(os.environ.get('PORT','18089'))
    host=os.environ.get('HOST','127.0.0.1')
    ThreadingHTTPServer((host, port), Handler).serve_forever()
