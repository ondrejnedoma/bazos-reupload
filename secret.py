import requests
from pyquery import PyQuery as pq
import yaml

with open('./config.yaml', 'r') as config_file:
  config = yaml.load(config_file, Loader=yaml.FullLoader)

secret_request = requests.get("https://pc.bazos.cz/pridat-inzerat.php", cookies={'bid': config["bid"], 'bkod': config["bkod"]})
with open('./secret_request.html', 'w', encoding='utf-8') as f:
    f.write(secret_request.text)
query = pq(secret_request.text)
secret_name = query('#formpridani > div:nth-child(2) > input[type="hidden"]').attr("name")
secret_value = query('#formpridani > div:nth-child(2) > input[type="hidden"]').attr("value")
print(secret_name)
print(secret_value)