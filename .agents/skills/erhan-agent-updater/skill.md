# Yetenek: Erhan Ajanı Otomatik Güncelleyici

## Açıklama
Bu yetenek, kullanıcı 'erhanAgent'ı güncellemek istediğinde veya "erhanAgent'ı güncelle" gibi komutlar verdiğinde tetiklenir. Güncelleme metin dosyasını okur ve değişiklikleri ana ajan dosyasına otomatik olarak uygular.

## Tetikleyici Kalıplar
- "erhanAgent'ı güncelle"
- "erhanAgent güncelleme dökümanını uygula"

## Talimatlar
1. Projenin kök dizininde (root) bulunan `erhanAgent_güncellemedokümanı.txt` isimli dosyanın içeriğini oku.
2. Bu metin dosyasındaki güncelleme isteklerini (tarz değişikliği, emoji ekleme veya yeni eğitim programları gibi) analiz et.
3. `agents/ErhanYilmazAsistani_agent.py` dosyasını aç.
4. Bu dosyanın içindeki `erhan_yilmaz_instructions` değişkenini veya ilgili prompt alanını bul.
5. Metin dosyasında bulduğun değişiklikleri, Python kod yapısını ve tırnak işaretlerini bozmadan temiz bir şekilde değişkenin içine uygula.
6. Dosya güncellendikten sonra, terminale hangi spesifik güncellemelerin başarıyla uygulandığını gösteren net bir özet yazdır.