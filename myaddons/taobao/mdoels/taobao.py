import top.api

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
url = 'eco.taobao.com'
port = 80
appkey = 30271274

secret = 'b6a5af9fe46b82951e6ce17423bd8ec8'

req = top.api.TradesSoldGetRequest(url, port)
req.set_app_info(top.appinfo(appkey, secret))
req.fields = "tid,start_created,buyer_nick,ext_type"
req.start_created = "2020-06-10 00:00:00"
req.end_created = "2020-06-12 23:59:59"
req.type = 'fixed'
req.status = "TRADE_FINISHED"
req.page_no = 1
req.page_size = 100
sessionkey = '61001170c1e2e5645d0be45081b09b20c87c630cb10cd902208164085326'
resw = req.getResponse(sessionkey)
print(resw, 'eee')