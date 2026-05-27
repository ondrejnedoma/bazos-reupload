import os
import re
import yaml
import requests
from pyquery import PyQuery as pq
from colorama import init, Fore
init()

def sanitize_path_component(value):
  sanitized = re.sub(r'[<>:\"/\\|?*]+', '_', value)
  sanitized = sanitized.strip().rstrip('. ')
  return sanitized

def get_image_dir(title):
  return os.path.join('./img', sanitize_path_component(title))

def setup():
  print(Fore.CYAN + "No config found, launching initial setup\nAvoid inputting special characters (ˇ,´,ů...)")
  email = input(Fore.YELLOW + "E-mail: " + Fore.WHITE)
  if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
    print(Fore.RED + f'Email "{email}" is invalid')
    exit()
  phone = input(Fore.YELLOW + "Phone number (example: 792123456): " + Fore.WHITE)
  if not re.match(r'^\d{9}$', phone):
    print(Fore.RED + f'Phone number "{phone}" is invalid')
    exit()
  password = input(Fore.YELLOW + "Password (has to be the same for all of your ads): " + Fore.WHITE)
  phone_number_request = requests.post("https://ostatni.bazos.cz/pridat-inzerat.php", data={
    "podminky": "1",
    "teloverit": phone,
    "Submit": "Odeslat",
  }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
  query = pq(phone_number_request.text)
  error_message = query("body > div.sirka > div.flexmain > div.maincontent > div > span.ztop").text()
  if error_message:
    print(Fore.RED + error_message)
    exit()
  else:
    print(Fore.BLUE + "Sent verification SMS to " + phone)
  verification_code = input(Fore.YELLOW + "Enter verification code from SMS: " + Fore.WHITE)
  verification_code_request = requests.post("https://ostatni.bazos.cz/pridat-inzerat.php", data={
    "klic": verification_code,
    "klictelefon": "+420" + phone,
    "Submit": "Odeslat",
  }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, cookies={'testcookie': 'ano', 'testcookieaaa': 'ano'})
  query = pq(verification_code_request.text)
  error_message = query("body > div.sirka > div.flexmain > div.maincontent > div > span.ztop").text()
  if error_message:
    print(Fore.RED + error_message)
    exit()
  else:
    bid = verification_code_request.cookies.get("bid")
    bkod = verification_code_request.cookies.get("bkod")
    print(Fore.BLUE + "bid: " + bid + Fore.WHITE)
    print(Fore.BLUE + "bkod: " + bkod + Fore.WHITE)
    with open('./config.yaml', 'w+') as config_file:
      yaml.dump({"email": email, "password": password, "phone": phone, "bid": bid, "bkod": bkod}, config_file)

def get_all_ads():
  all_ads_request = requests.post("https://www.bazos.cz/moje-inzeraty.php", data={
    "mail": config["email"],
    "telefon": config["phone"],
    "Submit": "Vypsat inzeráty",
  }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
  query = pq(all_ads_request.text)
  return query('div.inzeraty > div.inzeratynadpis > a').map(lambda i, e: query(e).attr("href"))


def get_ad_data(link):
  ad_info = {}
  ad_request = requests.get(link)
  query = pq(ad_request.text)
  ad_info["title"] = query("h1.nadpisdetail").text()
  print(Fore.BLUE + ad_info["title"] + Fore.WHITE, end="\r")
  ad_info["description"] = query("div.popisdetail").text()
  ad_info["domain"] = link.split("/")[2]
  ad_info["id"] = link.split("/")[4]
  ad_info["category"] = query("body > div > a:nth-child(16)").attr("href").split("&cat=")[1]
  ad_info["author"] = query("td.listadvlevo > table > tr:nth-child(1) > td:nth-child(2)").text()
  ad_info["price"] = re.sub(r'\D', '', query("td.listadvlevo > table > tr:nth-child(5) > td:nth-child(2)").text())
  ad_info["zip"] = re.sub(r'\D', '', query("td.listadvlevo > table > tr:nth-child(3) > td:nth-child(3) > a:nth-child(1)").text())
  images = []
  images.append(query("img.carousel-cell-image").attr("src"))
  filtered_thumbnails = query('img.obrazekflithumb')
  if filtered_thumbnails:
    filtered_thumbnails.pop(0)
    filtered_thumbnails.map(lambda i, e: images.append(query(e).attr("src").replace("t/", "/")))
  ad_info["images"] = images
  ad_info["image_dir"] = get_image_dir(ad_info["title"])
  return ad_info

def download_images(images, image_dir):
  os.makedirs(image_dir, exist_ok=True)
  for i, image in enumerate(images, start=1):
    image_path = os.path.join(image_dir, f"{i}.jpg")
    if os.path.exists(image_path):
      continue
    image_request = requests.get(image, stream=True)
    with open(image_path, "wb") as image_file:
      for chunk in image_request.iter_content(chunk_size=8192):
        if chunk:
          image_file.write(chunk)


def delete_ad(id, domain):
  requests.post("https://" + domain + "/deletei2.php", data={
    "heslobazar": config["password"],
    "idad": id,
    "administrace": "Vymazat",
  }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, cookies={'bid': config["bid"], 'bkod': config["bkod"]})

def upload_images(images, domain, image_dir):
  image_links = []
  for i, _image in enumerate(images, start=1):
    image_path = os.path.join(image_dir, f"{i}.jpg")
    with open(image_path, "rb") as image_file:
      image_request = requests.post("https://" + domain + "/upload.php", files={"file[0]": image_file})
    image_links.append(image_request.json()[0])
  return image_links

def create_ad(info, image_links):
  secret_request = requests.get("https://pc.bazos.cz/pridat-inzerat.php", cookies={'bid': config["bid"], 'bkod': config["bkod"]})
  query = pq(secret_request.text)
  secret_name = query('#formpridani > div:nth-child(2) > input[type="hidden"]').attr("name")
  secret_value = query('#formpridani > div:nth-child(2) > input[type="hidden"]').attr("value")
  files = []
  for image_link in image_links:
    files.append(("files[]", (None, image_link)))
  formdata = (
      ("category", (None, info["category"])),
      ("nadpis", (None, info["title"])),
      ("popis", (None, info["description"])),
      ("cena", (None, info["price"])),
      ("cenavyber", (None, "1")),
      ("lokalita", (None, info["zip"])),
      *files,
      ("jmeno", (None, info["author"])),
      ("telefoni", (None, config["phone"])),
      ("maili", (None, config["email"])),
      ("heslobazar", (None, config["password"])),
      (secret_name, (None, secret_value)),
      ("Submit", (None, "Odeslat"))
    )
  requests.post("https://" + info["domain"] + "/insert.php", files=formdata, cookies={'bid': config["bid"], 'bkod': config["bkod"]})
  print(Fore.GREEN + info["title"] + Fore.WHITE)

try:
  with open('./config.yaml', 'r') as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)
except:
  setup()
  with open('./config.yaml', 'r') as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)

os.makedirs('./img', exist_ok=True)
all_ads = get_all_ads()
print(Fore.BLUE + "Found " + str(len(all_ads)) + " ads" + Fore.WHITE)
for one_ad in all_ads:
  info = get_ad_data(one_ad)
  download_images(info["images"], info["image_dir"])
  delete_ad(info["id"], info["domain"])
  image_links = upload_images(info["images"], info["domain"], info["image_dir"])
  create_ad(info, image_links)