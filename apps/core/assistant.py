"""Bounded customer help backed by the catalogue, without a cloud AI service."""

import re
import unicodedata

from django.db.models import Q
from django.urls import reverse

from apps.medicines.models import Medicine


def normalize(text):
    return unicodedata.normalize("NFKC", text).casefold().strip()


ALIASES = {
    "पैरासिटामोल": "paracetamol", "पेरासिटामोल": "paracetamol",
    "क्रोसिन": "crocin", "डोलो": "dolo", "सेटिरिजिन": "cetirizine",
    "सिट्रीज़िन": "cetirizine", "अमोक्सिसिलिन": "amoxicillin",
    "इंसुलिन": "insulin", "ओआरएस": "ors", "बेनाड्रिल": "benadryl",
}

STOP_WORDS = set("do you have is are a an the in of for me my please find search show medicine medicines tablet tablets capsule syrup available availability stock price cost how much tell about details prescription required need buy can i get check generic brand hai hain kya ka ki ke mein mujhe chahiye dawa dawai batao दवा दवाई क्या है हैं की का के में मुझे चाहिए दिखाओ जानकारी कीमत उपलब्ध स्टॉक प्रिस्क्रिप्शन पर्ची पर्चा".split())


def customer_reply(message, language="en-IN"):
    hindi = language == "hi-IN"

    def choose(en, hi):
        return hi if hindi else en

    text = normalize(message)
    # Handle medical questions before catalogue matching. A medicine match must
    # never turn a symptom/dose question into a product recommendation.
    medical = r"\b(dose|dosage|take|taking|recommend|treat|treatment|symptom|pain|fever|pregnant|pregnancy|child|baby|allerg\w*|side.effect\w*|interaction\w*|overdose|safe|substitute|alternative|bukhar|dard|khansi|kitni|kitna|leni|lena)\b|खुराक|बुखार|दर्द|गर्भ|बच्च|एलर्जी|इलाज|खांसी|खाँसी|लेना|लेनी|दुष्प्रभाव|कितनी|कितना"
    if re.search(medical, text):
        return {"reply": choose(
            "Please ask the pharmacist about symptoms, doses, side effects or which medicine to take. I can look up catalogue details, but cannot choose a treatment or confirm whether a medicine is safe for you.",
            "लक्षण, खुराक, दुष्प्रभाव या कौन सी दवा लेनी है, इसके लिए फार्मासिस्ट से बात करें। मैं दवा की सूची में जानकारी खोज सकता हूँ, लेकिन इलाज या आपके लिए दवा की सुरक्षा तय नहीं कर सकता।",
        ), "medicines": []}

    if re.search(r"\b(sales|revenue|profit|customers|password|supplier|bills)\b|बिक्री|मुनाफा|पासवर्ड", text):
        return {"reply": choose(
            "This customer assistant only helps with medicine catalogue questions. Please ask pharmacy staff about accounts or other store information.",
            "यह ग्राहक सहायक केवल दवाओं की सूची से जुड़े सवालों में मदद करता है। खाते या दुकान की अन्य जानकारी के लिए स्टाफ से बात करें।",
        ), "medicines": []}

    report_intent = (
        re.search(r"\b(catalogue|catalog|report)\b|कैटलॉग|कैटलाग|सूची|रिपोर्ट", text)
        or re.search(r"\b(list|show|all)\b.*\b(medicines|medicine|drugs)\b", text)
        or re.search(r"\b(medicines|medicine)\b.*\b(list|summary)\b", text)
    )
    if report_intent:
        from .catalogue_report import catalogue_snapshot

        snapshot = catalogue_snapshot()
        total, active, inactive = snapshot["total"], snapshot["active"], snapshot["inactive"]
        required, categories = snapshot["prescription_required"], snapshot["category_count"]
        reply = choose(
            f"Medicine catalogue report\n• Total records: {total}\n• Active: {active}\n• Inactive: {inactive}\n• Categories: {categories}\n• Prescription marked as required: {required}\n\nOpen the full report below for every medicine, composition, strength, category, manufacturer, unit, prescription flag and status. You can print it or download a CSV. Stock quantities and prices are not recorded in this catalogue.",
            f"दवाओं की सूची की रिपोर्ट\n• कुल रिकॉर्ड: {total}\n• सक्रिय: {active}\n• निष्क्रिय: {inactive}\n• श्रेणियाँ: {categories}\n• प्रिस्क्रिप्शन आवश्यक के रूप में दर्ज: {required}\n\nपूरी सूची, जेनेरिक नाम, स्ट्रेंथ, श्रेणी, निर्माता, यूनिट, प्रिस्क्रिप्शन और स्थिति देखने के लिए नीचे रिपोर्ट खोलें। इसे प्रिंट या CSV में डाउनलोड कर सकते हैं। स्टॉक की मात्रा और कीमतें इस सूची में दर्ज नहीं हैं।",
        )
        return {"reply": reply, "medicines": [], "report_url": reverse("core:catalogue_report")}

    for original, replacement in ALIASES.items():
        text = text.replace(original, replacement)
    tokens = [word for word in re.findall(r"[^\W_]+", text, re.UNICODE)
              if word not in STOP_WORDS and len(word) > 1]
    # Search name/composition only: do not suggest drugs by symptom/category.
    query = Q()
    for token in tokens[:20]:
        query |= Q(name__icontains=token) | Q(generic_name__icontains=token)
    candidates = list(Medicine.objects.active().filter(query).order_by("name", "strength")[:40]) if tokens else []
    # Prefer the name with the most matched query words (e.g. 'Dolo 650').
    candidates.sort(key=lambda item: -sum(token in normalize(f"{item.name} {item.generic_name} {item.strength}") for token in tokens))
    medicines = [{"name": item.label, "generic_name": item.generic_name,
                  "prescription_required": item.prescription_required}
                 for item in candidates[:5]]
    if medicines:
        lines = [choose("I found these catalogue entries:", "दवाओं की सूची में ये नाम मिले:")]
        for item in medicines:
            flag = choose("Prescription marked as required", "सूची में प्रिस्क्रिप्शन आवश्यक है") if item["prescription_required"] else choose("Ask the pharmacist to confirm prescription requirements", "प्रिस्क्रिप्शन की जरूरत फार्मासिस्ट से पूछें")
            lines.append(f"• {item['name']} — {flag}.")
        lines.append(choose(
            "A catalogue entry does not confirm stock or price. Please check availability and the current price at the counter.",
            "सूची में नाम होने से स्टॉक या कीमत की पुष्टि नहीं होती। उपलब्धता और वर्तमान कीमत काउंटर पर पूछें।",
        ))
        return {"reply": "\n".join(lines), "medicines": medicines}

    if re.search(r"prescription|प्रिस्क्रिप्शन|पर्ची|पर्चा", text):
        reply = choose("Tell me the medicine name to check its prescription flag in our catalogue. The pharmacist can confirm what you need to bring.", "दवा का नाम बताएं ताकि मैं सूची में प्रिस्क्रिप्शन की जानकारी देख सकूँ। क्या लाना है, इसकी पुष्टि फार्मासिस्ट करेंगे।")
    elif re.search(r"\b(price|cost|stock|available|availability)\b|कीमत|स्टॉक|उपलब्ध", text) and not tokens:
        reply = choose("Tell me a medicine name to search the catalogue. Live stock and prices are not connected yet; the counter staff can confirm them.", "सूची में खोजने के लिए दवा का नाम बताएं। लाइव स्टॉक और कीमतें अभी जुड़ी नहीं हैं; काउंटर स्टाफ से पुष्टि करें।")
    elif re.search(r"^(hi|hello|hey|help|नमस्ते|नमस्कार|मदद)[!?.\s]*$", text):
        reply = choose("Hello! Type or say a medicine name, such as Crocin or Paracetamol. I can find catalogue entries and prescription flags. For advice about taking medicine, please speak with the pharmacist.", "नमस्ते! क्रोसिन या पैरासिटामोल जैसी दवा का नाम बोलें या लिखें। मैं सूची और प्रिस्क्रिप्शन की जानकारी खोज सकता हूँ। दवा लेने की सलाह के लिए फार्मासिस्ट से बात करें।")
    else:
        reply = choose("I couldn't match that to an active medicine in our catalogue. Try the brand or generic name printed on the pack, preferably in English, or ask the pharmacist. I can only answer catalogue and prescription-flag questions.", "मुझे सूची में इससे मेल खाती सक्रिय दवा नहीं मिली। पैक पर लिखा ब्रांड या जेनेरिक नाम लिखें, संभव हो तो अंग्रेज़ी में, या फार्मासिस्ट से पूछें। मैं केवल सूची और प्रिस्क्रिप्शन की जानकारी दे सकता हूँ।")
    return {"reply": reply, "medicines": []}
