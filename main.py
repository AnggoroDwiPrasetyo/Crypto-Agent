import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import datetime
import os
import sys
import time

# ==========================================
# KONFIGURASI 
# ==========================================
TOKEN_TELEGRAM = "GANTI_DENGAN_TOKEN_BOTFATHER_DISINI"
CHAT_ID = "GANTI_DENGAN_ID_ANGKA_KAMU_DISINI"

# Ambil dari Environment Variable (GitHub Secrets)
TOKEN = os.environ.get("TOKEN_TELEGRAM") or TOKEN_TELEGRAM
ID_TUJUAN = os.environ.get("CHAT_ID") or CHAT_ID

# DAFTAR KOIN (Sesuai Tag Cointelegraph)
# Catatan: Nama harus sesuai juga dengan ID di CoinGecko agar harganya muncul
COINS = [
    "bitcoin", "ethereum", "binancecoin", "solana", "ripple", 
    "dogecoin", "shiba-inu", "pepe", "floki", 
    "fetch-ai", "render-token", "near", 
    "sui", "sei", "aptos", "avalanche-2", "cardano", 
    "polkadot", "tron", "the-open-network", "chainlink",
    "uniswap", "matic-network", "arbitrum", "optimism", "litecoin"
]

# Mapping manual jika nama di Berita beda dengan nama di CoinGecko
# Format: "tag_berita": "id_coingecko"
MAPPING_ID = {
    "binance-coin": "binancecoin",
    "xrp": "ripple",
    "pepecoin": "pepe",
    "near-protocol": "near",
    "toncoin": "the-open-network",
    "polygon": "matic-network",
    "avalanche": "avalanche-2"
}

class CryptoSuperAgent:
    def __init__(self):
        print("🤖 Menginisialisasi Otak AI (FinBERT)...")
        try:
            self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception as e:
            print(f"❌ Gagal load model: {e}")
            sys.exit()

    def kirim_telegram(self, pesan):
        if "GANTI" in TOKEN or "GANTI" in ID_TUJUAN:
            print("❌ Token/ID belum diisi.")
            return

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": ID_TUJUAN, "text": pesan, "parse_mode": "Markdown"}
        requests.post(url, data=data)

    def ambil_harga_global(self):
        """Mengambil harga semua koin sekaligus dari CoinGecko"""
        print("💰 Mengambil data harga terbaru...")
        
        # Gabungkan semua koin jadi satu string untuk request API
        # Kita perlu memastikan ID-nya benar (pakai mapping jika ada)
        list_id = []
        for c in COINS:
            real_id = MAPPING_ID.get(c, c) # Cek mapping, kalau gak ada pake nama asli
            list_id.append(real_id)
            
        ids_string = ",".join(list_id)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd&include_24hr_change=true"
        
        try:
            response = requests.get(url, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ Gagal ambil harga: {e}")
            return {}

    def baca_berita(self, coin):
        # Kalau ada mapping, kembalikan ke tag berita aslinya
        # Contoh: CoinGecko butuh 'ripple', tapi Cointelegraph butuh 'xrp'
        tag_berita = coin
        for k, v in MAPPING_ID.items():
            if v == coin: tag_berita = k

        url = f"https://cointelegraph.com/tags/{tag_berita}"
        headers = {"User-Agent": "Mozilla/5.0"}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            headlines = []
            items = soup.find_all("span", class_="post-card-inline__title")
            for item in items[:2]:
                headlines.append(item.get_text().strip())
            return headlines
        except:
            return []

    def jalankan_misi(self):
        # 1. Atur Waktu (UTC+8 Untuk WITA / UTC+7 Untuk WIB)
        # Ganti hours=8 jika kamu di Bali/Kalsel/Sulawesi
        # Ganti hours=7 jika kamu di Jawa/Sumatera/Kalbar
        jam_sekarang = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%H:%M')
        tanggal = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%d-%m-%Y')
        
        print(f"\n🔍 MEMULAI PATROLI ({jam_sekarang})")
        
        # 2. Ambil Harga Dulu (Sekali request buat semua)
        data_harga = self.ambil_harga_global()
        
        laporan_final = f"🤖 *UPDATE PASAR & HARGA*\n📅 {tanggal} | ⏰ {jam_sekarang} WITA\n"
        laporan_final += "----------------------------------\n"
        
        jumlah_sinyal = 0
        koin_diproses = 0

        # Loop setiap koin
        for raw_coin in COINS:
            koin_diproses += 1
            
            # Cek ID CoinGecko yang benar
            coin_id = MAPPING_ID.get(raw_coin, raw_coin)
            
            # Ambil data harga
            info_harga = data_harga.get(coin_id, {})
            harga_usd = info_harga.get('usd', 0)
            perubahan_24h = info_harga.get('usd_24h_change', 0)
            
            # Format Harga: $10,000 (+5.2%)
            icon_harga = "🟢" if perubahan_24h >= 0 else "🔴"
            str_harga = f"${harga_usd:,.2f} ({icon_harga}{perubahan_24h:.2f}%)"

            # Baca Berita
            print(f"[{koin_diproses}/{len(COINS)}] Cek: {raw_coin.upper()}...", end="\r")
            berita_list = self.baca_berita(raw_coin)
            
            score = 0
            detail_berita = ""
            
            # Analisa Sentimen
            if berita_list:
                for judul in berita_list:
                    hasil = self.analyzer(judul)[0]
                    label = hasil['label']
                    
                    if label == 'positive': score += 1
                    elif label == 'negative': score -= 1
                    
                    if label != 'neutral':
                        icon = "📈" if label == 'positive' else "📉"
                        detail_berita += f"{icon} {judul[:30]}..\n"

            # --- LOGIKA LAPORAN ---
            # Tampilkan jika: 
            # 1. Ada Sinyal Kuat (Bullish/Bearish)
            # 2. ATAU Perubahan harga drastis (> 5% atau < -5%) meskipun berita netral
            
            if score != 0 or abs(perubahan_24h) > 5:
                status = "NETRAL 💤"
                if score > 0: status = "BULLISH 🔥"
                elif score < 0: status = "BEARISH 🩸"
                
                # Header per Koin
                laporan_final += f"\n🪙 *{raw_coin.upper()}*\n💵 {str_harga}\nSinyal: {status}\n{detail_berita}"
                jumlah_sinyal += 1
        
        print("\n✅ Selesai.")

        if jumlah_sinyal > 0:
            laporan_final += "\n----------------------------------"
            laporan_final += "\n_Filter: Hanya menampilkan koin dengan sinyal kuat atau volatilitas tinggi._"
            self.kirim_telegram(laporan_final)
        else:
            print("Pasar tenang. Tidak kirim laporan.")

if __name__ == "__main__":
    agent = CryptoSuperAgent()
    agent.jalankan_misi()
