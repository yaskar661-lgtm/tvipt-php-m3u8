import time
import requests
from flask import Flask, redirect

app = Flask(__name__)

# Kanal listesi
kanallar = {
    tvi: {"dosya": "tvi.m3u8", "slug": "tvi"},
    tvi_internacional: {"dosya": "tvi_internacional.m3u8", "slug": "tvi_internacional"},
    cnnpt: {"dosya": "cnnpt.m3u8", "slug": "cnn"},
    tvific: {"dosya": "tvific.m3u8", "slug": "tvi_ficcao"},
    tvireality: {"dosya": "tvireality.m3u8", "slug": "tvi_reality"},
    vmais: {"dosya": "vmais.m3u8", "slug": "vmais"},
}

# Token ve zaman takibi için global bir önbellek yapısı
token_cache = {"contents": None, "last_updated": 0}

# 4 saat = 4 * 60 * 60 = 14400 saniye
CACHE_DURATION = 4 * 60 * 60


def get_wms_auth_sign():
  """Token'ı çeker.

  Eğer son güncellemenin üzerinden 4 saat geçdiyse yeniler, geçmediyse
  önbellekteki geçerli token'ı döndürür.
  """
  global token_cache
  current_time = time.time()

  # Eğer token hiç alınmadıysa veya üzerinden 4 saatten fazla geçtiyse yeniden çek
  if (
      token_cache["contents"] is None
      or (current_time - token_cache["last_updated"]) > CACHE_DURATION
  ):
    url = "https://services.iol.pt/matrix?userId="
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101"
            " Firefox/74.0"
        )
    }

    try:
      response = requests.get(url, headers=headers, timeout=10)
      if response.status_code == 200:
        token_cache["contents"] = response.text.strip()
        token_cache["last_updated"] = current_time  # Zamanı güncelle
        print("[BILGI] Yeni wmsAuthSign başarıyla alındı ve önbelleklendi.")
    except Exception as e:
      print(f"[HATA] Token alınamadı: {e}")

  return token_cache["contents"]


@app.route("/kanal/<int:kanal_id>")
def kanal_yonlendir(kanal_id):
  if kanal_id not in kanallar:
    return "Kanal bulunamadı", 404

  # İlgili kanalın slug bilgisini alıyoruz
  slug = kanallar[kanal_id]["slug"]

  # Önbellekteki veya güncellenmiş token'ı al
  contents = get_wms_auth_sign()

  if not contents:
    return "Yayın anahtarı alınamadı", 500

  # m3u8 linkini oluşturma
  stream_link = f"https://video-auth6.iol.pt/live_{slug}/live_{slug}/playlist.m3u8?wmsAuthSign={contents}"

  return redirect(stream_link, code=302)

@app.route("/restart")
def restart_cache():
  """Önbelleği sıfırlar ve anında yeni bir token çeker."""
  global token_cache
  # Önbelleği sıfırla
  token_cache = {"contents": None, "last_updated": 0}

  # Yeni token'ı hemen tetikle
  new_token = get_wms_auth_sign(force_refresh=True)

  if new_token:
    return (
        "Önbellek başarıyla sıfırlandı ve yeni token"
        " oluşturuldu! ✅<br><a href='/kanal/1'>Kanallara dönmek için tıkla</a>",
        200,
    )
  else:
    return "Önbellek sıfırlandı ancak yeni token alınamadı! ❌", 500

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(debug=True, port=port)
