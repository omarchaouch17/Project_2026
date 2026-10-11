"""faq.py - free, rule-based help assistant (no AI, no API, no cost).

The question is matched to a topic by keywords; the answers are written in advance
(DE/EN/FR/AR). No data leaves the server. If ANTHROPIC_API_KEY is set, the app uses
the AI instead (assistant.py).
"""
from translations import texts

TOPICS = [
    {"id": "cholesterol",
     "label": {"de": "Was ist Gesamtcholesterin?", "en": "What is total cholesterol?",
               "fr": "Qu'est-ce que le cholestérol total ?", "ar": "ما هو الكوليسترول الكلي؟"},
     "keys": ("cholesterin", "cholesterol", "cholestérol", "كوليسترول", "blutfett"),
     "answer": {
         "de": "Das Gesamtcholesterin umfasst alle Blutfette zusammen. Unter 200 mg/dL gilt es als wünschenswert, 200–239 als grenzwertig, ab 240 als hoch. Es ist nur ein Teil des Gesamtbildes – HDL und Blutdruck zählen ebenfalls.",
         "en": "Total cholesterol covers all blood fats together. Below 200 mg/dL is desirable, 200–239 borderline, from 240 high. It is only part of the picture – HDL and blood pressure matter too.",
         "fr": "Le cholestérol total regroupe toutes les graisses du sang. Moins de 200 mg/dL est souhaitable, 200–239 limite, à partir de 240 élevé. Ce n'est qu'une partie du tableau : le HDL et la tension comptent aussi.",
         "ar": "الكوليسترول الكلي هو مجموع دهون الدم. أقل من 200 mg/dL مرغوب، و200–239 حدّي، ومن 240 فما فوق مرتفع. وهو جزء فقط من الصورة؛ فالـ HDL وضغط الدم مهمان أيضًا."}},
    {"id": "hdl",
     "label": {"de": "Was bedeutet HDL?", "en": "What does HDL mean?",
               "fr": "Que signifie HDL ?", "ar": "ماذا يعني HDL؟"},
     "keys": ("hdl", "gutes cholesterin", "good cholesterol", "bon cholestérol", "الجيد"),
     "answer": {
         "de": "HDL ist das „gute“ Cholesterin: Es transportiert Cholesterin aus den Gefäßen ab. Hier ist ein höherer Wert besser. Unter 40 mg/dL (Männer) bzw. 50 mg/dL (Frauen) gilt er als eher niedrig, ab 60 als günstig.",
         "en": "HDL is the “good” cholesterol: it carries cholesterol away from the vessels. Here a higher value is better. Below 40 mg/dL (men) or 50 mg/dL (women) it is rather low, from 60 it is favourable.",
         "fr": "Le HDL est le « bon » cholestérol : il évacue le cholestérol des vaisseaux. Ici, plus c'est haut, mieux c'est. En dessous de 40 mg/dL (hommes) ou 50 mg/dL (femmes), il est plutôt bas ; à partir de 60, il est favorable.",
         "ar": "HDL هو الكوليسترول «الجيد»: يحمل الكوليسترول بعيدًا عن الأوعية. هنا كلما ارتفع كان أفضل. تحت 40 mg/dL (الرجال) أو 50 (النساء) يُعدّ منخفضًا، ومن 60 فما فوق مناسب."}},
    {"id": "ldl",
     "label": {"de": "Was ist LDL?", "en": "What is LDL?", "fr": "Qu'est-ce que le LDL ?", "ar": "ما هو LDL؟"},
     "keys": ("ldl", "schlechtes cholesterin", "bad cholesterol", "mauvais cholestérol"),
     "answer": {
         "de": "LDL ist das „schlechte“ Cholesterin: Es kann sich in den Gefäßwänden ablagern. Der Framingham-Score in dieser App verwendet LDL nicht, sondern Gesamtcholesterin und HDL.",
         "en": "LDL is the “bad” cholesterol: it can build up in vessel walls. The Framingham score in this app does not use LDL, but total cholesterol and HDL.",
         "fr": "Le LDL est le « mauvais » cholestérol : il peut se déposer dans la paroi des vaisseaux. Le score de Framingham de cette application n'utilise pas le LDL, mais le cholestérol total et le HDL.",
         "ar": "LDL هو الكوليسترول «السيئ»: قد يترسب في جدران الأوعية. لا تستخدم درجة فرامنغهام في هذا التطبيق LDL، بل الكوليسترول الكلي وHDL."}},
    {"id": "blood_pressure",
     "label": {"de": "Was ist der systolische Blutdruck?", "en": "What is systolic blood pressure?",
               "fr": "Qu'est-ce que la tension systolique ?", "ar": "ما هو ضغط الدم الانقباضي؟"},
     "keys": ("blutdruck", "systol", "blood pressure", "tension", "pression", "ضغط"),
     "answer": {
         "de": "Der systolische Blutdruck ist der obere Wert beim Messen – der Druck, wenn das Herz pumpt. Um 120 mmHg gilt als optimal, 120–139 als grenzwertig, ab 140 als erhöht. Eine einzelne Messung sagt wenig; regelmäßiges Messen ist aussagekräftiger.",
         "en": "Systolic blood pressure is the upper number when measuring – the pressure while the heart pumps. Around 120 mmHg is optimal, 120–139 borderline, from 140 elevated. One reading says little; regular measuring is more meaningful.",
         "fr": "La tension systolique est le chiffre du haut – la pression quand le cœur se contracte. Autour de 120 mmHg est optimal, 120–139 limite, à partir de 140 élevée. Une seule mesure en dit peu ; des mesures régulières sont plus parlantes.",
         "ar": "ضغط الدم الانقباضي هو الرقم العلوي عند القياس، أي الضغط أثناء انقباض القلب. حوالي 120 mmHg مثالي، و120–139 حدّي، ومن 140 فما فوق مرتفع. قياس واحد لا يكفي؛ القياس المنتظم أدق."}},
    {"id": "units",
     "label": {"de": "Was bedeuten mg/dL und mmHg?", "en": "What do mg/dL and mmHg mean?",
               "fr": "Que signifient mg/dL et mmHg ?", "ar": "ماذا تعني mg/dL وmmHg؟"},
     "keys": ("mg/dl", "mmhg", "einheit", "unit", "unité", "وحدة"),
     "answer": {
         "de": "mg/dL heißt Milligramm pro Deziliter Blut (Einheit für Cholesterin). mmHg heißt Millimeter Quecksilbersäule (Einheit für den Blutdruck).",
         "en": "mg/dL means milligrams per deciliter of blood (unit for cholesterol). mmHg means millimetres of mercury (unit for blood pressure).",
         "fr": "mg/dL signifie milligrammes par décilitre de sang (unité du cholestérol). mmHg signifie millimètres de mercure (unité de la tension artérielle).",
         "ar": "mg/dL تعني ملّيغرام لكل ديسيلتر من الدم (وحدة الكوليسترول). mmHg تعني ملّيمتر زئبق (وحدة ضغط الدم)."}},
    {"id": "framingham",
     "label": {"de": "Wie funktioniert der Framingham-Score?", "en": "How does the Framingham score work?",
               "fr": "Comment fonctionne le score de Framingham ?", "ar": "كيف تعمل درجة فرامنغهام؟"},
     "keys": ("framingham", "score", "berechn", "calculat", "calcul", "فرامنغهام", "درجة", "حساب"),
     "answer": {
         "de": "Der Framingham-Score schätzt aus Alter, Geschlecht, Gesamtcholesterin, HDL, Blutdruck (mit/ohne Behandlung) und Rauchen das Risiko für eine Herzerkrankung in den nächsten 10 Jahren. Er stammt aus einer großen US-Langzeitstudie. Es ist eine grobe Schätzung, kein Diagnoseinstrument.",
         "en": "The Framingham score estimates the risk of heart disease over the next 10 years from age, sex, total cholesterol, HDL, blood pressure (treated or not) and smoking. It comes from a large US long-term study. It is a rough estimate, not a diagnostic tool.",
         "fr": "Le score de Framingham estime le risque de maladie cardiaque sur 10 ans à partir de l'âge, du sexe, du cholestérol total, du HDL, de la tension (traitée ou non) et du tabagisme. Il provient d'une grande étude américaine de long terme. C'est une estimation approximative, pas un outil de diagnostic.",
         "ar": "تقدّر درجة فرامنغهام خطر أمراض القلب خلال 10 سنوات انطلاقًا من العمر والجنس والكوليسترول الكلي وHDL وضغط الدم (مع علاج أو بدونه) والتدخين. وهي مستمدة من دراسة أمريكية طويلة الأمد. إنها تقدير تقريبي وليست أداة تشخيص."}},
    {"id": "categories",
     "label": {"de": "Was bedeuten niedrig, mittel, hoch?", "en": "What do low, medium, high mean?",
               "fr": "Que signifient faible, moyen, élevé ?", "ar": "ماذا تعني منخفض ومتوسط ومرتفع؟"},
     "keys": ("kategorie", "category", "catégorie", "niedrig", "mittel", "hoch", "low", "medium", "high", "faible", "moyen", "élevé", "منخفض", "متوسط", "مرتفع", "فئة"),
     "answer": {
         "de": "Die Einteilung folgt den ATP-III-Grenzen für das 10-Jahres-Risiko: unter 10 % niedrig, 10–20 % mittel, über 20 % hoch. Sie hilft bei der Einordnung, ersetzt aber keine ärztliche Beurteilung.",
         "en": "The grouping follows ATP III limits for the 10-year risk: under 10% low, 10–20% medium, over 20% high. It helps with orientation but does not replace a medical assessment.",
         "fr": "Le classement suit les seuils ATP III pour le risque à 10 ans : moins de 10 % faible, 10–20 % moyen, plus de 20 % élevé. Il aide à s'orienter mais ne remplace pas une évaluation médicale.",
         "ar": "يتبع التصنيف حدود ATP III للخطر خلال 10 سنوات: أقل من 10% منخفض، 10–20% متوسط، أكثر من 20% مرتفع. يساعد على التوجيه لكنه لا يغني عن التقييم الطبي."}},
    {"id": "smoking",
     "label": {"de": "Warum zählt Rauchen?", "en": "Why does smoking count?",
               "fr": "Pourquoi le tabagisme compte-t-il ?", "ar": "لماذا يُحتسب التدخين؟"},
     "keys": ("rauch", "zigarette", "smok", "cigarette", "fum", "tabac", "تدخين", "سيجار"),
     "answer": {
         "de": "Rauchen schädigt die Gefäße und erhöht das Herz-Kreislauf-Risiko deutlich. Der Framingham-Score unterscheidet nur „aktuell Raucher: ja/nein“; die Zigarettenanzahl wird hier zur Dokumentation gespeichert, ändert den Prozentwert aber nicht. Ein Rauchstopp senkt das Risiko.",
         "en": "Smoking damages the vessels and clearly raises cardiovascular risk. The Framingham score only distinguishes “current smoker: yes/no”; the number of cigarettes is stored here for documentation but does not change the percentage. Quitting lowers the risk.",
         "fr": "Fumer abîme les vaisseaux et augmente nettement le risque cardiovasculaire. Le score de Framingham ne distingue que « fumeur actuel : oui/non » ; le nombre de cigarettes est enregistré ici pour la documentation mais ne change pas le pourcentage. Arrêter réduit le risque.",
         "ar": "يضرّ التدخين الأوعية ويرفع خطر أمراض القلب والأوعية بوضوح. تميّز درجة فرامنغهام فقط بين «مدخّن حاليًا: نعم/لا»؛ ويُخزَّن عدد السجائر هنا للتوثيق ولا يغيّر النسبة. الإقلاع يخفّض الخطر."}},
    {"id": "exercise",
     "label": {"de": "Was kann ich im Alltag tun?", "en": "What can I do in everyday life?",
               "fr": "Que puis-je faire au quotidien ?", "ar": "ماذا يمكنني أن أفعل يوميًا؟"},
     "keys": ("bewegung", "sport", "ernähr", "essen", "lebensstil", "exercise", "diet", "lifestyle", "alimentation", "mode de vie", "رياضة", "غذاء", "نمط", "alltag", "everyday", "quotidien", "يومي"),
     "answer": {
         "de": "Allgemein empfiehlt die WHO mindestens 150 Minuten moderate Bewegung pro Woche. Dazu helfen viel Gemüse, Obst und Vollkorn sowie wenig Salz und gesättigte Fette. Das ist eine allgemeine Information – bei konkreten Fragen bitte Ärztin oder Arzt fragen.",
         "en": "In general, the WHO recommends at least 150 minutes of moderate activity per week. Plenty of vegetables, fruit and whole grains and little salt and saturated fat also help. This is general information – for specific questions please ask a doctor.",
         "fr": "En général, l'OMS recommande au moins 150 minutes d'activité modérée par semaine. Beaucoup de légumes, de fruits et de céréales complètes, peu de sel et de graisses saturées aident aussi. Information générale : pour une question précise, demandez à un médecin.",
         "ar": "بشكل عام توصي منظمة الصحة العالمية بما لا يقل عن 150 دقيقة من النشاط المعتدل أسبوعيًا. كما يفيد الإكثار من الخضار والفاكهة والحبوب الكاملة وتقليل الملح والدهون المشبعة. هذه معلومات عامة؛ للأسئلة المحددة اسأل الطبيب."}},
    {"id": "data",
     "label": {"de": "Was passiert mit meinen Daten?", "en": "What happens to my data?",
               "fr": "Que deviennent mes données ?", "ar": "ماذا يحدث لبياناتي؟"},
     "keys": ("daten", "datenschutz", "anonym", "data", "privacy", "données", "confidential", "بيانات", "خصوصية"),
     "answer": {
         "de": "Die Werte werden in der Datenbank dieser Demo gespeichert. Andere Besucher sehen nur anonyme Einträge ohne Namen; es werden keine IP-Adressen gespeichert. Bitte nur erfundene Daten eingeben. Dieser Assistent arbeitet regelbasiert – es werden keine Daten an eine KI gesendet.",
         "en": "The values are stored in this demo's database. Other visitors only see anonymous entries without names; no IP addresses are stored. Please enter made-up data only. This assistant is rule-based – no data is sent to an AI.",
         "fr": "Les valeurs sont enregistrées dans la base de cette démo. Les autres visiteurs ne voient que des entrées anonymes sans noms ; aucune adresse IP n'est enregistrée. Saisissez uniquement des données fictives. Cet assistant fonctionne par règles : aucune donnée n'est envoyée à une IA.",
         "ar": "تُخزَّن القيم في قاعدة بيانات هذا العرض. يرى الزوار الآخرون إدخالات مجهولة بلا أسماء، ولا تُخزَّن عناوين IP. أدخل بيانات وهمية فقط. يعمل هذا المساعد بقواعد ثابتة، ولا تُرسل أي بيانات إلى ذكاء اصطناعي."}},
]

RESULT = {
    "id": "result",
    "label": {"de": "Was bedeutet mein Ergebnis?", "en": "What does my result mean?",
              "fr": "Que signifie mon résultat ?", "ar": "ماذا تعني نتيجتي؟"},
    "keys": ("mein ergebnis", "my result", "mon résultat", "résultat", "ergebnis", "result", "نتيجتي", "نتيجة"),
    "answer": {
        "de": "Ihr berechnetes 10-Jahres-Risiko beträgt {p} % ({cat}). Das ist eine grobe Schätzung aus den eingegebenen Werten, keine Diagnose. Besprechen Sie das Ergebnis bei Fragen mit einer Ärztin oder einem Arzt.",
        "en": "Your calculated 10-year risk is {p}% ({cat}). This is a rough estimate from the entered values, not a diagnosis. If you have questions, discuss the result with a doctor.",
        "fr": "Votre risque à 10 ans calculé est de {p} % ({cat}). C'est une estimation approximative à partir des valeurs saisies, pas un diagnostic. En cas de question, parlez du résultat à un médecin.",
        "ar": "خطرك المحسوب خلال 10 سنوات هو {p}% ({cat}). هذا تقدير تقريبي من القيم المُدخلة وليس تشخيصًا. عند وجود أسئلة ناقش النتيجة مع طبيب."},
    "without": {
        "de": "Zuerst ein Ergebnis berechnen – dann kann ich es erklären.",
        "en": "Calculate a result first – then I can explain it.",
        "fr": "Calculez d'abord un résultat – je pourrai ensuite l'expliquer.",
        "ar": "احسب نتيجة أولًا، وبعدها أستطيع شرحها."},
}

ALL_TOPICS = TOPICS + [RESULT]

NOT_FOUND = {
    "de": "Dazu habe ich keine Antwort. Ich kann zum Beispiel erklären: {topics}.",
    "en": "I don't have an answer to that. I can explain, for example: {topics}.",
    "fr": "Je n'ai pas de réponse à cela. Je peux par exemple expliquer : {topics}.",
    "ar": "ليس لدي إجابة عن ذلك. يمكنني مثلًا شرح: {topics}.",
}


def suggestions(language):
    """Example questions as buttons (all topics, result first)."""
    return [RESULT["label"][language]] + [t["label"][language] for t in TOPICS[:6]]


def answer(message, language, result=None):
    """Best topic by keyword hits; without a hit, a list of possible topics."""
    lowered = message.lower()
    best, best_hits = None, 0
    for topic in ALL_TOPICS:
        hits = sum(1 for k in topic["keys"] if k in lowered)
        if hits > best_hits:
            best, best_hits = topic, hits
    if best is None:
        topics = ", ".join(t["label"][language].rstrip("?").rstrip(" ?") for t in TOPICS[:5])
        return NOT_FOUND[language].format(topics=topics)
    if best["id"] == "result":
        if not result:
            return RESULT["without"][language]
        category = texts[language]["cat_" + result["category"]]
        return RESULT["answer"][language].format(p=result["risk_percent"], cat=category)
    return best["answer"][language]
