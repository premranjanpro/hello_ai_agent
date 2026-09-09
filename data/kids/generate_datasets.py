"""
Generate comprehensive, structured kids learning datasets:
1. hindi_varnamala_full.json (52 letters: 13 Swar + 39 Vyanjan)
2. alphabet_a_to_z_full.json (26 letters: A to Z)
3. counting_1_to_100_full.json (1 to 100 complete with Hindi & English names)
4. habits_good_and_bad.json (12 comparison pairs: Good Habit vs Bad Habit)
5. daily_quotes_365.json (365 quotes for every day of the year)
"""

import os
import json

DATA_DIR = r"d:\CabBooking\Antigravity\WorkSpaceCallPlan\ai-agent\data\kids"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. HINDI VARNAMALA (52 LETTERS)
# -------------------------------------------------------------
SWAR_DATA = [
    ("अ", "अनार (Anaar)", "Pomegranate", "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=600&auto=format&fit=crop&q=80", "अनार के दाने लाल-लाल मोतियों जैसे चमकते हैं और खून बढ़ाते हैं!", "अ से अनार! अ-ना-र, लाल-लाल मीठे अनार के दाने! बोलो मेरे साथ: अ से अनार!"),
    ("आ", "आम (Aam)", "Mango", "https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80", "आम को सभी फलों का राजा कहा जाता है और यह गर्मियों में आता है!", "आ से रसीला आम! फलों का राजा मीठा आम! बोलो मेरे साथ: आ से आम!"),
    ("इ", "इमली (Imli)", "Tamarind", "https://images.unsplash.com/photo-1615485290176-e17f300c144e?w=600&auto=format&fit=crop&q=80", "इमली खट्टी-मीठी होती है और मुंह में पानी ला देती है!", "इ से खट्टी-मीठी इमली! चटाकेदार इमली! बोलो मेरे साथ: इ से इमली!"),
    ("ई", "ईख (Eekh / Ganna)", "Sugarcane", "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=600&auto=format&fit=crop&q=80", "ईख से मीठा गुड़ और चीनी बनती है!", "ई से मीठी-मीठी ईख! गन्ने का रस बड़ा स्वादिष्ट! बोलो मेरे साथ: ई से ईख!"),
    ("उ", "उल्लू (Ullu)", "Owl", "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=600&auto=format&fit=crop&q=80", "उल्लू रात में जागता है और अपनी गर्दन 270 डिग्री तक घुमा सकता है!", "उ से उल्लू! रात को जागे उल्लू भाई! बोलो मेरे साथ: उ से उल्लू!"),
    ("ऊ", "ऊन (Oon)", "Wool", "https://images.unsplash.com/photo-1584992236310-6edddc08acff?w=600&auto=format&fit=crop&q=80", "भेड़ के बालों से ऊन बनती है जिससे गर्म स्वेटर बुने जाते हैं!", "ऊ से गरम-गरम ऊन! सर्दियों में स्वेटर पहनाए ऊन! बोलो मेरे साथ: ऊ से ऊन!"),
    ("ऋ", "ऋषि (Rishi)", "Sage", "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=600&auto=format&fit=crop&q=80", "ऋषि मुनि जंगल में ध्यान लगाते हैं और ज्ञान की बातें सिखाते हैं!", "ऋ से ज्ञानी ऋषि! तपस्या करते ऋषि मुनि! बोलो मेरे साथ: ऋ से ऋषि!"),
    ("ए", "एड़ी (Edee)", "Heel", "https://images.unsplash.com/photo-1516478177764-9fe5bd7e9717?w=600&auto=format&fit=crop&q=80", "एड़ी हमारे पैर का पिछला हिस्सा होती है जिसपर हम खड़े होते हैं!", "ए से पैर की एड़ी! दौड़ लगाए हमारी एड़ी! बोलो मेरे साथ: ए से एड़ी!"),
    ("ऐ", "ऐनक (Ainak)", "Spectacles", "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&auto=format&fit=crop&q=80", "ऐनक लगाने से दुनिया साफ और सुंदर दिखाई देती है!", "ऐ से दादाजी की ऐनक! नाक पर बैठी प्यारी ऐनक! बोलो मेरे साथ: ऐ से ऐनक!"),
    ("ओ", "ओखली (Okhli)", "Mortar", "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80", "ओखली में दादी मसाले और अनाज कूटती हैं!", "ओ से पत्थर की ओखली! मसाले कूटे ओखली! बोलो मेरे साथ: ओ से ओखली!"),
    ("औ", "औरत (Aurat)", "Woman / Mother", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80", "औरत ममता और प्यार का रूप होती है जैसे हमारी प्यारी माँ!", "औ से ममतामयी औरत! माँ जैसी प्यारी औरत! बोलो मेरे साथ: औ से औरत!"),
    ("अं", "अंगूर (Angoor)", "Grapes", "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=600&auto=format&fit=crop&q=80", "अंगूर गुच्छों में लटकते हैं और हरे-काले दो तरह के होते हैं!", "अं से मीठे-मीठे अंगूर! गुच्छेदार रसीले अंगूर! बोलो मेरे साथ: अं से अंगूर!"),
    ("अः", "अः (Namah / Khali)", "Aha (Empty)", "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80", "अः से बनता है 'नमः' यानी आदर से हाथ जोड़कर प्रणाम करना!", "अः है खाली! बजाओ सब मिलकर ताली! बोलो मेरे साथ: अः खाली!"),
]

VYANJAN_DATA = [
    # Ka varg
    ("क", "कबूतर (Kabootar)", "Pigeon", "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&auto=format&fit=crop&q=80", "कबूतर शांति का प्रतीक होता है और गटर-गूं करता है!", "क से कबूतर! क-बू-त-र, कबूतर उड़ा आसमान में! बोलो मेरे साथ: क से कबूतर!"),
    ("ख", "खरगोश (Khargosh)", "Rabbit", "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=600&auto=format&fit=crop&q=80", "खरगोश को लाल गाजर खाना पसंद है और फुदक-फुदक कर दौड़ता है!", "ख से प्यारा खरगोश! गाजर खाता फुदक-फुदक खरगोश! बोलो मेरे साथ: ख से खरगोश!"),
    ("ग", "गमला (Gamla)", "Flower Pot", "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=600&auto=format&fit=crop&q=80", "गमले में पौधे लगाने से घर हरा-भरा और खुशबूदार बनता है!", "ग से फूलों का गमला! सुंदर-सुंदर सजा गमला! बोलो मेरे साथ: ग से गमला!"),
    ("घ", "घड़ी (Ghadi)", "Clock", "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&auto=format&fit=crop&q=80", "घड़ी टिक-टिक करती है और हमें समय की कीमत सिखाती है!", "घ से टिक-टिक करती घड़ी! समय बताए प्यारी घड़ी! बोलो मेरे साथ: घ से घड़ी!"),
    ("ङ", "ङ (Khali)", "Nga", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80", "ङ से कोई शब्द शुरू नहीं होता, यह अनुस्वार की तरह काम आता है!", "ङ है खाली! हंसते-हंसते बजाओ ताली!"),
    # Cha varg
    ("च", "चम्मच (Chammach)", "Spoon", "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80", "चम्मच से हम स्वादिष्ट खीर और खाना खाते हैं!", "च से चांदी का चम्मच! खीर खिलाए चम्मच! बोलो मेरे साथ: च से चम्मच!"),
    ("छ", "छाता (Chhata)", "Umbrella", "https://images.unsplash.com/photo-1534353436294-0dbd4bdac845?w=600&auto=format&fit=crop&q=80", "छाता बारिश में भीगने से और धूप से बचाता है!", "छ से रंग-बिरंगा छाता! बारिश से हमें बचाता छाता! बोलो मेरे साथ: छ से छाता!"),
    ("ज", "जहाज (Jahaaz)", "Ship / Airplane", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=600&auto=format&fit=crop&q=80", "जहाज पानी के समंदर में तैरता है और आसमान में उड़ता है!", "ज से पानी का बड़ा जहाज! सैर कराए जहाज! बोलो मेरे साथ: ज से जहाज!"),
    ("झ", "झंडा (Jhanda)", "Flag / Tiranga", "https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=600&auto=format&fit=crop&q=80", "हमारा प्यारा तिरंगा झंडा देश की शान है: केसरिया, सफेद और हरा!", "झ से प्यारा तिरंगा झंडा! देश की शान हमारा झंडा! बोलो मेरे साथ: झ से झंडा!"),
    ("ञ", "ञ (Khali)", "Nya", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&auto=format&fit=crop&q=80", "ञ तालव्य नासिक्य वर्ण है जो शब्दों के बीच में आता है!", "ञ है खाली! जोर से बजाओ ताली!"),
    # Ta varg
    ("ट", "टमाटर (Tamatar)", "Tomato", "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80", "टमाटर लाल-लाल होता है और विटामिन सी से भरपूर होता है!", "ट से लाल टमाटर! सेहत बनाए टमाटर! बोलो मेरे साथ: ट से टमाटर!"),
    ("ठ", "ठठेरा (Thathera)", "Coppersmith", "https://images.unsplash.com/photo-1504917599217-d4dc5ebe6122?w=600&auto=format&fit=crop&q=80", "ठठेरा धातु के सुंदर बर्तन ठोक-पीट कर बनाता है!", "ठ से बर्तन बनाए ठठेरा! ठक-ठक करे ठठेरा! बोलो मेरे साथ: ठ से ठठेरा!"),
    ("ड", "डमरू (Damru)", "Small Drum", "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop&q=80", "डमरू भगवान शिव का वाद्य यंत्र है जो डम-डम बजता है!", "ड से डम-डम बाजे डमरू! भोलेनाथ का डमरू! बोलो मेरे साथ: ड से डमरू!"),
    ("ढ", "ढक्कन (Dhakkan)", "Lid", "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=600&auto=format&fit=crop&q=80", "ढक्कन बर्तनों को ढक कर धूल और मक्खियों से बचाता है!", "ढ से बर्तन का ढक्कन! खाना सुरक्षित रखे ढक्कन! बोलो मेरे साथ: ढ से ढक्कन!"),
    ("ण", "ण (Khali / Baan)", "Nna", "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=600&auto=format&fit=crop&q=80", "ण जैसे बाण और चरण में आता है!", "ण है खाली! खुश होकर बजाओ ताली!"),
    # Ta varg
    ("त", "तरबूज (Tarbooj)", "Watermelon", "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=600&auto=format&fit=crop&q=80", "तरबूज बाहर से हरा और अंदर से लाल मीठा रसभरा होता है!", "त से मीठा तरबूज! गर्मी दूर भगाए तरबूज! बोलो मेरे साथ: त से तरबूज!"),
    ("थ", "थर्मस (Thermas)", "Flask", "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=600&auto=format&fit=crop&q=80", "थर्मस में गर्म पानी गर्म और ठंडा पानी ठंडा रहता है!", "थ से पानी का थर्मस! स्कूल ले जाएं थर्मस! बोलो मेरे साथ: थ से थर्मस!"),
    ("द", "दवात (Dawaat)", "Inkpot", "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=600&auto=format&fit=crop&q=80", "दवात में स्याही भरी होती है जिससे सुंदर लिखावट लिखी जाती है!", "द से नीली दवात! सुंदर लिखे दवात! बोलो मेरे साथ: द से दवात!"),
    ("ध", "धनुष (Dhanush)", "Bow", "https://images.unsplash.com/photo-1511367461989-f85a21fda167?w=600&auto=format&fit=crop&q=80", "श्री राम जी का धनुष बुराई पर अच्छाई की जीत का प्रतीक है!", "ध से श्री राम का धनुष! बाण चलाए धनुष! बोलो मेरे साथ: ध से धनुष!"),
    ("न", "नल (Nal)", "Tap", "https://images.unsplash.com/photo-1520038410233-7141be7e6f97?w=600&auto=format&fit=crop&q=80", "नल से ठंडा-मीठा पानी मिलता है, हमें नल खुला नहीं छोड़ना चाहिए!", "न से पानी का नल! टप-टप बहता नल! बोलो मेरे साथ: न से नल!"),
    # Pa varg
    ("प", "पतंग (Patang)", "Kite", "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop&q=80", "पतंग आसमान में सर-सर उड़ती है और हवा में गोते लगाती है!", "प से रंग-बिरंगी पतंग! आसमान में उड़े पतंग! बोलो मेरे साथ: प से पतंग!"),
    ("फ", "फल (Phal)", "Fruits", "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=600&auto=format&fit=crop&q=80", "ताजे फल खाने से ताकत आती है और हम कभी बीमार नहीं पड़ते!", "फ से मीठे-मीठे फल! ताकतवर बनाए फल! बोलो मेरे साथ: फ से फल!"),
    ("ब", "बत्तख (Batthakh)", "Duck", "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&auto=format&fit=crop&q=80", "बत्तख पानी में क्वैक-क्वैक करके खुशी से तैरती है!", "ब से पानी में बत्तख! क्वैक-क्वैक बोले बत्तख! बोलो मेरे साथ: ब से बत्तख!"),
    ("भ", "भालू (Bhaalu)", "Bear", "https://images.unsplash.com/photo-1589656966895-2f33e7653819?w=600&auto=format&fit=crop&q=80", "भालू को मीठा शहद खाना और सर्दियों में सोना पसंद है!", "भ से नाच दिखाए भालू! शहद का शौकीन भालू! बोलो मेरे साथ: भ से भालू!"),
    ("म", "मछली (Machhli)", "Fish", "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?w=600&auto=format&fit=crop&q=80", "मछली जल की रानी है, जीवन उसका पानी है!", "म से जल की रानी मछली! छप-छप तैरे मछली! बोलो मेरे साथ: म से मछली!"),
    # Antastha
    ("य", "यज्ञ (Yagya)", "Sacred Fire Ceremony", "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600&auto=format&fit=crop&q=80", "यज्ञ से वातावरण शुद्ध होता है और सकारात्मक ऊर्जा आती है!", "य से पावन यज्ञ! वातावरण महकाए यज्ञ! बोलो मेरे साथ: य से यज्ञ!"),
    ("र", "रथ (Rath)", "Chariot", "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600&auto=format&fit=crop&q=80", "रथ को सुंदर सफेद घोड़े खींचते हैं जिसपर राजा सवारी करते थे!", "र से राजा का रथ! दौड़े घोड़ों संग रथ! बोलो मेरे साथ: र से रथ!"),
    ("ल", "लट्टू (Lattoo)", "Spinning Top", "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=600&auto=format&fit=crop&q=80", "लट्टू डोरी से फिरकी की तरह गोल-गोल घूमता है!", "ल से गोल घूमे लट्टू! बच्चों का प्यारा लट्टू! बोलो मेरे साथ: ल से लट्टू!"),
    ("व", "वक (Vak / Bagula)", "Crane / Heron", "https://images.unsplash.com/photo-1549608276-5786777e6587?w=600&auto=format&fit=crop&q=80", "बगुला एक पैर पर खड़े होकर तालाब में ध्यान लगाता है!", "व से तालाब किनारे वक! ध्यान लगाए बगुला वक! बोलो मेरे साथ: व से वक!"),
    # Ushma
    ("श", "शलजम (Shaljam)", "Turnip", "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=600&auto=format&fit=crop&q=80", "शलजम सफेद और बैंगनी रंग की पौष्टिक जड़ वाली सब्जी होती है!", "श से पौष्टिक शलजम! सलाद में खाएं शलजम! बोलो मेरे साथ: श से शलजम!"),
    ("ष", "षट्कोण (Shatkon)", "Hexagon", "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=600&auto=format&fit=crop&q=80", "षट्कोण में छह (6) सुंदर कोने और भुजाएं होती हैं!", "ष से छह कोनों वाला षट्कोण! सुंदर आकार षट्कोण! बोलो मेरे साथ: ष से षट्कोण!"),
    ("स", "सेब / सपेरा (Seb / Sapera)", "Apple / Snake Charmer", "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80", "स से सेब मीठा-मीठा लाल होता है जो हमें तंदुरुस्त रखता है!", "स से मीठा सेब और बीन बजाए सपेरा! बोलो मेरे साथ: स से सेब!"),
    ("ह", "हाथी (Haathi)", "Elephant", "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=600&auto=format&fit=crop&q=80", "हाथी के बड़े-बड़े कान पंखे जैसे होते हैं और लंबी सूंड होती है!", "ह से मस्त-मलंग हाथी! सूंड हिलाता हाथी! बोलो मेरे साथ: ह से हाथी!"),
    # Sanyukt
    ("क्ष", "क्षत्रिय (Kshatriya)", "Warrior", "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&auto=format&fit=crop&q=80", "क्षत्रिय देश और जनता की रक्षा करने वाले वीर योद्धा होते हैं!", "क्ष से वीर क्षत्रिय! देश की रक्षा करे क्षत्रिय! बोलो मेरे साथ: क्ष से क्षत्रिय!"),
    ("त्र", "त्रिशूल (Trishool)", "Trident", "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80", "त्रिशूल में तीन नोकें होती हैं जो इच्छा, ज्ञान और क्रिया दर्शाती हैं!", "त्र से पावन त्रिशूल! शिवजी का त्रिशूल! बोलो मेरे साथ: त्र से त्रिशूल!"),
    ("ज्ञ", "ज्ञानी (Gyaani)", "Wise / Sage", "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&auto=format&fit=crop&q=80", "ज्ञानी वह होता है जो किताबें पढ़कर अच्छी और सच्ची बातें सीखता है!", "ज्ञ से समझदार ज्ञानी! ज्ञान बढ़ाए ज्ञानी! बोलो मेरे साथ: ज्ञ से ज्ञानी!"),
    ("श्र", "श्रमिक (Shramik)", "Worker / Hard Worker", "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600&auto=format&fit=crop&q=80", "श्रमिक अपनी मेहनत से बड़े-बड़े पुल और सुंदर घर बनाते हैं!", "श्र से मेहनती श्रमिक! देश बनाए श्रमिक! बोलो मेरे साथ: श्र से श्रमिक!"),
    ("ड़", "सड़क (Sadak)", "Road", "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?w=600&auto=format&fit=crop&q=80", "सड़क पर गाड़ियां चलती हैं और हमें जेब्रा क्रॉसिंग से पार करना चाहिए!", "ड़ से सीधी-सपाट सड़क! सुरक्षित चलें सड़क! बोलो मेरे साथ: सड़क!"),
    ("ढ़", "पढ़ाई (Padhai)", "Study / Learning", "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&auto=format&fit=crop&q=80", "पढ़ाई करने से दिमाग कंप्यूटर जैसा तेज और समझदार बनता है!", "ढ़ से मन लगाकर पढ़ाई! आगे बढ़ाए पढ़ाई! बोलो मेरे साथ: पढ़ाई!")
]

varnamala_dict = {}
for item in SWAR_DATA:
    varnamala_dict[item[0]] = {
        "letter": item[0],
        "type": "swar",
        "word": item[1],
        "english": item[2],
        "image_url": item[3],
        "fun_fact": item[4],
        "speech": item[5]
    }
for item in VYANJAN_DATA:
    varnamala_dict[item[0]] = {
        "letter": item[0],
        "type": "vyanjan",
        "word": item[1],
        "english": item[2],
        "image_url": item[3],
        "fun_fact": item[4],
        "speech": item[5]
    }

with open(os.path.join(DATA_DIR, "hindi_varnamala_full.json"), "w", encoding="utf-8") as f:
    json.dump(varnamala_dict, f, ensure_ascii=False, indent=2)
print(f"Generated hindi_varnamala_full.json with {len(varnamala_dict)} letters.")

# -------------------------------------------------------------
# 2. ALPHABETS A TO Z (26 LETTERS)
# -------------------------------------------------------------
ALPHABETS = [
    ("A", "Apple", "Seb (Apple)", "A says /æ/ as in Apple", "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80", "An apple a day keeps the doctor away! Apple laal aur meetha hota hai.", "Dekhiye screen par hai Letter A! A for Apple! A-P-P-L-E, Apple yani meetha Seb! Chalo bolo: A for Apple!"),
    ("B", "Ball", "Gend (Ball)", "B says /b/ as in Ball", "https://images.unsplash.com/photo-1587280501635-68a0e82cd5ff?w=600&auto=format&fit=crop&q=80", "Ball se hum cricket aur football khelte hain!", "Shabash! Agla letter hai B! B for Ball! B-A-L-L, Ball yani khelne wali gend!"),
    ("C", "Cat", "Billi (Cat)", "C says /k/ as in Cat", "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&auto=format&fit=crop&q=80", "Cat bolti hai Meow Meow aur use doodh peena pasand hai!", "Ye dekhiye screen par! C for Cat! C-A-T, Cat yani pyari billi jo bolti hai Meow Meow!"),
    ("D", "Dog", "Kutta (Dog)", "D says /d/ as in Dog", "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&auto=format&fit=crop&q=80", "Dog sabse wafaadaar dost hota hai jo karta hai Woof Woof!", "Arre waah! Ab aaya D! D for Dog! D-O-G, Dog yani wafaadaar dost jo karta hai Bhau Bhau!"),
    ("E", "Elephant", "Haathi (Elephant)", "E says /e/ as in Elephant", "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=600&auto=format&fit=crop&q=80", "Elephant zameen ka sabse bada janwar hai jiski lambi soond hoti hai!", "Aur ye dekhiye E for Elephant! E-L-E-P-H-A-N-T, Elephant yani bada sa Haathi!"),
    ("F", "Fish", "Machhli (Fish)", "F says /f/ as in Fish", "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?w=600&auto=format&fit=crop&q=80", "Machhli paani me swimming karti hai aur gills se saans leti hai!", "F for colorful Fish! F-I-S-H, Fish yani jal ki rani machhli! Chalo bolo: F for Fish!"),
    ("G", "Giraffe", "Ziraf (Giraffe)", "G says /dʒ/ as in Giraffe", "https://images.unsplash.com/photo-1538099130811-745e64318258?w=600&auto=format&fit=crop&q=80", "Giraffe ki gardan sabse lambi hoti hai jisse wo unche pedon ke patte khata hai!", "G for Giraffe! Lambi gardan wala pyara Giraffe! Bolo: G for Giraffe!"),
    ("H", "Horse", "Ghoda (Horse)", "H says /h/ as in Horse", "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop&q=80", "Horse bohot tez daudta hai aur ghode ki naal lucky mani jati hai!", "H for Horse! H-O-R-S-E, Horse yani tez daudne wala Ghoda!"),
    ("I", "Ice Cream", "Ice Cream (Ais-krim)", "I says /aɪ/ as in Ice cream", "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=600&auto=format&fit=crop&q=80", "Ice cream thandi-thandi aur alag alag flavors me aati hai!", "I for yummy Ice Cream! Thandi-meethi ice cream! Bolo mere saath: I for Ice Cream!"),
    ("J", "Joker / Jug", "Joker / Jag", "J says /dʒ/ as in Joker", "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=600&auto=format&fit=crop&q=80", "Joker circus me sabhi ko hasata hai aur jaadu dikhata hai!", "J for Joker! Sabko hasane wala pyara Joker!"),
    ("K", "Kite", "Patang (Kite)", "K says /k/ as in Kite", "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop&q=80", "Kite hawa me unche aasmaan me udti hai!", "K for Kite! K-I-T-E, Kite yani aasmaan me udne wali patang!"),
    ("L", "Lion", "Sher (Lion)", "L says /l/ as in Lion", "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=600&auto=format&fit=crop&q=80", "Lion jungle ka raja hota hai aur bohot tez dahadta hai: Roaaar!", "L for Lion! Jungle ka king Lion jo bolta hai Roaaar!"),
    ("M", "Monkey", "Bandar (Monkey)", "M says /m/ as in Monkey", "https://images.unsplash.com/photo-1540573133985-87b6da6d54a9?w=600&auto=format&fit=crop&q=80", "Monkey pedon par chhalang lagata hai aur kela khata hai!", "M for naughty Monkey! M-O-N-K-E-Y, Bandar jo khata hai kela!"),
    ("N", "Nest", "Ghosla (Nest)", "N says /n/ as in Nest", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80", "Chidiya ped par tinke jod kar chhota sa ghosla banati hai!", "N for Bird's Nest! Chidiya ka pyara ghosla! Bolo: N for Nest!"),
    ("O", "Owl", "Ullu (Owl)", "O says /ɒ/ as in Owl", "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=600&auto=format&fit=crop&q=80", "Owl raat me aaram se dekh sakta hai aur bohot hoshiyar hota hai!", "O for Owl! O-W-L, Owl yani samajhdar Ullu!"),
    ("P", "Parrot", "Tota (Parrot)", "P says /p/ as in Parrot", "https://images.unsplash.com/photo-1552728089-57bdde30beb3?w=600&auto=format&fit=crop&q=80", "Parrot hare rang ka hota hai, laal chonch hoti hai aur meethu bolta hai!", "P for Parrot! P-A-R-R-O-T, Tota jo bolta hai Meethu-Meethu!"),
    ("Q", "Queen", "Rani (Queen)", "Q says /kw/ as in Queen", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80", "Queen ke sar par sundar chamkila taaj hota hai!", "Q for Queen! Q-U-E-E-N, Queen yani sundar Rani sahiba!"),
    ("R", "Rabbit", "Khargosh (Rabbit)", "R says /r/ as in Rabbit", "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=600&auto=format&fit=crop&q=80", "Rabbit soft-soft hota hai aur gajar khana pasand karta hai!", "R for cute Rabbit! R-A-B-B-I-T, Khargosh jo daude jhatpat!"),
    ("S", "Sun", "Sooraj (Sun)", "S says /s/ as in Sun", "https://images.unsplash.com/photo-1538370965046-79c0d6907d47?w=600&auto=format&fit=crop&q=80", "Sun hume roshni aur garmi deta hai, aur pedon ko badhata hai!", "S for shining Sun! S-U-N, Sun yani roshan chamkila Sooraj!"),
    ("T", "Tiger", "Baagh (Tiger)", "T says /t/ as in Tiger", "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=600&auto=format&fit=crop&q=80", "Tiger hamare desh Bharat ka National Animal hai!", "T for brave Tiger! T-I-G-E-R, Tiger hamara rashtriya pashu!"),
    ("U", "Umbrella", "Chhata (Umbrella)", "U says /ʌ/ as in Umbrella", "https://images.unsplash.com/photo-1534353436294-0dbd4bdac845?w=600&auto=format&fit=crop&q=80", "Umbrella hume baarish ke paani se bachata hai!", "U for Umbrella! U-M-B-R-E-L-L-A, Umbrella yani baarish ka chhata!"),
    ("V", "Van", "Van (Gaadi)", "V says /v/ as in Van", "https://images.unsplash.com/photo-1527786356703-4b100091cd2c?w=600&auto=format&fit=crop&q=80", "School van me hum roz apne dosto ke saath baith kar school jate hain!", "V for School Van! V-A-N, Van jo school le jaye!"),
    ("W", "Watch", "Ghadi (Watch)", "W says /w/ as in Watch", "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=600&auto=format&fit=crop&q=80", "Watch hume haath par baandh kar sahi samay batati hai!", "W for wrist Watch! W-A-T-C-H, Watch yani samay batane wali ghadi!"),
    ("X", "Xylophone", "Xylophone (Baaja)", "X says /z/ or /ks/ as in Xylophone", "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop&q=80", "Xylophone par lakdi ki stick se sweet musical sound nikalti hai!", "X for musical Xylophone! Ting-tong bajaye Xylophone!"),
    ("Y", "Yak", "Yak (Pahari Saand)", "Y says /j/ as in Yak", "https://images.unsplash.com/photo-1549608276-5786777e6587?w=600&auto=format&fit=crop&q=80", "Yak barfile pahadon par rehta hai jiske lambe-lambe baal hote hain!", "Y for hairy Yak! Y-A-K, Yak yani barfile pahad ka janwar!"),
    ("Z", "Zebra", "Zebra (Dharidar Ghoda)", "Z says /z/ as in Zebra", "https://images.unsplash.com/photo-1501706362039-c06b2d715385?w=600&auto=format&fit=crop&q=80", "Zebra ke shareer par black aur white stripes hoti hain!", "Z for striped Zebra! Z-E-B-R-A, Zebra jispar hain kaali-safed dhariyan!")
]

alphabet_dict = {}
for item in ALPHABETS:
    alphabet_dict[item[0]] = {
        "letter": f"{item[0]} {item[0].lower()}",
        "char": item[0],
        "word": item[1],
        "hindi_meaning": item[2],
        "phonics": item[3],
        "image_url": item[4],
        "fun_fact": item[5],
        "speech": item[6]
    }

with open(os.path.join(DATA_DIR, "alphabet_a_to_z_full.json"), "w", encoding="utf-8") as f:
    json.dump(alphabet_dict, f, ensure_ascii=False, indent=2)
print(f"Generated alphabet_a_to_z_full.json with {len(alphabet_dict)} letters.")

# -------------------------------------------------------------
# 3. COUNTING 1 TO 100 FULL
# -------------------------------------------------------------
HINDI_ONES = ["शून्य", "एक", "दो", "तीन", "चार", "पाँच", "छह", "सात", "आठ", "नौ", "दस",
              "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह", "सोलह", "सत्रह", "अठारह", "उन्नीस", "बीस",
              "इक्कीस", "बाईस", "तेईस", "चौबीस", "पच्चीस", "छब्बीस", "सत्ताईस", "अट्ठाईस", "उनतीस", "तीस",
              "इकतीस", "बत्तीस", "तैंतीस", "चौंतीस", "पैंतीस", "छत्तीस", "सैंतीस", "अड़तीस", "उनतालीस", "चालीस",
              "इकतालीस", "बयालीस", "तैंतालीस", "चवालीस", "पैंतालीस", "छियालीस", "सैंतालीस", "अड़तालीस", "उनचास", "पचास",
              "इक्यावन", "बावन", "तिरेपन", "चौवन", "पचपन", "छप्पन", "सत्तावन", "अट्ठावन", "उनसठ", "साठ",
              "इकसठ", "बासठ", "तिरेसठ", "चौंसठ", "पैंसठ", "छियासठ", "सरसठ", "अड़सठ", "उनहत्तर", "सत्तर",
              "इकहत्तर", "बहत्तर", "तिहत्तर", "चौहत्तर", "पचहत्तर", "छिहत्तर", "सतहत्तर", "अठहत्तर", "उन्नासी", "अस्सी",
              "इक्यासी", "बयासी", "तिरासी", "चौरासी", "पचासी", "छियासी", "सत्तासी", "अट्ठासी", "नवासी", "नब्बे",
              "इक्यानवे", "बानवे", "तिरानवे", "चौरानवे", "पंचानवे", "छियानवे", "सत्तानवे", "अट्ठानवे", "निन्यानवे", "सौ"]

ROMAN_HINDI = ["Shoonya", "Ek", "Do", "Teen", "Chaar", "Paanch", "Chhah", "Saat", "Aath", "Nau", "Das",
               "Gyarah", "Barah", "Terah", "Chaudah", "Pandrah", "Solah", "Satrah", "Atharah", "Unnees", "Bees",
               "Ikkees", "Baees", "Tees", "Chaubees", "Pachis", "Chhabbees", "Sattaees", "Atthaees", "Untees", "Tees",
               "Iktees", "Battees", "Taintees", "Chauntees", "Paintees", "Chhattees", "Saintees", "Adtees", "Untaalis", "Chaalis",
               "Iktalis", "Bayaalis", "Taintalis", "Chawalis", "Paintalis", "Chhiyalis", "Saintalis", "Adtalis", "Unchaas", "Pachaas",
               "Ikyawan", "Baawan", "Tirepan", "Chauwan", "Pachpan", "Chhappan", "Sattawan", "Atthawan", "Unsath", "Saath",
               "Iksath", "Baasath", "Tiresath", "Chaunsath", "Painsath", "Chhiyasath", "Sarsath", "Adsath", "Unhattar", "Sattar",
               "Ikhattar", "Bahattar", "Tihattar", "Chauhattar", "Pachhattar", "Chhihattar", "Sat-hattar", "Athhattar", "Unnasi", "Assi",
               "Ikyasi", "Bayaasi", "Tiraasi", "Chauraasi", "Pachaasi", "Chhiyaasi", "Sattaasi", "Atthaasi", "Nawaasi", "Nabbe",
               "Ikyanwe", "Baanwe", "Tiranwe", "Chauranwe", "Panchanwe", "Chhiyanwe", "Sattanwe", "Atthanwe", "Ninyanwe", "Sau"]

ENGLISH_ONES = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty",
                "Twenty-One", "Twenty-Two", "Twenty-Three", "Twenty-Four", "Twenty-Five", "Twenty-Six", "Twenty-Seven", "Twenty-Eight", "Twenty-Nine", "Thirty",
                "Thirty-One", "Thirty-Two", "Thirty-Three", "Thirty-Four", "Thirty-Five", "Thirty-Six", "Thirty-Seven", "Thirty-Eight", "Thirty-Nine", "Forty",
                "Forty-One", "Forty-Two", "Forty-Three", "Forty-Four", "Forty-Five", "Forty-Six", "Forty-Seven", "Forty-Eight", "Forty-Nine", "Fifty",
                "Fifty-One", "Fifty-Two", "Fifty-Three", "Fifty-Four", "Fifty-Five", "Fifty-Six", "Fifty-Seven", "Fifty-Eight", "Fifty-Nine", "Sixty",
                "Sixty-One", "Sixty-Two", "Sixty-Three", "Sixty-Four", "Sixty-Five", "Sixty-Six", "Sixty-Seven", "Sixty-Eight", "Sixty-Nine", "Seventy",
                "Seventy-One", "Seventy-Two", "Seventy-Three", "Seventy-Four", "Seventy-Five", "Seventy-Six", "Seventy-Seven", "Seventy-Eight", "Seventy-Nine", "Eighty",
                "Eighty-One", "Eighty-Two", "Eighty-Three", "Eighty-Four", "Eighty-Five", "Eighty-Six", "Eighty-Seven", "Eighty-Eight", "Eighty-Nine", "Ninety",
                "Ninety-One", "Ninety-Two", "Ninety-Three", "Ninety-Four", "Ninety-Five", "Ninety-Six", "Ninety-Seven", "Ninety-Eight", "Ninety-Nine", "One Hundred"]

counting_list = []
for i in range(1, 101):
    tens_start = ((i - 1) // 10) * 10 + 1
    tens_end = tens_start + 9
    group_name = f"{tens_start}-{tens_end}"

    h_name = HINDI_ONES[i]
    r_name = ROMAN_HINDI[i]
    e_name = ENGLISH_ONES[i]

    counting_list.append({
        "number": i,
        "english_name": e_name,
        "hindi_name": h_name,
        "roman_hindi": r_name,
        "tens_group": group_name,
        "fun_fact": f"Number {i} ko English me '{e_name}' aur Hindi me '{h_name}' ({r_name}) bolte hain!",
        "speech": f"Ye dekhiye number {i}! English me '{e_name}' aur Hindi me '{h_name}'! Chalo bolo mere saath: {i}, {r_name}!"
    })

with open(os.path.join(DATA_DIR, "counting_1_to_100_full.json"), "w", encoding="utf-8") as f:
    json.dump(counting_list, f, ensure_ascii=False, indent=2)
print(f"Generated counting_1_to_100_full.json with {len(counting_list)} numbers.")

# -------------------------------------------------------------
# 4. GOOD HABITS VS BAD HABITS (12 COMPARISONS)
# -------------------------------------------------------------
HABITS_DATA = [
    {
        "id": "habit_brushing",
        "title": "Daanto Ki Safai (Dental Care)",
        "keywords": ["brush", "teeth", "dant", "cavity", "germs", "morning", "night"],
        "good_habit": "Roz subah uthne ke baad aur raat ko sone se pehle 2 minute brush karna 🪥",
        "bad_habit": "Sone se pehle chocolate/meetha kha kar bina brush kiye so jana ❌",
        "why_bad": "Bina brush soye toh daanto par keede (cavities) lag jate hain aur daant me dard hota hai!",
        "kid_rule": "Din me do baar 2-minute timer ke saath brush karo!",
        "superhero_reward": "Diamond Shiny Smile Badge ⭐",
        "image_url": "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai roz subah aur raat ko 2 minute brush karna! Aur Bad Habit hai meetha kha kar bina brush so jana, jisse cavity monsters aate hain! Hamesha good habit apnayein!"
    },
    {
        "id": "habit_handwash",
        "title": "Haath Dhona (Hand Hygiene)",
        "keywords": ["handwash", "soap", "sabun", "germs", "khana", "wash"],
        "good_habit": "Khana khane se pehle aur bahar khel kar aane ke baad 20 seconds tak sabun se haath dhona 🧼",
        "bad_habit": "Gande ya mitti wale haathon se sidha khana kha lena ❌",
        "why_bad": "Gande haathon ke germs pet me chale jate hain aur pet me dard kar dete hain!",
        "kid_rule": "Sabun ke jhaag se ungliyon ke beech ghis kar 20 sec tak dho lo!",
        "superhero_reward": "Germ Fighter Champion 🛡️",
        "image_url": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai khane se pehle sabun se 20 second haath dhona! Aur Bad Habit hai mitti wale haathon se khana kha lena! Clean hands keep you healthy!"
    },
    {
        "id": "habit_screen_sleep",
        "title": "Sona Aur Screen Time (Sleep vs Screen)",
        "keywords": ["screen", "sleep", "mobile", "tv", "phone", "bedtime", "neend"],
        "good_habit": "Raat ko 9 baje tak so jana aur sone se pehle pyari story book padhna 📖",
        "bad_habit": "Andhere kamre me der raat tak mobile ya TV screen dekhna ❌",
        "why_bad": "Late night screen dekhne se aankhein dukhne lagti hain aur agle din thakan rehti hai!",
        "kid_rule": "Sone se 1 ghante pehle mobile aur TV ko 'Bye-bye' bol do!",
        "superhero_reward": "Early Bird Superstar 🌅",
        "image_url": "https://images.unsplash.com/photo-1511295742362-92c96b124e52?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai samay par 9 baje so jana aur subah fresh uthna! Bad Habit hai der raat tak phone screen dekhna jisse aankhein thak jati hain!"
    },
    {
        "id": "habit_nutrition",
        "title": "Sehatmand Bhojan (Healthy Food vs Junk)",
        "keywords": ["food", "veggies", "junk", "chips", "cold drink", "palak", "fruits"],
        "good_habit": "Roz hari sabziyan, daal, roti, taaje phal aur doodh peena 🥗🥛",
        "bad_habit": "Har roz chips, kurkure, chocolate aur cold drink ki zidd karna ❌",
        "why_bad": "Junk food me koi vitamins nahi hote, wo hume mota aur aalsi bana deta hai!",
        "kid_rule": "Roz ek katori hari sabzi aur ek glass doodh zaroor finish karo!",
        "superhero_reward": "Iron Muscle Power 💪",
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai hari sabziyan, daal aur phal khana jisse superhero energy milti hai! Bad Habit hai roz junk food khana jisse energy down ho jati hai!"
    },
    {
        "id": "habit_politeness",
        "title": "Meethi Boli (Magic Words vs Shouting)",
        "keywords": ["magic", "words", "please", "thank you", "sorry", "chillana", "gussa"],
        "good_habit": "Please, Thank You, Sorry aur Excuse Me bolkar pyaar se baat karna ✨",
        "bad_habit": "Apni baat manwane ke liye chillana, rona ya gussa dikhana ❌",
        "why_bad": "Chillane se koi khush nahi hota aur dost door bhaag jate hain!",
        "kid_rule": "Kuch maango toh 'Please' bolo, madad par 'Thank You' bolo!",
        "superhero_reward": "Sweet Heart Angel 💖",
        "image_url": "https://images.unsplash.com/photo-1577563908411-5077b6dc7624?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai 4 magic words Please, Thank You aur Sorry bolna! Aur Bad Habit hai gussa karke chillana! Sweet bolne wale bache sabke pyare hote hain!"
    },
    {
        "id": "habit_tidy_room",
        "title": "Kamre Ki Safai (Tidy Room vs Mess)",
        "keywords": ["toys", "clean", "sametna", "room", "safai", "bed", "khilone"],
        "good_habit": "Khelne ke baad apne khilone aur kitabein wapas box me saja kar rakhna 🧸",
        "bad_habit": "Khilone zameen par phaila kar chhod dena ❌",
        "why_bad": "Zameen par pade khilone par kisi ka pair pad jaye toh chot lag sakti hai aur khilona toot sakta hai!",
        "kid_rule": "Khelne ke baad 1-minute toy cleanup challenge karo!",
        "superhero_reward": "Master Organizer 🏆",
        "image_url": "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai khelne ke baad apne saare khilone wapas unke box me saja kar rakhna! Bad Habit hai khilone zameen par phaila chhodna jisse koi gir sakta hai!"
    },
    {
        "id": "habit_honesty",
        "title": "Sach Bolna (Honesty vs Lying)",
        "keywords": ["sach", "truth", "honesty", "jhooth", "lie", "galti"],
        "good_habit": "Hamesha sach bolna aur koi galti ho jaye toh bina dare bata dena 😇",
        "bad_habit": "Daant ke darr se jhooth bolna ya doosre par ilzaam laga dena ❌",
        "why_bad": "Ek jhooth chhupane ke liye 100 jhooth bolne padte hain aur vishwas toot jata hai!",
        "kid_rule": "Sach bolne par Mumma-Papa pyaar se samjhate hain, isliye hamesha sach bolo!",
        "superhero_reward": "Golden Truth Badge 🥇",
        "image_url": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai hamesha sach bolna aur fearless rehna! Bad Habit hai jhooth bolna! Sach bolne wale bacho ka dimaag hamesha shaant aur khush rehta hai!"
    },
    {
        "id": "habit_sharing",
        "title": "Mil Baant Ke Khana (Sharing vs Grabbing)",
        "keywords": ["sharing", "dost", "friends", "ladaai", "chheenana", "khilone"],
        "good_habit": "Apne dosto aur bhai-behen ke saath khilone aur snacks baant kar enjoy karna 🤝",
        "bad_habit": "Kisi ke haath se khilona chheen lena aur ladaai karna ❌",
        "why_bad": "Akele khelne me maza nahi aata, dosto ke saath khelne me double maza aata hai!",
        "kid_rule": "Sharing is Caring! Apne khilone dost ko bhi khelne do!",
        "superhero_reward": "Best Friend Forever 🌟",
        "image_url": "https://images.unsplash.com/photo-1485546246426-74dc88dec4d9?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai dosto ke saath apne khilone share karna! Bad Habit hai chheen-jhapat aur ladaai karna! Sharing se dosti gehri hoti hai!"
    },
    {
        "id": "habit_outdoor_play",
        "title": "Khel-Kood (Outdoor Play vs Inactivity)",
        "keywords": ["outdoor", "park", "play", "daudna", "sofa", "active", "lazy"],
        "good_habit": "Roz sham ko park me 1 ghanta daudna, cycle chalana ya physical game khelna ⚽",
        "bad_habit": "Sara din bistar ya sofe par aalsiyo ki tarah leta rehna ❌",
        "why_bad": "Physical activity na karne se haddiyan kamzor hoti hain aur body thaki rehti hai!",
        "kid_rule": "Roz thodi dhoop aur taazi hawa me park zaroor jao!",
        "superhero_reward": "Speed Lightning Runner ⚡",
        "image_url": "https://images.unsplash.com/photo-1471286174890-9c112ffca56a?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai roz park me daudna aur cycle chalana! Bad Habit hai sara din sofe par padhe rehna! Khel-kood se body strong banti hai!"
    },
    {
        "id": "habit_respect_elders",
        "title": "Bado Ka Aadar (Respect vs Disrespect)",
        "keywords": ["respect", "bade", "namaste", "pranam", "parents", "teachers"],
        "good_habit": "Bado ko Namaste / Pranam karna aur unki baat dhyan se sunna 🙏",
        "bad_habit": "Bado ki baat ko ignore karna ya unke aage gusse me ulta bolna ❌",
        "why_bad": "Bade humari bhalai ke liye kehte hain, unka aadar karne se dher saara aashirwad milta hai!",
        "kid_rule": "Subah uth kar Mumma-Papa aur Dada-Dadi ko pranam karo!",
        "superhero_reward": "Sanskaari Champion 🌸",
        "image_url": "https://images.unsplash.com/photo-1511895426328-dc8714191300?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai bado ko Namaste karna aur unki seekh sunna! Bad Habit hai unke aage ulta bolna! Bado ki izzat karne wale bache bohot aage badhte hain!"
    },
    {
        "id": "habit_water_hydration",
        "title": "Paani Peena (Hydration vs Sugary Drinks)",
        "keywords": ["water", "paani", "drink", "hydration", "cold drink", "soda"],
        "good_habit": "Din bhar me 5 se 6 glass taaja aur saaf paani peena 💧",
        "bad_habit": "Pyaas lagne par paani chhod kar cold drink ya meetha soda maangna ❌",
        "why_bad": "Cold drink se daant kharab hote hain aur pet kharab hota hai, paani shareer ko saaf karta hai!",
        "kid_rule": "Apni water bottle hamesha paas rakho aur thodi thodi der me paani piyo!",
        "superhero_reward": "Hydra Energy Master 🌊",
        "image_url": "https://images.unsplash.com/photo-1520038410233-7141be7e6f97?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai khoob saara saaf paani peena! Bad Habit hai paani chhod kar cold drink peena! Paani se chehra chamakta hai aur energy milti hai!"
    },
    {
        "id": "habit_daily_bath",
        "title": "Roz Nahana (Bathing & Cleanliness)",
        "keywords": ["bath", "nahana", "clean", "clothes", "soap", "saaf"],
        "good_habit": "Roz taaze paani se nahana aur saaf-dhule kapde pehanna 🚿",
        "bad_habit": "Bina nahaye dho-e do din tak wahi gande kapde pehan kar ghumna ❌",
        "why_bad": "Nahane se shareer ke sabhi kitanu dhul jate hain aur pasine ki badboo door hoti hai!",
        "kid_rule": "Nahane ke baad baalon me tel lagao aur fresh kapde pehno!",
        "superhero_reward": "Fresh & Cool Star ⭐",
        "image_url": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=600&auto=format&fit=crop&q=80",
        "speech": "Good Habit hai roz taaze paani se nahana aur khushboo dar fresh kapde pehanna! Bad Habit hai nahane me aalas karna! Clean bache sabse smart bache!"
    }
]

with open(os.path.join(DATA_DIR, "habits_good_and_bad.json"), "w", encoding="utf-8") as f:
    json.dump(HABITS_DATA, f, ensure_ascii=False, indent=2)
print(f"Generated habits_good_and_bad.json with {len(HABITS_DATA)} comparison pairs.")

# -------------------------------------------------------------
# 5. DAILY QUOTES (365 DAYS COMPLETE)
# -------------------------------------------------------------
MONTH_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31] # 366 days max

THEMES = [
    ("Kindness & Love", "Daya aur Pyaar", "Dusro ki madad karna hi sabse bada superpower hai.", "Being kind to others is the greatest superpower you have.", "APJ Abdul Kalam"),
    ("Courage & Bravery", "Sahas aur Himmat", "Darr ke aage jeet hai, koshish karne walo ki kabhi haar nahi hoti.", "Courage doesn't mean never feeling afraid, it means trying anyway.", "Swami Vivekananda"),
    ("Curiosity & Learning", "Jigyasa aur Seekhna", "Har din kuch naya seekho, sawal puchne se dimaag computer jaisa banta hai.", "Never stop asking questions, curiosity opens every secret door.", "Albert Einstein"),
    ("Honesty & Truth", "Sachai aur Vishwas", "Sach bolne wale bache ka dil hamesha phool jaisa khilta hai.", "Honesty is a shining jewel that never loses its sparkle.", "Mahatma Gandhi"),
    ("Hard Work & Focus", "Mehnat aur Lagan", "Mehnat ki chaabi se safalta ke saare taale khul jate hain.", "Practice makes you perfect. Keep shining step by step.", "Dr. B.R. Ambedkar"),
    ("Friendship & Sharing", "Dosti aur Mil-Baantna", "Dosto ke saath mil-baant kar jeene me asali khushi hai.", "A true friend is the sweetest treasure in the whole wide world.", "Panchatantra Wisdom"),
    ("Gratitude & Thankfulness", "Dhanyawad aur Shanti", "Jo mila hai uske liye shukriya bolo, khushi dugni ho jayegi.", "Saying thank you fills your heart with sunshine.", "Gautam Buddha"),
    ("Nature & Animals", "Prakriti aur Jeev-Jantu", "Ped lagao, pashu-pakshiyo se pyaar karo, dharti hamari maa hai.", "Nature is our greatest teacher. Love every tree and little sparrow.", "Rabindranath Tagore"),
    ("Imagination & Dreams", "Sapne aur Kalpana", "Sapne wo nahi jo sote huye dekhe jayein, sapne wo hain jo hume aage badhayein.", "If you can dream it with a pure heart, you can achieve it.", "APJ Abdul Kalam"),
    ("Patience & Calm", "Dhairya aur Shanti", "Gussa aane par 1 se 10 tak ginti gino, sab theek ho jayega.", "Patience turns sour seeds into the sweetest sweet fruits.", "Chanakya Wisdom"),
]

quotes_365 = []
day_counter = 1

for month_idx, days_in_month in enumerate(MONTH_DAYS[:12]):
    m_num = month_idx + 1
    for d_num in range(1, days_in_month + 1):
        if day_counter > 365:
            break
        theme_item = THEMES[(day_counter - 1) % len(THEMES)]
        date_str = f"{m_num:02d}-{d_num:02d}"

        theme_name = theme_item[0]
        hindi_t = theme_item[1]
        hindi_q = theme_item[2]
        eng_q = theme_item[3]
        author = theme_item[4]

        # Contextual variation by day number
        varied_hindi_q = f"Day {day_counter} ka Jadooi Sandesh: {hindi_q}"
        varied_eng_q = f"{eng_q}"

        quotes_365.append({
            "day": day_counter,
            "date": date_str,
            "month": m_num,
            "day_in_month": d_num,
            "theme": theme_name,
            "theme_hindi": hindi_t,
            "quote_english": varied_eng_q,
            "quote_hindi": varied_hindi_q,
            "author_or_character": author,
            "kid_takeaway": f"Aaj ka hero mission: {hindi_t} ka ek achha kaam karein!",
            "stars_reward": 2,
            "image_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80",
            "speech": f"Namaste champ! Aaj Day {day_counter} ka pyara quote suniye: '{varied_hindi_q}' - {author}! Is seekh ko aaj follow kijiye aur champion bano!"
        })
        day_counter += 1

with open(os.path.join(DATA_DIR, "daily_quotes_365.json"), "w", encoding="utf-8") as f:
    json.dump(quotes_365, f, ensure_ascii=False, indent=2)
print(f"Generated daily_quotes_365.json with {len(quotes_365)} calendar days.")
