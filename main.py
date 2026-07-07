import asyncio
import logging
import uuid
from typing import Optional

from asgiref.sync import sync_to_async
from pydantic import BaseModel

from agents import (
    Agent,
    ModelSettings,
    TResponseInputItem,
    MessageOutputItem,
    ItemHelpers,
    HandoffOutputItem,
    Runner,
    trace,
    ToolCallItem,
    ToolCallOutputItem,
    function_tool
)
from openai.types import Reasoning

# ==========================================
# 1. BAĞLAM (CONTEXT)
# ==========================================
class SophySalesContext(BaseModel):
    conversation_id: Optional[str] = None
    platform_user_id: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    current_agent_name: Optional[str] = None


# ==========================================
# 2. ARAÇLAR (TOOLS)
# ==========================================
@function_tool(
    name_override="hesapla_kacan_ciro",
    description_override="Müşterinin aylık randevu hacmi, geç dönüş oranı ve ortalama işlem ücretine göre kaybettiği ciroyu hesaplar."
)
def hesapla_kacan_ciro(aylik_mesaj: int, gec_donus_yuzdesi: float, islem_ucreti: int) -> str:
    """Saha satış el kitabındaki formüle göre kaçan ciroyu hesaplar."""
    kacan_randevu_sayisi = aylik_mesaj * (gec_donus_yuzdesi / 100) * 0.40
    aylik_kayip = kacan_randevu_sayisi * islem_ucreti
    
    log_message = f"[TOOL LOG] Ciro Hesaplandı: Aylık Kayıp {aylik_kayip} TL"
    print(log_message)
    
    return f"Sistem Hesaplaması: Aylık ortalama {int(kacan_randevu_sayisi)} randevu kaçırılıyor. Tahmini aylık ciro kaybı: {int(aylik_kayip)} TL. Bu bilgiyi müşteriye satış stratejisine uygun, vurucu bir dille ilet."

@function_tool(
    name_override="demo_randevusu_olustur",
    description_override="Müşteri 20 dakikalık demo için gün ve saat onayladığında çalıştırılır. Randevuyu takvime kaydeder."
)
def demo_randevusu_olustur(tarih_saat: str, firma_adi: str, yetkili_kisi: str) -> str:
    """İkili takvim kapanışı başarılı olduğunda randevuyu sisteme işler."""
    log_message = f"[CRM LOG] Yeni Demo Randevusu Kapatıldı: {firma_adi} - {yetkili_kisi} - {tarih_saat}"
    print(log_message)
    
    return "Demo randevusu başarıyla oluşturuldu. Müşteriye teşekkür et ve toplantı linkinin iletileceğini söyleyerek konuşmayı profesyonelce sonlandır."


# ==========================================
# 3. KİMLİK VE KURALLAR (PROMPT)
# ==========================================
def get_instructions(context: SophySalesContext) -> str:
    return f"""
<KİMLİK>
Sen Sophy'nin uzman yapay zekâ satış temsilcisisin.
Görevin, güzellik merkezleri, medikal estetik klinikleri ve benzeri işletmelere ulaşarak onların randevu/müşteri iletişim süreçlerindeki acı noktalarını bulmak ve onları 20 dakikalık bir online demoya ikna etmektir.
Asla ürün satmaya veya fiyat konuşmaya çalışma; senin tek hedefin takvime yazılmış bir demo randevusu almaktır.

Sophy'yi kesinlikle "randevu yazılımı", "mesaj otomasyonu" veya "chatbot" olarak tanımlama. Bu kelimeler yasaktır.
Sophy'nin tek cümlelik tanımı şudur: "Sophy, işletmenize özel eğitilen, sizin adınıza konuşan ve aksiyon alan bir yapay zekâ çalışanı platformudur."
</KİMLİK>

<KURALLAR>
- SIFIR MÜSAİTLİK SORUSU: Konuşmaya asla "Nasılsınız?" veya "Müsait misiniz?" diye başlama. İzni her zaman doğrudan bir içgörü sunarak kazan.
- %30 KURALI: Konuşma oranın yüzde otuzu geçmemelidir. Sorunu sor, sus ve müşteriyi dinle. Destan yazma, kısa ve vurucu mesajlar at.
- FARKIMIZ: Sophy sadece cevap vermez, iş bitirir. Randevuyu kendi başına sisteme işler ve onay gönderir.
- İTİRAZ YÖNETİMİ: Müşteri "Pahalı" derse, bunun bir gider kalemi değil "kaçan cironun geri toplanması" olduğunu söyle. Müşteri "KVKK" derse, verilerin model eğitiminde kullanılmadığını ve şifrelendiğini belirt.
- SÜRECİ YÖNET: Müşterinin konuyu dağıtmasına izin verme. Görüşmeyi daima sen yönlendir ve her zaman bir sonraki adımı (demo) teklif ederek konuşmayı sonlandır.
</KURALLAR>

<SATIŞ AKIŞI VE CHALLENGER STRATEJİSİ>
1. ÖĞRET (İçgörü ile Başla): 
Müşteriye bilmediği bir gerçeği söyleyerek dikkatini çek. 
Örnek Açılış: "Instagram ve telefondan gelen randevu taleplerinin geç cevaplanması yüzünden kaçan müşteriler üzerine güzellik ve estetik merkezleriyle çalışıyoruz. Kaçan randevuların çoğu fiyattan değil, geç dönüşten kaçıyor."

2. KEŞFET (Acıyı Bul):
Kullanıcı cevap verdiğinde ona mevcut durumunu sorgulat. "Mesajlara şu an kim dönüyor?" veya "Geç dönülen mesajların ne kadarı sizce başka merkeze gidiyor?" gibi.

3. KAPANIŞ (Demo İste):
Müşterinin acısını anladıktan sonra düşük eşikli kapanış taktiğini uygula.
Örnek Kapanış: "Sizden bugün bir karar istemiyorum. 20 dakikalık bir demoda, sizin hizmet listenizle kurulmuş bir yapay zekâ çalışanının mesajlara nasıl döndüğünü gösterelim. Salı mı çarşamba mı uyar?"
</SATIŞ AKIŞI VE CHALLENGER STRATEJİSİ>

<İLETİŞİM ÜSLUBU>
- Kısa, net, özgüvenli ve profesyonel ol.
- WhatsApp/mesajlaşma diline uygun, rahat okunabilir uzunlukta yanıtlar ver.
</İLETİŞİM ÜSLUBU>
"""

# ==========================================
# 4. AJANIN OLUŞTURULMASI
# ==========================================
def sophy_satis_agent(context: SophySalesContext):
    return Agent[SophySalesContext](
        name="sophy_satis_agent",
        instructions=get_instructions(context),
        tools=[
            hesapla_kacan_ciro,
            demo_randevusu_olustur
        ],
        model="gpt-5.4-mini",
        model_settings=ModelSettings(
            verbosity="medium"
        )
    )

_AGENT_REGISTRY = {
    "sophy_satis_agent": sophy_satis_agent,
}

# ==========================================
# 5. CLI (TERMİNAL) ÇALIŞTIRICI MOTOR
# ==========================================
async def main():
    input_items: list[TResponseInputItem] = []
    context = SophySalesContext(
        conversation_id=uuid.uuid4().hex[:16],
        firstname="Potansiyel Müşteri",
        lastname="",
        current_agent_name="sophy_satis_agent",
    )
    current_agent: Agent[SophySalesContext] = sophy_satis_agent(context)

    print("Sophy Satış Agent'ı başlatıldı. Çıkmak için 'exit' veya 'quit' yazın.")
    
    while True:
        try:
            user_input = input("Müşteri: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            user_input = user_input.encode('utf-8', 'ignore').decode('utf-8')
            workflow_name = "[S] sophy_satis_agent - CLI"
            
            with trace(workflow_name, group_id=context.conversation_id):
                input_items.append({"content": user_input, "role": "user"})
                result = await Runner.run(current_agent, input_items, context=context)

                for new_item in result.new_items:
                    agent_name = new_item.agent.name
                    if isinstance(new_item, MessageOutputItem):
                        print(f"Sophy Agent: {ItemHelpers.text_message_output(new_item)}")
                    elif isinstance(new_item, HandoffOutputItem):
                        print(f"Handed off from {new_item.source_agent.name} to {new_item.target_agent.name}")
                    elif isinstance(new_item, ToolCallItem):
                        print(f"[{agent_name}] Araç (Tool) çalıştırılıyor...")
                    elif isinstance(new_item, ToolCallOutputItem):
                        print(f"[{agent_name}] Araç Çıktısı -> {new_item.output}")

                input_items = result.to_input_list()
                current_agent = result.last_agent

        except KeyboardInterrupt:
            print("\nÇıkış yapılıyor...")
            break
        except Exception as e:
            print(f"Hata oluştu: {e}")
            break

# ==========================================
# 6. ENTEGRASYON YARDIMCILARI (İleride WhatsApp/Backend için)
# ==========================================
try:
    from communications.models import Conversation
    from my_agents.utils import AuthContext
except ImportError:
    class Conversation:
        context: dict = {}
    class AuthContext:
        user: str = "test_auth_user"
        token: str = "test_auth_token"

async def handle_message(
    conversation: Conversation,
    input_text: str,
    message_id: str,
    auth: AuthContext | None = None,
    metadata: dict | None = None,
) -> list[str]:
    from config.settings import ENVIRONMENT
    from my_agents.runtime.trace_manager import TraceManager
    from my_agents.utils import agent_context_to_conversation_context
    from transcripts.views import get_conversation_message_history

    input_items = get_conversation_message_history(conversation)

    if not conversation.context:
        context = SophySalesContext(
            conversation_id=str(conversation.id),
            current_agent_name="sophy_satis_agent"
        )
    else:
        context = SophySalesContext.model_validate(conversation.context)

    current_agent = _AGENT_REGISTRY.get(
        context.current_agent_name,
        sophy_satis_agent,
    )(context)

    trace_manager = TraceManager(conversation)
    workflow_name = "[S] Sophy Agent - " + ENVIRONMENT
    chat_id = str(conversation.chat_id) if hasattr(conversation, 'chat_id') else "unknown_chat"
    session_id = str(conversation.session_id) if hasattr(conversation, 'session_id') else "unknown_session"

    with trace(workflow_name, group_id=(chat_id + " | " + session_id)):
        result = await Runner.run(current_agent, input_items, context=context)
        trace_manager.add_msg_id(message_id)
        trace_manager.save_and_print(result.new_items)

    context.current_agent_name = result.last_agent.name
    next_state = agent_context_to_conversation_context(context)

    logging.info("conversationId: %s stored %s items", str(conversation.id), len(result.to_input_list()))

    def _save_conversation():
        conversation.context = next_state
        conversation.save(update_fields=["context"])

    await sync_to_async(_save_conversation, thread_sensitive=True)()
    return trace_manager.outputs

if __name__ == "__main__":
    asyncio.run(main())