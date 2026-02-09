import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import datetime
import os
import sys

# ==========================================
# KONFIGURASI SUPER AGENT (LINK UPDATE)
# ==========================================

TOKEN = os.environ.get("TOKEN_TELEGRAM")
ID_TUJUAN = os.environ.get("CHAT_ID")

if not TOKEN: TOKEN = "ISI_TOKEN_DISINI_JIKA_TES_LOKAL"
if not ID_TUJUAN: ID_TUJUAN = "ISI_ID_DISINI_JIKA_TES_LOKAL"

COINS = [
    "bitcoin", "ethereum", "solana", "binancecoin", "ripple", 
    "dogecoin", "shiba-inu", "pepe", "floki", "bonk",
    "sui", "sei", "aptos", "render-token", "fetch-ai",
    "avalanche-2", "fantom", "optimism", "arbitrum"
]

MAPPING_ID = {
    "binance-coin": "binancecoin",
    "xrp": "ripple",
    "pepecoin": "pepe",
    "toncoin": "the-open-network",
    "avalanche": "avalanche-2",
    "matic": "matic-network",
    "render": "render-token"
}

TAGS_AIRDROP = ["airdrop", "altcoin", "defi", "gamefi"]
KEYWORDS_CUAN = ["airdrop", "snapshot", "claim", "listing", "binance", "launchpad", "reward"]

class CryptoUltimateBot:
    def __init__(self):
        print("🤖 Menyalakan Mesin AI (FinBERT)...")
        try:
            self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception as e:
            print(f"❌ Gagal load model AI: {e}")
            sys.exit()

    def kirim_telegram(self, pesan):
        if "ISI_TOKEN" in TOKEN:
            print("⚠️ Token belum diisi! Skip kirim Telegram.")
            return
        
        # PENTING: disable_web_page_preview=True agar chat tidak penuh gambar thumbnail
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": ID_TUJUAN, 
            "text": pesan, 
            "parse_mode": "Markdown", 
            "disable_web_page_preview": "true"
        }
        try:
            requests.post(url, data=data)
            print("📨 Pesan terkirim!")
        except Exception as e:
            print(f"❌ Gagal kirim: {e}")

    def ambil_harga_semua(self):
        print("💰 Mengambil data harga pasar...")
        list_id_gecko = [MAPPING_ID.get(c, c) for c in COINS]
        ids_string = ",".join(list_id_gecko)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd&include_24hr_change=true"
        try:
            return requests.get(url, timeout=10).json()
        except:
            return {}

    def scraping_berita(self, tag):
        """Ambil Judul DAN Link Berita"""
        tag_url = tag
        for k, v in MAPPING_ID.items():
            if v == tag: tag_url = k
            
        url = f"https://cointelegraph.com/tags/{tag_url}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        hasil_scraping = []
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Cari elemen judul (biasanya span di dalam link)
            items = soup.find_all("span", class_="post-card-inline__title")
            
            for item in items[:2]: # Ambil 2 berita saja
                judul = item.get_text().strip()
                
                # Cari link parent (karena span ada di dalam tag <a>)
                parent_link = item.find_parent('a')
                if parent_link:
                    link_lengkap = "https://cointelegraph.com" + parent_link['href']
                else:
                    link_lengkap = "https://cointelegraph.com"

                # Simpan judul dan link dalam dictionary
                hasil_scraping.append({'judul': judul, 'link': link_lengkap})
                
            return hasil_scraping
        except:
            return []

    def jalankan_radar_airdrop(self):
        print("📡 Scanning peluang Airdrop...")
        laporan_airdrop = ""
        ada_temuan = False
        
        for tag in TAGS_AIRDROP:
            berita_list = self.scraping_berita(tag) # Sekarang return list of dict
            for item in berita_list:
                judul = item['judul']
                link = item['link']
                
                if any(k in judul.lower() for k in KEYWORDS_CUAN):
                    # Format Link: [Judul](URL)
                    laporan_airdrop += f"🎁 [{judul}]({link})\n"
                    ada_temuan = True
        
        if ada_temuan:
            return "\n----------------------------------\n🔥 *RADAR AIRDROP & LISTING*\n" + laporan_airdrop
        return ""

    def mulai_patroli(self):
        waktu = datetime.datetime.now() + datetime.timedelta(hours=7) # WIB
        jam_str = waktu.strftime('%H:%M')
        tgl_str = waktu.strftime('%d-%m-%Y')
        
        print(f"\n🚀 START PATROLI: {tgl_str} {jam_str}")
        data_harga = self.ambil_harga_semua()
        
        laporan_final = f"🤖 *UPDATE PASAR CRYPTO*\n📅 {tgl_str} | ⏰ {jam_str} WIB\n"
        laporan_final += "----------------------------------\n"
        
        jumlah_sinyal = 0
        
        for raw_coin in COINS:
            coin_id = MAPPING_ID.get(raw_coin, raw_coin)
            info = data_harga.get(coin_id, {})
            harga = info.get('usd', 0)
            change = info.get('usd_24h_change', 0)
            
            icon_hrg = "🟢" if change >= 0 else "🔴"
            str_harga = f"${harga:,.2f} ({icon_hrg}{change:.2f}%)"
            
            print(f"🔍 Cek Sentimen: {raw_coin.upper()}...", end="\r")
            
            # Panggil fungsi scraping baru (return dict)
            berita_data = self.scraping_berita(raw_coin)
            
            sentiment_score = 0
            detail_berita = ""
            
            for item in berita_data:
                judul = item['judul']
                link = item['link']
                
                hasil = self.analyzer(judul)[0]
                label = hasil['label']
                
                if label == 'positive': sentiment_score += 1
                elif label == 'negative': sentiment_score -= 1
                
                if label != 'neutral':
                    icon_news = "📈" if label == 'positive' else "📉"
                    # --- FITUR BARU: LINK SEE MORE ---
                    # Format: 📈 Judul Berita.. [See more](link)
                    detail_berita += f"{icon_news} {judul[:30]}.. [See more]({link})\n"

            # Filter Laporan
            is_volatile = abs(change) > 3.0
            is_significant = sentiment_score != 0
            
            if is_significant or is_volatile:
                status = "NETRAL 💤"
                if sentiment_score > 0: status = "BULLISH 🔥"
                elif sentiment_score < 0: status = "BEARISH 🩸"
                
                laporan_final += f"\n🪙 *{raw_coin.upper()}*\n💵 {str_harga}\nSinyal: {status}\n{detail_berita}"
                jumlah_sinyal += 1

        info_airdrop = self.jalankan_radar_airdrop()
        if info_airdrop:
            laporan_final += info_airdrop
            jumlah_sinyal += 1

        print("\n✅ Analisis Selesai.")
        
        if jumlah_sinyal > 0:
            self.kirim_telegram(laporan_final)
        else:
            print("💤 Pasar sepi, tidak ada laporan.")

if __name__ == "__main__":
    bot = CryptoUltimateBot()
    bot.mulai_patroli()

